"""Sync layer to prevent drift between agent-native paths and canonical store."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from .store import MemoryStore


@dataclass
class SymlinkMapping:
    """A symlink mapping from native path to canonical path."""

    native: Path
    canonical: Path
    description: str


@dataclass
class DriftReport:
    """Report of detected drift."""

    native_path: Path
    canonical_path: Path
    native_hash: str
    canonical_hash: str
    description: str


def get_hermes_mappings(base_path: Path | str | None = None) -> list[SymlinkMapping]:
    """Get recommended symlink mappings for Hermes."""
    store = MemoryStore(base_path)
    home = Path.home()

    return [
        SymlinkMapping(
            native=home / ".hermes" / "SOUL.md",
            canonical=store.base_path / "core" / "soul.md",
            description="Hermes SOUL.md -> canonical soul.md",
        ),
        SymlinkMapping(
            native=home / ".hermes" / "memories" / "USER.md",
            canonical=store.base_path / "core" / "user.md",
            description="Hermes USER.md -> canonical user.md",
        ),
    ]


def get_claude_mappings(base_path: Path | str | None = None) -> list[SymlinkMapping]:
    """Get recommended symlink mappings for Claude Code."""
    store = MemoryStore(base_path)
    home = Path.home()
    mappings = []

    # Map all existing Claude project memories
    claude_projects = home / ".claude" / "projects"
    if claude_projects.exists():
        for project_dir in claude_projects.iterdir():
            if not project_dir.is_dir():
                continue

            project_name = project_dir.name.lstrip("-").replace("-", "_")
            native_memory = project_dir / "memory" / "MEMORY.md"
            canonical_memory = store.base_path / "projects" / project_name / "memory.md"

            mappings.append(
                SymlinkMapping(
                    native=native_memory,
                    canonical=canonical_memory,
                    description=f"Claude project {project_name} memory -> canonical",
                )
            )

    return mappings


def _file_hash(path: Path) -> str:
    """Compute a simple hash of file content."""
    if not path.exists():
        return ""

    import hashlib

    content = path.read_bytes()
    return hashlib.sha256(content).hexdigest()[:16]


def ensure_symlinks(
    mappings: list[SymlinkMapping],
    dry_run: bool = False,
) -> list[SymlinkMapping]:
    """Create or update symlinks for given mappings.

    Returns:
        List of mappings that were created or updated.
    """
    created = []

    for mapping in mappings:
        native = mapping.native
        canonical = mapping.canonical

        # Ensure parent directory exists
        if not dry_run:
            native.parent.mkdir(parents=True, exist_ok=True)

        # If native exists but is a regular file, back it up
        if native.exists() and native.is_file() and not native.is_symlink():
            backup = native.with_suffix(native.suffix + ".backup")
            if not dry_run:
                shutil.copy2(str(native), str(backup))

        # Create or update symlink
        if native.exists() or native.is_symlink():
            if not dry_run:
                native.unlink()

        if not dry_run:
            native.symlink_to(canonical)

        created.append(mapping)

    return created


def check_drift(
    mappings: list[SymlinkMapping],
    additional_paths: dict[Path, Path] | None = None,
) -> list[DriftReport]:
    """Check for drift between native and canonical files.

    Checks:
    1. Symlink mappings where native file exists but differs from canonical
    2. Additional paths where agent wrote directly to native location
    """
    drift_reports = []

    all_checks = list(mappings)
    if additional_paths:
        for native, canonical in additional_paths.items():
            all_checks.append(
                SymlinkMapping(
                    native=native,
                    canonical=canonical,
                    description="Additional drift check path",
                )
            )

    for mapping in all_checks:
        native = mapping.native
        canonical = mapping.canonical

        if not native.exists():
            continue

        # If it's a symlink pointing to canonical, no drift
        if native.is_symlink() and os.path.realpath(native) == os.path.realpath(canonical):
            continue

        native_hash = _file_hash(native)
        canonical_hash = _file_hash(canonical)

        if native_hash != canonical_hash:
            drift_reports.append(
                DriftReport(
                    native_path=native,
                    canonical_path=canonical,
                    native_hash=native_hash,
                    canonical_hash=canonical_hash,
                    description=mapping.description,
                )
            )

    return drift_reports


def repair_drift(report: DriftReport, strategy: str = "merge", dry_run: bool = False) -> bool:
    """Repair drift by merging or overwriting.

    Args:
        report: The drift report to repair
        strategy: One of 'merge', 'canonical-wins', 'native-wins'
        dry_run: If True, only log what would happen

    Returns:
        True if repair was successful
    """
    native = report.native_path
    canonical = report.canonical_path

    if strategy == "canonical-wins":
        if not dry_run:
            shutil.copy2(str(canonical), str(native))
        return True

    if strategy == "native-wins":
        if not dry_run:
            shutil.copy2(str(native), str(canonical))
        return True

    if strategy == "merge":
        native_content = native.read_text() if native.exists() else ""
        canonical_content = canonical.read_text() if canonical.exists() else ""

        merged = _merge_markdown(native_content, canonical_content)

        if not dry_run:
            canonical.write_text(merged)
            if not native.is_symlink():
                native.write_text(merged)

        return True

    return False


def _merge_markdown(left: str, right: str) -> str:
    """Merge two markdown documents, deduplicating sections."""
    import re

    # Simple merge strategy: concatenate and deduplicate by section header
    sections = {}

    for content in [left, right]:
        # Split by headers
        parts = re.split(r"\n(?=#+ )", content.strip())
        for part in parts:
            if not part.strip():
                continue

            # Use first line as key
            lines = part.strip().split("\n")
            key = lines[0].strip()

            if key not in sections:
                sections[key] = part.strip()
            elif len(part.strip()) > len(sections[key]):
                # Keep the longer/more detailed version
                sections[key] = part.strip()

    return "\n\n".join(sections.values())


def run_full_sync(
    base_path: Path | str | None = None,
    repair_strategy: str = "merge",
    dry_run: bool = False,
) -> dict:
    """Run a full sync: ensure symlinks and repair any drift.

    Returns:
        Dict with created symlinks and drift reports.
    """
    hermes_mappings = get_hermes_mappings(base_path)
    claude_mappings = get_claude_mappings(base_path)

    all_mappings = hermes_mappings + claude_mappings

    created = ensure_symlinks(all_mappings, dry_run=dry_run)
    drift = check_drift(all_mappings)

    repaired = []
    for report in drift:
        success = repair_drift(report, strategy=repair_strategy, dry_run=dry_run)
        if success:
            repaired.append(report)

    return {
        "created_symlinks": [m.description for m in created],
        "drift_detected": len(drift),
        "drift_repaired": len(repaired),
        "dry_run": dry_run,
    }
