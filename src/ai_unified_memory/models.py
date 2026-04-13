"""Pydantic models for AI Unified Memory."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MemorySection(str, Enum):
    """Valid memory sections."""

    CORE = "core"
    DAILY = "daily"
    PROJECTS = "projects"
    SKILLS = "skills"


class CoreKey(str, Enum):
    """Keys within the core section."""

    USER = "user"
    AGENTS = "agents"
    SOUL = "soul"
    MEMORY = "memory"


class MemoryEntry(BaseModel):
    """A single memory entry with metadata."""

    key: str = Field(..., description="Unique key for this memory")
    content: str = Field(..., description="Markdown content")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    agent: str | None = Field(None, description="Which agent created this entry")
    source: str | None = Field(None, description="Source context (file, conversation ID, etc.)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extra metadata")

    def to_markdown(self) -> str:
        """Convert to markdown with YAML frontmatter."""
        import yaml

        frontmatter = {
            "key": self.key,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "agent": self.agent,
            "source": self.source,
            **self.metadata,
        }
        # Remove None values
        frontmatter = {k: v for k, v in frontmatter.items() if v is not None}

        yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        return f"---\n{yaml_str}---\n\n{self.content}\n"

    @classmethod
    def from_markdown(cls, markdown: str, key: str | None = None) -> MemoryEntry:
        """Parse a markdown file with YAML frontmatter."""
        import yaml

        if markdown.startswith("---"):
            parts = markdown.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                content = parts[2].strip()

                return cls(
                    key=key or frontmatter.get("key", "unknown"),
                    content=content,
                    tags=frontmatter.get("tags", []),
                    created_at=datetime.fromisoformat(
                        frontmatter.get("created_at", datetime.utcnow().isoformat())
                    ),
                    updated_at=datetime.fromisoformat(
                        frontmatter.get("updated_at", datetime.utcnow().isoformat())
                    ),
                    agent=frontmatter.get("agent"),
                    source=frontmatter.get("source"),
                    metadata={
                        k: v
                        for k, v in frontmatter.items()
                        if k not in {"key", "tags", "created_at", "updated_at", "agent", "source"}
                    },
                )

        # No frontmatter - treat entire content as markdown
        return cls(key=key or "unknown", content=markdown.strip())


class ProjectMemory(BaseModel):
    """Memory for a specific project."""

    name: str = Field(..., description="Project name")
    path: str | None = Field(None, description="Absolute path to project directory")
    content: str = Field(default="", description="Project memory markdown content")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SearchResult(BaseModel):
    """Result from a memory search."""

    key: str = Field(..., description="Memory key")
    section: str = Field(..., description="Section (core, daily, projects, skills)")
    excerpt: str = Field(..., description="Matching excerpt")
    score: float = Field(..., description="Relevance score (0-1)")
    metadata: dict[str, Any] = Field(default_factory=dict)


class DailyNote(BaseModel):
    """A daily note entry."""

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    entries: list[MemoryEntry] = Field(default_factory=list)

    @classmethod
    def from_markdown(cls, date: str, markdown: str) -> DailyNote:
        """Parse daily note markdown."""
        entries = []

        # Split by entry separators (## headers)
        import re

        sections = re.split(r"\n## ", markdown)
        header = sections[0].strip()

        for section in sections[1:]:
            if not section.strip():
                continue
            lines = section.split("\n", 1)
            entry_key = lines[0].strip()
            entry_content = lines[1].strip() if len(lines) > 1 else ""

            entry = MemoryEntry(
                key=f"{date}/{entry_key}",
                content=entry_content,
                created_at=datetime.utcnow(),
            )
            entries.append(entry)

        return cls(date=date, entries=entries)

    def to_markdown(self) -> str:
        """Convert to markdown."""
        lines = [f"# Daily Notes - {self.date}\n"]

        for entry in self.entries:
            lines.append(f"## {entry.key.split('/')[-1]}")
            lines.append("")
            lines.append(entry.content)
            lines.append("")

        return "\n".join(lines)
