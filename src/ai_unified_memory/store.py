"""File system storage backend for AI Unified Memory."""

from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import DailyNote, MemoryEntry, ProjectMemory, SearchResult

DEFAULT_MEMORY_PATH = Path.home() / ".agent-memory"


class MemoryStore:
    """Manages the file-based memory store."""

    def __init__(self, base_path: Path | str | None = None) -> None:
        self.base_path = Path(base_path) if base_path else DEFAULT_MEMORY_PATH
        self._ensure_structure()
        self._init_search_db()

    def _ensure_structure(self) -> None:
        """Create directory structure if it doesn't exist."""
        directories = [
            self.base_path,
            self.base_path / "core",
            self.base_path / "daily",
            self.base_path / "projects",
            self.base_path / "skills",
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        # Create default core files if they don't exist
        default_files = {
            "core/user.md": "# User Profile\n\n_Learn about the person you're helping..._\n",
            "core/agents.md": "# Agent Guidelines\n\n_Shared behavior rules for all agents..._\n",
            "core/soul.md": "# Agent Identity\n\n_Who we are..._\n",
            "core/memory.md": "# Long-term Memory\n\n_Important learnings and decisions..._\n",
        }
        for filepath, content in default_files.items():
            full_path = self.base_path / filepath
            if not full_path.exists():
                full_path.write_text(content)

    def _init_search_db(self) -> None:
        """Initialize SQLite FTS database for search."""
        db_path = self.base_path / ".search.db"
        self.search_db = sqlite3.connect(str(db_path), check_same_thread=False)
        self.search_db.row_factory = sqlite3.Row

        cursor = self.search_db.cursor()

        # Main documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY,
                key TEXT UNIQUE,
                section TEXT,
                content TEXT,
                updated_at TIMESTAMP
            )
        """)

        # FTS virtual table
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                key,
                content,
                content_rowid=id
            )
        """)

        self.search_db.commit()

    def _index_document(self, key: str, section: str, content: str) -> None:
        """Index a document for search."""
        cursor = self.search_db.cursor()

        # Remove old entry if exists
        cursor.execute("DELETE FROM documents WHERE key = ?", (key,))

        # Insert new entry
        cursor.execute(
            "INSERT INTO documents (key, section, content, updated_at) VALUES (?, ?, ?, ?)",
            (key, section, content, datetime.utcnow()),
        )

        self.search_db.commit()

    def read_core(self, key: str) -> MemoryEntry | None:
        """Read a core memory file."""
        path = self.base_path / "core" / f"{key}.md"
        if not path.exists():
            return None

        content = path.read_text()
        return MemoryEntry.from_markdown(content, key=key)

    def write_core(self, entry: MemoryEntry) -> bool:
        """Write a core memory file."""
        path = self.base_path / "core" / f"{entry.key}.md"
        path.write_text(entry.to_markdown())
        self._index_document(f"core/{entry.key}", "core", entry.content)
        return True

    def read_project(self, project_name: str) -> ProjectMemory | None:
        """Read project memory."""
        path = self.base_path / "projects" / project_name / "memory.md"
        if not path.exists():
            return None

        content = path.read_text()
        return ProjectMemory(
            name=project_name,
            content=content,
            updated_at=datetime.fromtimestamp(path.stat().st_mtime),
        )

    def write_project(self, project: ProjectMemory) -> bool:
        """Write project memory."""
        project_dir = self.base_path / "projects" / project.name
        project_dir.mkdir(parents=True, exist_ok=True)

        path = project_dir / "memory.md"
        path.write_text(project.content)
        self._index_document(f"projects/{project.name}", "projects", project.content)
        return True

    def read_daily(self, date: str | None = None) -> DailyNote:
        """Read daily notes for a specific date."""
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        path = self.base_path / "daily" / f"{date}.md"
        if not path.exists():
            # Return empty daily note
            return DailyNote(date=date, entries=[])

        content = path.read_text()
        return DailyNote.from_markdown(date, content)

    def append_daily(self, content: str, tags: list[str] | None = None, agent: str | None = None) -> bool:
        """Append an entry to today's daily notes."""
        date = datetime.utcnow().strftime("%Y-%m-%d")
        path = self.base_path / "daily" / f"{date}.md"

        # Generate entry key from timestamp
        entry_key = datetime.utcnow().strftime("%H:%M:%S")

        entry = MemoryEntry(
            key=f"{date}/{entry_key}",
            content=content,
            tags=tags or [],
            agent=agent,
        )

        if path.exists():
            existing = path.read_text()
            lines = existing.split("\n")
        else:
            lines = [f"# Daily Notes - {date}", ""]

        # Append new entry
        lines.extend([
            f"## {entry_key}",
            "",
            content,
            "",
        ])

        if tags:
            lines.append(f"**Tags:** {', '.join(tags)}")
            lines.append("")

        path.write_text("\n".join(lines))
        self._index_document(f"daily/{entry.key}", "daily", content)
        return True

    def list_projects(self) -> list[str]:
        """List all project names."""
        projects_dir = self.base_path / "projects"
        if not projects_dir.exists():
            return []

        return sorted([
            d.name for d in projects_dir.iterdir()
            if d.is_dir() and (d / "memory.md").exists()
        ])

    def create_project(self, name: str, path: str | None = None) -> bool:
        """Create a new project memory."""
        project_dir = self.base_path / "projects" / name
        project_dir.mkdir(parents=True, exist_ok=True)

        memory_file = project_dir / "memory.md"
        if not memory_file.exists():
            content = f"# {name} - Project Memory\n\n_Project-specific context and learnings..._\n"
            memory_file.write_text(content)

        return True

    def search(self, query: str, scope: str = "all") -> list[SearchResult]:
        """Search memory content."""
        cursor = self.search_db.cursor()

        # Use FTS5 for search
        try:
            cursor.execute(
                """
                SELECT d.key, d.section, d.content, rank
                FROM documents_fts
                JOIN documents d ON d.id = documents_fts.rowid
                WHERE documents_fts MATCH ?
                ORDER BY rank
                LIMIT 20
                """,
                (query,),
            )
        except sqlite3.OperationalError:
            # FTS might not be set up correctly, fallback to simple LIKE
            cursor.execute(
                "SELECT key, section, content FROM documents WHERE content LIKE ?",
                (f"%{query}%",),
            )

        results = []
        for row in cursor.fetchall():
            # Extract excerpt around match
            content = row["content"]
            excerpt = self._extract_excerpt(content, query)

            # Calculate simple relevance score
            score = self._calculate_score(content, query)

            results.append(SearchResult(
                key=row["key"],
                section=row["section"],
                excerpt=excerpt,
                score=score,
            ))

        return sorted(results, key=lambda r: r.score, reverse=True)

    def _extract_excerpt(self, content: str, query: str, context: int = 100) -> str:
        """Extract an excerpt around the first match."""
        query_lower = query.lower()
        content_lower = content.lower()

        pos = content_lower.find(query_lower)
        if pos == -1:
            # Return first N chars
            return content[:200] + "..." if len(content) > 200 else content

        start = max(0, pos - context)
        end = min(len(content), pos + len(query) + context)

        excerpt = content[start:end]
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(content):
            excerpt = excerpt + "..."

        return excerpt

    def _calculate_score(self, content: str, query: str) -> float:
        """Calculate a simple relevance score."""
        query_lower = query.lower()
        content_lower = content.lower()

        count = content_lower.count(query_lower)
        if count == 0:
            return 0.0

        # Score based on frequency and position (earlier = better)
        first_pos = content_lower.find(query_lower)
        position_bonus = 1.0 - (first_pos / max(len(content), 1))

        return min(1.0, (count * 0.1) + (position_bonus * 0.5))

    def get_project_context(self, project_path: str) -> dict[str, Any]:
        """Get relevant context for a project path."""
        # Normalize path
        project_path = os.path.expanduser(project_path)
        project_name = os.path.basename(project_path)

        # Try exact match first
        project_memory = self.read_project(project_name)

        # Also check for project by path
        for name in self.list_projects():
            pm = self.read_project(name)
            if pm and pm.path == project_path:
                project_memory = pm
                break

        return {
            "project_name": project_name,
            "project_path": project_path,
            "memory": project_memory.content if project_memory else None,
            "global_memory": self.read_core("memory"),
            "user_profile": self.read_core("user"),
        }

    def list_core_keys(self) -> list[str]:
        """List all core memory keys."""
        core_dir = self.base_path / "core"
        if not core_dir.exists():
            return []

        return sorted([
            f.stem for f in core_dir.glob("*.md")
            if f.is_file()
        ])
