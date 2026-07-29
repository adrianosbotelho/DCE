"""Integration: snippet indexer via CLI."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dce.domain.models import SearchFilters, SearchSpec
from dce.infrastructure.storage.connection import connect
from dce.infrastructure.storage.repository import SqliteDocumentRepository
from dce.interfaces.cli.main import app

runner = CliRunner()


def test_cli_indexes_snippets_separately(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    assert runner.invoke(app, ["init", str(root), "--name", "snip"]).exit_code == 0
    assert (root / ".dce" / "snippets").is_dir()

    (root / ".dce" / "snippets" / "ora-check.md").write_text(
        "---\ntitle: ORA-12541 check\nlanguage: bash\n---\n\n"
        "```bash\nlsnrctl status | grep ORA-12541\n```\n",
        encoding="utf-8",
    )
    (root / "docs").mkdir()
    (root / "docs" / "guide.md").write_text("# Guide\n\nGeneral docs.\n", encoding="utf-8")

    result = runner.invoke(app, ["index", str(root)])
    assert result.exit_code == 0, result.stdout
    assert "snippet" in result.stdout

    with connect(root / ".dce" / "dce.sqlite") as conn:
        repo = SqliteDocumentRepository(conn)
        hits = repo.search(
            SearchSpec(
                text="ORA-12541",
                filters=SearchFilters(source_types=["snippet"]),
                limit=10,
            )
        )
        assert len(hits) == 1
        doc = hits[0].document
        assert doc.source_type == "snippet"
        assert doc.metadata["language"] == "bash"
        assert "lsnrctl" in (doc.metadata.get("code") or "")

        md_hits = repo.search(
            SearchSpec(
                text="lsnrctl",
                filters=SearchFilters(source_types=["markdown"]),
                limit=20,
            )
        )
        assert all("snippets" not in h.document.uri for h in md_hits)
