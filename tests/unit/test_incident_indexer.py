"""Unit tests for incident indexer."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from dce.domain.ports import Indexer
from dce.infrastructure.indexers.common import TextFileItem
from dce.infrastructure.indexers.incident import IncidentIndexer


def test_incident_transform(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    root.mkdir()
    text = (
        "---\ntitle: Listener outage\nseverity: sev1\nstatus: resolved\n"
        "error_codes: [ORA-12541]\nresolution: Restarted listener\n"
        "root_cause: Port blocked\nimpact: Payments delayed\n---\n\n"
        "Postmortem for ORA-12541.\n"
    )
    item = TextFileItem(
        relative_path=".dce/incidents/ora.md",
        absolute_path=root / ".dce" / "incidents" / "ora.md",
        text=text,
        mtime=datetime.now(UTC),
    )
    indexer = IncidentIndexer(root)
    assert isinstance(indexer, Indexer)
    doc = indexer.transform(item)
    assert doc.source_type == "incident"
    assert "incident" in doc.tags
    assert "sev1" in doc.tags
    assert "ORA-12541" in doc.tags
    assert doc.metadata["resolution"] == "Restarted listener"
    assert doc.metadata["error_codes"] == ["ORA-12541"]
    assert "Restarted listener" in doc.summary


def test_incident_discover(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    inc = root / "incidents"
    inc.mkdir(parents=True)
    (inc / "outage.md").write_text("# Outage\n\nORA-12541 hit prod.\n", encoding="utf-8")
    indexer = IncidentIndexer(root)
    items = list(indexer.discover({}))
    assert len(items) == 1
    doc = indexer.transform(items[0])
    assert doc.source_type == "incident"
