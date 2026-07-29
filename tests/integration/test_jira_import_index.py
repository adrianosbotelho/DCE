"""Integration tests for Jira import indexing."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dce.domain.models import SearchFilters, SearchSpec
from dce.infrastructure.storage.connection import connect
from dce.infrastructure.storage.repository import SqliteDocumentRepository
from dce.interfaces.cli.main import app

runner = CliRunner()


def test_cli_index_jira_import(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    assert runner.invoke(app, ["init", str(root), "--name", "jira"]).exit_code == 0
    assert (root / "imports" / "jira").is_dir()

    (root / "imports" / "jira" / "export.json").write_text(
        """
        {
          "issues": [
            {
              "key": "PAY-125",
              "title": "TNS listener",
              "description": "ORA-12541 in prod",
              "type": "Bug",
              "priority": "High",
              "components": ["oracle"],
              "labels": ["network"],
              "assignee": "alice",
              "solution": "Restart listener and open port 1521",
              "lessons_learned": "Monitor listener health",
              "related_prs": ["https://git/pr/99"]
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    # disabled by default — force via --source
    result = runner.invoke(app, ["index", str(root), "--source", "jira"])
    assert result.exit_code == 0, result.stdout
    assert "jira_import" in result.stdout

    with connect(root / ".dce" / "dce.sqlite") as conn:
        repo = SqliteDocumentRepository(conn)
        hits = repo.search(
            SearchSpec(text="ORA-12541", filters=SearchFilters(source_types=["jira"]))
        )
        assert len(hits) == 1
        doc = hits[0].document
        assert doc.uri == "PAY-125"
        assert doc.metadata["solution"]
        assert "https://git/pr/99" in doc.related_uris
        assert "issue:PAY-125" in doc.related_uris
        assert doc.project == "PAY"
