"""FastMCP server for AI Unified Memory."""

from __future__ import annotations

import os
from typing import Any

from fastmcp import FastMCP

from .models import MemoryEntry
from .store import MemoryStore

mcp = FastMCP("ai-unified-memory")
store = MemoryStore()


@mcp.tool()
def memory_read(section: str, key: str) -> str:
    """Read a memory entry.

    Args:
        section: One of 'core', 'projects', 'daily', 'skills'
        key: The memory key (e.g. 'user', 'cashflow', '2026-04-13')

    Returns:
        The memory content as markdown, or an error message if not found.
    """
    if section == "core":
        entry = store.read_core(key)
        return entry.content if entry else f"[Memory not found: core/{key}]"

    if section == "projects":
        project = store.read_project(key)
        return project.content if project else f"[Project not found: {key}]"

    if section == "daily":
        daily = store.read_daily(key)
        return daily.to_markdown() if daily.entries else f"[No notes for {key}]"

    return f"[Unknown section: {section}]"


@mcp.tool()
def memory_write(section: str, key: str, content: str, tags: list[str] | None = None) -> bool:
    """Write a memory entry.

    Args:
        section: One of 'core', 'projects', 'skills'
        key: The memory key
        content: Markdown content to write
        tags: Optional tags for categorization

    Returns:
        True if successful.
    """
    agent = os.environ.get("AGENT_NAME", "unknown")

    if section == "core":
        entry = MemoryEntry(key=key, content=content, tags=tags or [], agent=agent)
        return store.write_core(entry)

    if section == "projects":
        from .models import ProjectMemory

        existing = store.read_project(key)
        project = ProjectMemory(
            name=key,
            content=content,
            created_at=existing.created_at if existing else None,
        )
        return store.write_project(project)

    return False


@mcp.tool()
def memory_search(query: str, scope: str = "all") -> list[dict[str, Any]]:
    """Search across all memory.

    Args:
        query: Search query string
        scope: Limit search scope ('all', 'core', 'projects', 'daily', 'skills')

    Returns:
        List of search results with key, section, excerpt, and score.
    """
    results = store.search(query, scope)

    # Filter by scope if requested
    if scope != "all":
        results = [r for r in results if r.section == scope]

    return [
        {
            "key": r.key,
            "section": r.section,
            "excerpt": r.excerpt,
            "score": round(r.score, 3),
        }
        for r in results[:10]
    ]


@mcp.tool()
def memory_append_daily(content: str, tags: list[str] | None = None) -> bool:
    """Append an entry to today's daily notes.

    Args:
        content: Content to append
        tags: Optional tags

    Returns:
        True if successful.
    """
    agent = os.environ.get("AGENT_NAME", "unknown")
    return store.append_daily(content, tags or [], agent=agent)


@mcp.tool()
def memory_get_project_context(project_path: str) -> dict[str, Any]:
    """Get unified context for a project.

    Args:
        project_path: Absolute or home-relative path to project directory

    Returns:
        Dict with project_name, project_path, memory, global_memory, user_profile.
    """
    context = store.get_project_context(project_path)

    return {
        "project_name": context["project_name"],
        "project_path": context["project_path"],
        "memory": context["memory"],
        "global_memory": context["global_memory"].content if context["global_memory"] else None,
        "user_profile": context["user_profile"].content if context["user_profile"] else None,
    }


@mcp.tool()
def memory_list_projects() -> list[str]:
    """List all projects with memory."""
    return store.list_projects()


@mcp.tool()
def memory_create_project(name: str, path: str | None = None) -> bool:
    """Create a new project memory.

    Args:
        name: Project name
        path: Optional absolute path to project directory

    Returns:
        True if successful.
    """
    return store.create_project(name, path)


@mcp.tool()
def memory_list_core_keys() -> list[str]:
    """List all available core memory keys."""
    return store.list_core_keys()


def run_stdio() -> None:
    """Run the MCP server over stdio."""
    mcp.run(transport="stdio")


def run_sse(host: str = "127.0.0.1", port: int = 8080) -> None:
    """Run the MCP server over SSE."""
    mcp.run(transport="sse", host=host, port=port)
