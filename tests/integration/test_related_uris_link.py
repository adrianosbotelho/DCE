"""Integration: related_uris linking between jira and git."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from dce.domain.models import SearchFilters, SearchSpec
from dce.infrastructure.storage.connection import connect
from dce.infrastructure.storage.repository import SqliteDocumentRepository
from dce.interfaces.cli.main import app

runner = CliRunner()
pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def test_cli_index_links_issue_and_commit(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    assert runner.invoke(app, ["init", str(root), "--name", "link"]).exit_code == 0

    (root / "imports" / "jira" / "export.json").write_text(
        """
        {
          "issues": [
            {
              "key": "PAY-42",
              "title": "Listener flap",
              "description": "ORA-12541",
              "related_prs": ["https://git/pr/7"]
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    _git(root, "init")
    _git(root, "config", "user.email", "dev@example.com")
    _git(root, "config", "user.name", "Dev")
    (root / "fix.py").write_text("pass\n", encoding="utf-8")
    _git(root, "add", "fix.py")
    _git(
        root,
        "commit",
        "-m",
        "PAY-42: fix listener\n\nCloses via https://github.com/acme/pay/pull/7",
    )

    # Index both sources; linker runs after upserts.
    assert runner.invoke(app, ["index", str(root), "--source", "jira"]).exit_code == 0
    result = runner.invoke(app, ["index", str(root), "--source", "git"])
    assert result.exit_code == 0, result.stdout

    with connect(root / ".dce" / "dce.sqlite") as conn:
        repo = SqliteDocumentRepository(conn)
        git_hits = repo.search(
            SearchSpec(text="PAY-42", filters=SearchFilters(source_types=["git"]), limit=10)
        )
        jira_hits = repo.search(
            SearchSpec(text="PAY-42", filters=SearchFilters(source_types=["jira"]), limit=10)
        )
        assert git_hits and jira_hits
        git_doc = git_hits[0].document
        jira_doc = jira_hits[0].document
        assert "issue:PAY-42" in git_doc.related_uris
        commit_links = [u for u in jira_doc.related_uris if u.startswith("commit:")]
        assert commit_links
        assert commit_links[0] in git_doc.related_uris
        assert "https://github.com/acme/pay/pull/7" in jira_doc.related_uris
        assert "https://git/pr/7" in jira_doc.related_uris
