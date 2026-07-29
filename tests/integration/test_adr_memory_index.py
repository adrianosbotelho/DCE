"""Integration: ADR + memory indexing end-to-end."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dce.domain.models import SearchFilters, SearchSpec
from dce.infrastructure.storage.connection import connect
from dce.infrastructure.storage.repository import SqliteDocumentRepository
from dce.interfaces.cli.main import app

runner = CliRunner()


def test_cli_indexes_adr_and_memory_separately(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    assert runner.invoke(app, ["init", str(root), "--name", "s5"]).exit_code == 0

    adr_dir = root / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "ADR-001.md").write_text(
        "# ADR-001 — Offline store\n\n- **Status:** Accepted\n\nSQLite FTS5.\n",
        encoding="utf-8",
    )
    (root / "docs" / "guide.md").write_text("# Guide\n\nGeneral docs.\n", encoding="utf-8")
    (root / ".dce" / "memory" / "note.md").write_text(
        "# Memory note\n\nORA-12541 quick tip.\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["index", str(root)])
    assert result.exit_code == 0, result.stdout
    assert "adr" in result.stdout
    assert "memory" in result.stdout
    assert "markdown" in result.stdout

    with connect(root / ".dce" / "dce.sqlite") as conn:
        repo = SqliteDocumentRepository(conn)
        adr_hits = repo.search(SearchSpec(text="FTS5", filters=SearchFilters(source_types=["adr"])))
        assert len(adr_hits) == 1
        assert adr_hits[0].document.source_type == "adr"
        assert adr_hits[0].document.metadata.get("adr_number") == "001"

        mem_hits = repo.search(
            SearchSpec(text="ORA-12541", filters=SearchFilters(source_types=["memory"]))
        )
        assert len(mem_hits) == 1
        assert mem_hits[0].document.source_type == "memory"

        md_hits = repo.search(
            SearchSpec(text="General", filters=SearchFilters(source_types=["markdown"]))
        )
        assert len(md_hits) == 1

        all_adr_path = repo.search(SearchSpec(text="Offline store"))
        source_types = {h.document.source_type for h in all_adr_path}
        assert "adr" in source_types
        assert "markdown" not in source_types


def test_cli_index_source_adr_only(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    assert runner.invoke(app, ["init", str(root)]).exit_code == 0
    adr_dir = root / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "ADR-002.md").write_text(
        "# ADR-002 — Builder\n\nStatus: Accepted\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["index", str(root), "--source", "adr"])
    assert result.exit_code == 0, result.stdout
    assert "adr" in result.stdout
