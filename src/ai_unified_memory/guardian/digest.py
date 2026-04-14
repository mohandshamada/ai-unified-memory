"""Generate a daily digest from the unified memory store."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ai_unified_memory.store import MemoryStore
from ai_unified_memory.sync import check_drift, get_hermes_mappings, get_claude_mappings


def generate_digest() -> dict:
    """Generate a digest of the unified memory store."""
    store = MemoryStore()
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    # Check daily notes
    today_daily = store.read_daily(today)
    yesterday_daily = store.read_daily(yesterday)

    # Check projects
    projects = store.list_projects()

    # Check core memories
    core_keys = store.list_core_keys()

    # Check drift
    drift = check_drift(get_hermes_mappings() + get_claude_mappings())

    # Check store size
    total_size = sum(
        f.stat().st_size for f in store.base_path.rglob("*") if f.is_file()
    )

    return {
        "date": today,
        "today_entries": len(today_daily.entries),
        "yesterday_entries": len(yesterday_daily.entries),
        "projects": projects,
        "core_keys": core_keys,
        "drift_count": len(drift),
        "drift_items": [
            {
                "native": str(d.native_path),
                "canonical": str(d.canonical_path),
                "description": d.description,
            }
            for d in drift
        ],
        "store_size_mb": round(total_size / (1024 * 1024), 2),
    }


def format_digest(digest: dict) -> str:
    """Format digest as a human-readable string."""
    lines = [
        f"🧠 *Memory Guardian Digest — {digest['date']}*",
        "",
        f"📅 *Daily Notes:*",
        f"  • Today: {digest['today_entries']} entries",
        f"  • Yesterday: {digest['yesterday_entries']} entries",
        "",
        f"📦 *Projects:* {len(digest['projects'])}",
    ]
    for project in digest["projects"]:
        lines.append(f"  • {project}")

    lines.extend([
        "",
        f"🔑 *Core Memories:* {', '.join(digest['core_keys'])}",
        "",
    ])

    if digest["drift_count"] > 0:
        lines.append(f"⚠️ *Drift Detected:* {digest['drift_count']} issues")
        for item in digest["drift_items"]:
            lines.append(f"  • {item['description']}")
    else:
        lines.append("✅ *No drift detected*")

    lines.extend([
        "",
        f"💾 *Store Size:* {digest['store_size_mb']} MB",
    ])

    return "\n".join(lines)
