"""Integration: procedure indexer via CLI."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dce.domain.models import SearchFilters, SearchSpec
from dce.infrastructure.storage.connection import connect
from dce.infrastructure.storage.repository import SqliteDocumentRepository
from dce.interfaces.cli.main import app

runner = CliRunner()


def test_cli_indexes_procedures_separately(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    assert runner.invoke(app, ["init", str(root), "--name", "proc"]).exit_code == 0
    assert (root / ".dce" / "procedures").is_dir()

    (root / ".dce" / "procedures" / "ora-listener.md").write_text(
        "---\ntitle: ORA-12541 listener\nseverity: high\ntechnology: oracle\n---\n\n"
        "1. Check `lsnrctl status`\n"
        "2. Restart listener\n"
        "3. Verify port 1521\n",
        encoding="utf-8",
    )
    (root / "docs").mkdir()
    (root / "docs" / "guide.md").write_text("# Guide\n\nGeneral docs.\n", encoding="utf-8")

    result = runner.invoke(app, ["index", str(root)])
    assert result.exit_code == 0, result.stdout
    assert "procedure" in result.stdout

    with connect(root / ".dce" / "dce.sqlite") as conn:
        repo = SqliteDocumentRepository(conn)
        hits = repo.search(
            SearchSpec(
                text="ORA-12541",
                filters=SearchFilters(source_types=["procedure"]),
                limit=10,
            )
        )
        assert len(hits) == 1
        doc = hits[0].document
        assert doc.source_type == "procedure"
        assert doc.metadata["step_count"] == 3
        assert doc.technology == "oracle"

        # Not double-indexed as markdown
        md_hits = repo.search(
            SearchSpec(
                text="listener",
                filters=SearchFilters(source_types=["markdown"]),
                limit=20,
            )
        )
        assert all("procedures" not in h.document.uri for h in md_hits)
