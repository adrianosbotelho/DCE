"""Unit tests for ADR and Memory indexers."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from dce.domain.ports import Indexer
from dce.infrastructure.indexers.adr import AdrIndexer, extract_adr_number, extract_adr_status
from dce.infrastructure.indexers.common import TextFileItem
from dce.infrastructure.indexers.memory import MemoryIndexer


def test_extract_adr_number_and_status() -> None:
    assert extract_adr_number("docs/adr/ADR-001.md", "Title", {}) == "001"
    assert extract_adr_number("x.md", "ADR-7 Decision", {"number": 12}) == "012"
    body = "- **Status:** Accepted\n\nContext\n"
    assert extract_adr_status(body, {}) == "Accepted"
    assert extract_adr_status("no status", {"status": "Proposed"}) == "Proposed"


def test_adr_transform(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    root.mkdir()
    indexer = AdrIndexer(root)
    assert isinstance(indexer, Indexer)
    item = TextFileItem(
        relative_path="docs/adr/ADR-001.md",
        absolute_path=root / "docs/adr/ADR-001.md",
        text="# ADR-001 — SQLite\n\n- **Status:** Accepted\n\nUse FTS5.\n",
        mtime=datetime(2026, 7, 29, tzinfo=UTC),
    )
    doc = indexer.transform(item)
    assert doc.source_type == "adr"
    assert doc.metadata["adr_number"] == "001"
    assert doc.metadata["status"] == "Accepted"
    assert "ADR-001" in doc.tags
    assert "Accepted" in doc.tags


def test_memory_transform_and_discover(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    mem = root / ".dce" / "memory"
    mem.mkdir(parents=True)
    (mem / "tip.md").write_text(
        "---\ntitle: Tip\ntags: [oracle]\n---\n\nRemember ORA-12541 checklist.\n",
        encoding="utf-8",
    )
    indexer = MemoryIndexer(root)
    assert isinstance(indexer, Indexer)
    items = list(indexer.discover({}))
    assert len(items) == 1
    doc = indexer.transform(items[0])
    assert doc.source_type == "memory"
    assert "memory" in doc.tags
    assert doc.title == "Tip"
