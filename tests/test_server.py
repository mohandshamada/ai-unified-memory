"""Tests for the MCP server tools."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_unified_memory.server import (
    memory_append_daily,
    memory_create_project,
    memory_get_project_context,
    memory_list_projects,
    memory_read,
    memory_write,
    store,
)


@pytest.fixture(autouse=True)
def temp_store():
    """Override the store's base path for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_base = store.base_path
        store.base_path = Path(tmpdir)
        store._ensure_structure()
        store._init_search_db()
        yield
        store.base_path = original_base


def test_memory_read_write_core():
    assert memory_write("core", "user", "# My Name") is True
    content = memory_read("core", "user")
    assert "# My Name" in content


def test_memory_read_write_project():
    assert memory_create_project("test-project") is True
    assert memory_write("projects", "test-project", "# Project Details") is True
    content = memory_read("projects", "test-project")
    assert "# Project Details" in content


def test_memory_append_daily():
    assert memory_append_daily("Something happened") is True
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    content = memory_read("daily", today)
    assert "Something happened" in content


def test_memory_list_projects():
    memory_create_project("p1")
    memory_create_project("p2")
    projects = memory_list_projects()
    assert "p1" in projects
    assert "p2" in projects


def test_memory_get_project_context():
    memory_create_project("my-app", path="/home/user/my-app")
    memory_write("core", "memory", "Global info")
    
    ctx = memory_get_project_context("/home/user/my-app")
    assert ctx["project_name"] == "my-app"
    assert "Global info" in ctx["global_memory"]
