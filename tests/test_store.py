"""Tests for the memory store."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ai_unified_memory.models import MemoryEntry, ProjectMemory
from ai_unified_memory.store import MemoryStore


@pytest.fixture
def store():
    """Create a temporary memory store."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield MemoryStore(base_path=tmpdir)


class TestMemoryStore:
    def test_ensure_structure_creates_defaults(self, store):
        assert (store.base_path / "core").exists()
        assert (store.base_path / "daily").exists()
        assert (store.base_path / "projects").exists()
        assert (store.base_path / "skills").exists()

        # Default core files
        assert (store.base_path / "core" / "user.md").exists()
        assert (store.base_path / "core" / "agents.md").exists()

    def test_read_write_core(self, store):
        entry = MemoryEntry(key="test", content="Hello world", tags=["test"])
        assert store.write_core(entry) is True

        read = store.read_core("test")
        assert read is not None
        assert read.content == "Hello world"
        assert read.tags == ["test"]

    def test_read_missing_core(self, store):
        assert store.read_core("nonexistent") is None

    def test_read_write_project(self, store):
        project = ProjectMemory(name="my-project", content="# My Project\n", path="/tmp/my-project")
        assert store.write_project(project) is True

        read = store.read_project("my-project")
        assert read is not None
        assert read.name == "my-project"
        assert read.path == "/tmp/my-project"
        assert "# My Project" in read.content

        # Verify frontmatter on disk
        path = store.base_path / "projects" / "my-project" / "memory.md"
        content = path.read_text()
        assert "path: /tmp/my-project" in content

    def test_list_projects(self, store):
        store.create_project("alpha")
        store.create_project("beta")

        projects = store.list_projects()
        assert "alpha" in projects
        assert "beta" in projects

    def test_append_daily(self, store):
        assert store.append_daily("First note", tags=["note"]) is True
        assert store.append_daily("Second note") is True

        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        daily = store.read_daily(today)

        assert len(daily.entries) == 2
        assert "First note" in [e.content for e in daily.entries]
        assert "Second note" in [e.content for e in daily.entries]

    def test_search(self, store):
        entry = MemoryEntry(key="python", content="Python is great for AI agents.")
        store.write_core(entry)

        results = store.search("Python")
        assert len(results) > 0
        assert any(r.key == "core/python" for r in results)

    def test_get_project_context(self, store):
        store.create_project("cashflow")
        store.write_project(ProjectMemory(name="cashflow", content="# Cashflow\n\nApp"))

        ctx = store.get_project_context("/root/cashflow")
        assert ctx["project_name"] == "cashflow"
        assert "Cashflow" in ctx["memory"]
