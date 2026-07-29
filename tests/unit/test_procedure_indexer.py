"""Unit tests for procedure indexer."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from dce.domain.ports import Indexer
from dce.infrastructure.indexers.common import TextFileItem
from dce.infrastructure.indexers.procedure import ProcedureIndexer, extract_steps


def test_extract_steps_from_frontmatter_and_body() -> None:
    assert extract_steps({"steps": ["A", "B"]}, "") == ["A", "B"]
    body = "1. Check listener\n2. Open port 1521\n- skip me\n- [x] Bounce service\n"
    steps = extract_steps({}, body)
    assert steps == ["Check listener", "Open port 1521", "Bounce service"]


def test_procedure_transform(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    root.mkdir()
    text = (
        "---\ntitle: Fix ORA-12541\nseverity: high\ntags: [oracle]\n"
        "steps:\n  - Check listener\n  - Restart\n---\n\n"
        "Runbook for listener failures.\n"
    )
    item = TextFileItem(
        relative_path=".dce/procedures/ora.md",
        absolute_path=root / ".dce" / "procedures" / "ora.md",
        text=text,
        mtime=datetime.now(UTC),
    )
    indexer = ProcedureIndexer(root)
    assert isinstance(indexer, Indexer)
    doc = indexer.transform(item)
    assert doc.source_type == "procedure"
    assert doc.title == "Fix ORA-12541"
    assert "procedure" in doc.tags
    assert "high" in doc.tags
    assert doc.metadata["step_count"] == 2
    assert doc.metadata["steps"] == ["Check listener", "Restart"]
    assert doc.metadata["severity"] == "high"


def test_procedure_discover(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    proc = root / "procedures"
    proc.mkdir(parents=True)
    (proc / "boot.md").write_text("# Boot\n\n1. Step one\n", encoding="utf-8")
    indexer = ProcedureIndexer(root)
    items = list(indexer.discover({}))
    assert len(items) == 1
    doc = indexer.transform(items[0])
    assert doc.metadata["step_count"] == 1
