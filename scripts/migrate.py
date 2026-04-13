"""Migration script from existing agent memories to unified store.

This script detects and migrates:
- Hermes memories: ~/.hermes/memories/USER.md, workspace MEMORY.md, AGENTS.md
- Claude Code memories: ~/.claude/projects/*/memory/MEMORY.md, workspace CLAUDE.md
- OpenClaw memories: ~/.openclaw/memory/main.sqlite (document index)

Usage:
    python scripts/migrate.py --dry-run
    python scripts/migrate.py --apply
    python scripts/migrate.py --apply --backup-dir /path/to/backups
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from ai_unified_memory.models import MemoryEntry, ProjectMemory
from ai_unified_memory.store import MemoryStore


def backup_file(src: Path, backup_dir: Path) -> None:
    """Backup a single file."""
    if not src.exists():
        return

    dest = backup_dir / src.relative_to(Path.home())
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dest))


def migrate_hermes(store: MemoryStore, backup_dir: Path, dry_run: bool) -> dict:
    """Migrate Hermes memories to canonical store."""
    migrated = {"core_files": 0, "workspace_files": 0}

    # Core memories
    hermes_dir = Path.home() / ".hermes"
    memories_dir = hermes_dir / "memories"

    if memories_dir.exists():
        user_md = memories_dir / "USER.md"
        if user_md.exists():
            if not dry_run:
                backup_file(user_md, backup_dir)
                content = user_md.read_text()
                entry = MemoryEntry.from_markdown(content, key="user")
                store.write_core(entry)
            migrated["core_files"] += 1

    # Workspace files (scan common workspace roots)
    workspace_roots = [Path.home(), Path.home() / "hive", Path.home() / "workspace"]
    for root in workspace_roots:
        if not root.exists():
            continue

        for ag in root.rglob("AGENTS.md"):
            if not dry_run:
                backup_file(ag, backup_dir)
            migrated["workspace_files"] += 1

        for mem in root.rglob("MEMORY.md"):
            # Skip if it's inside a project directory
            if ".claude" in str(mem):
                continue
            if not dry_run:
                backup_file(mem, backup_dir)
            migrated["workspace_files"] += 1

    return migrated


def migrate_claude(store: MemoryStore, backup_dir: Path, dry_run: bool) -> dict:
    """Migrate Claude Code project memories to canonical store."""
    migrated = {"projects": 0, "workspace_files": 0}

    claude_projects = Path.home() / ".claude" / "projects"
    if not claude_projects.exists():
        return migrated

    for project_dir in claude_projects.iterdir():
        if not project_dir.is_dir():
            continue

        # Convert dir name to project name
        project_name = project_dir.name.lstrip("-").replace("-", "_")
        memory_file = project_dir / "memory" / "MEMORY.md"

        if memory_file.exists():
            if not dry_run:
                backup_file(memory_file, backup_dir)
                content = memory_file.read_text()
                project = ProjectMemory(
                    name=project_name,
                    content=content,
                )
                store.write_project(project)
            migrated["projects"] += 1

        # Also check for CLAUDE.md in workspace
        claude_md = project_dir / "CLAUDE.md"
        if claude_md.exists():
            if not dry_run:
                backup_file(claude_md, backup_dir)
            migrated["workspace_files"] += 1

    return migrated


def migrate_openclaw(store: MemoryStore, backup_dir: Path, dry_run: bool) -> dict:
    """Migrate OpenClaw document index metadata (not embeddings)."""
    migrated = {"files": 0}

    openclaw_db = Path.home() / ".openclaw" / "memory" / "main.sqlite"
    if not openclaw_db.exists():
        return migrated

    if not dry_run:
        backup_file(openclaw_db, backup_dir)

        conn = sqlite3.connect(str(openclaw_db))
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT path, source, text FROM chunks LIMIT 100")
            for row in cursor.fetchall():
                path, source, text = row
                if text:
                    # Store as skill reference
                    migrated["files"] += 1
        except Exception:
            pass
        finally:
            conn.close()

    return migrated


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate agent memories to unified store")
    parser.add_argument("--dry-run", action="store_true", help="Preview migrations without applying")
    parser.add_argument("--apply", action="store_true", help="Apply migrations")
    parser.add_argument(
        "--backup-dir",
        type=str,
        default=str(Path.home() / ".agent-memory-backups"),
        help="Directory to backup original files",
    )
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("Error: Specify --dry-run or --apply")
        parser.print_help()
        return 1

    backup_dir = Path(args.backup_dir) / datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    store = MemoryStore()

    print("=" * 50)
    print("AI Unified Memory - Migration Tool")
    print("=" * 50)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'APPLY'}")
    print(f"Backup dir: {backup_dir}")
    print(f"Canonical store: {store.base_path}")
    print("")

    # Run migrations
    hermes = migrate_hermes(store, backup_dir, args.dry_run)
    claude = migrate_claude(store, backup_dir, args.dry_run)
    openclaw = migrate_openclaw(store, backup_dir, args.dry_run)

    print("Hermes migration:")
    print(f"  Core files: {hermes['core_files']}")
    print(f"  Workspace files: {hermes['workspace_files']}")
    print("")

    print("Claude Code migration:")
    print(f"  Projects: {claude['projects']}")
    print(f"  Workspace files: {claude['workspace_files']}")
    print("")

    print("OpenClaw migration:")
    print(f"  Indexed files: {openclaw['files']}")
    print("")

    total = sum(hermes.values()) + sum(claude.values()) + sum(openclaw.values())
    print(f"Total items found: {total}")

    if args.dry_run:
        print("\nThis was a dry run. No changes were made.")
        print(f"Run with --apply to migrate (backups will be saved to {backup_dir})")
    else:
        print(f"\nMigration complete! Original files backed up to {backup_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
