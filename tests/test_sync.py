"""Tests for the sync layer."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ai_unified_memory.sync import (
    SymlinkMapping,
    check_drift,
    ensure_symlinks,
    repair_drift,
    _merge_markdown,
)


class TestSyncLayer:
    def test_ensure_symlinks_creates_link(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            native = Path(tmpdir) / "native" / "test.md"
            canonical = Path(tmpdir) / "canonical" / "test.md"
            canonical.parent.mkdir(parents=True, exist_ok=True)
            canonical.write_text("canonical content")

            mapping = SymlinkMapping(
                native=native,
                canonical=canonical,
                description="test mapping",
            )

            created = ensure_symlinks([mapping])
            assert len(created) == 1
            assert native.is_symlink()
            assert native.read_text() == "canonical content"

    def test_check_drift_no_drift(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            canonical = Path(tmpdir) / "canonical.md"
            canonical.write_text("same")
            native = Path(tmpdir) / "native.md"
            native.symlink_to(canonical)

            mapping = SymlinkMapping(
                native=native,
                canonical=canonical,
                description="test",
            )

            drift = check_drift([mapping])
            assert len(drift) == 0

    def test_check_drift_detects_divergence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            canonical = Path(tmpdir) / "canonical.md"
            native = Path(tmpdir) / "native.md"
            canonical.write_text("canonical")
            native.write_text("native")

            mapping = SymlinkMapping(
                native=native,
                canonical=canonical,
                description="test",
            )

            drift = check_drift([mapping])
            assert len(drift) == 1
            assert drift[0].native_hash != drift[0].canonical_hash

    def test_repair_drift_canonical_wins(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            canonical = Path(tmpdir) / "canonical.md"
            native = Path(tmpdir) / "native.md"
            canonical.write_text("canonical")
            native.write_text("native")

            from ai_unified_memory.sync import DriftReport
            report = DriftReport(
                native_path=native,
                canonical_path=canonical,
                native_hash="abc",
                canonical_hash="def",
                description="test",
            )

            assert repair_drift(report, strategy="canonical-wins") is True
            assert native.read_text() == "canonical"

    def test_merge_markdown(self):
        left = "# Header A\n\nContent A\n\n# Header B\n\nContent B"
        right = "# Header A\n\nUpdated Content A\n\n# Header C\n\nContent C"

        merged = _merge_markdown(left, right)
        assert "# Header A" in merged
        assert "Updated Content A" in merged
        assert "# Header B" in merged
        assert "# Header C" in merged
