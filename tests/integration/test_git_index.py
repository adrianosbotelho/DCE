"""Integration: git indexer via CLI into SQLite."""

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


def test_cli_index_git(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    assert runner.invoke(app, ["init", str(root), "--name", "gitws"]).exit_code == 0

    _git(root, "init")
    _git(root, "config", "user.email", "dev@example.com")
    _git(root, "config", "user.name", "Dev")
    (root / "service.py").write_text("x = 1\n", encoding="utf-8")
    _git(root, "add", "service.py")
    _git(root, "commit", "-m", "PAY-7: bootstrap service\n\nHandles ORA-12541 retries")

    result = runner.invoke(app, ["index", str(root), "--source", "git"])
    assert result.exit_code == 0, result.stdout
    assert "git" in result.stdout

    with connect(root / ".dce" / "dce.sqlite") as conn:
        repo = SqliteDocumentRepository(conn)
        hits = repo.search(
            SearchSpec(text="ORA-12541", filters=SearchFilters(source_types=["git"]))
        )
        assert len(hits) >= 1
        doc = hits[0].document
        assert doc.source_type == "git"
        assert "PAY-7" in doc.tags
        assert "service.py" in doc.metadata["paths"]
