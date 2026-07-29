"""Integration: incident indexer via CLI."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dce.domain.models import SearchFilters, SearchSpec
from dce.infrastructure.storage.connection import connect
from dce.infrastructure.storage.repository import SqliteDocumentRepository
from dce.interfaces.cli.main import app

runner = CliRunner()


def test_cli_indexes_incidents_separately(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    assert runner.invoke(app, ["init", str(root), "--name", "inc"]).exit_code == 0
    assert (root / ".dce" / "incidents").is_dir()

    (root / ".dce" / "incidents" / "ora-outage.md").write_text(
        "---\ntitle: ORA-12541 outage\nseverity: sev2\nstatus: resolved\n"
        "error_codes: [ORA-12541]\nresolution: Opened port 1521\n"
        "technology: oracle\n---\n\n"
        "Listener unreachable in prod.\n",
        encoding="utf-8",
    )
    (root / "docs").mkdir()
    (root / "docs" / "guide.md").write_text("# Guide\n\nGeneral docs.\n", encoding="utf-8")

    result = runner.invoke(app, ["index", str(root)])
    assert result.exit_code == 0, result.stdout
    assert "incident" in result.stdout

    with connect(root / ".dce" / "dce.sqlite") as conn:
        repo = SqliteDocumentRepository(conn)
        hits = repo.search(
            SearchSpec(
                text="ORA-12541",
                filters=SearchFilters(source_types=["incident"]),
                limit=10,
            )
        )
        assert len(hits) == 1
        doc = hits[0].document
        assert doc.source_type == "incident"
        assert doc.metadata["status"] == "resolved"
        assert doc.technology == "oracle"

        md_hits = repo.search(
            SearchSpec(
                text="unreachable",
                filters=SearchFilters(source_types=["markdown"]),
                limit=20,
            )
        )
        assert all("incidents" not in h.document.uri for h in md_hits)
