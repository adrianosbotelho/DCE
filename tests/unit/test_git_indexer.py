"""Unit tests for git indexer helpers."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from dce.domain.ports import Indexer
from dce.infrastructure.indexers.git import (
    GitIndexer,
    extract_issue_keys,
    parse_git_bodies,
    parse_git_log,
    read_commits,
)

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


def test_extract_issue_keys() -> None:
    keys = extract_issue_keys("Fix PAY-12 listener", "See also PROJ-3 and pay-12")
    assert keys == ["PAY-12", "PROJ-3"]


def test_parse_git_log_and_bodies() -> None:
    sample = (
        "\x1e"
        "abc123\x1fabc\x1fAda\x1fada@ex.com\x1f2026-07-29T12:00:00+00:00\x1fFix PAY-1\n"
        "src/a.py\n"
        "README.md\n"
        "\x1e"
        "def456\x1fdef\x1fBob\x1fbob@ex.com\x1f2026-07-28T12:00:00+00:00\x1fDocs\n"
        "docs/x.md\n"
    )
    commits = parse_git_log(sample)
    assert len(commits) == 2
    assert commits[0].sha == "abc123"
    assert commits[0].paths == ("src/a.py", "README.md")
    assert commits[0].subject == "Fix PAY-1"

    bodies = parse_git_bodies("\x1eabc123\x1dBody line\nMore\n\x1edef456\x1d")
    assert bodies["abc123"] == "Body line\nMore"


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "dev@example.com"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Dev"],
        cwd=path,
        check=True,
        capture_output=True,
    )


def test_read_commits_from_real_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    (repo / "app.py").write_text("print('hi')\n", encoding="utf-8")
    subprocess.run(["git", "add", "app.py"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "PAY-99: add app\n\nListener notes ORA-12541"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    commits = read_commits(repo, max_commits=10, include_body=True)
    assert len(commits) == 1
    assert commits[0].subject.startswith("PAY-99")
    assert "app.py" in commits[0].paths
    assert "ORA-12541" in commits[0].body or "Listener" in commits[0].body

    indexer = GitIndexer(repo)
    assert isinstance(indexer, Indexer)
    items = list(indexer.discover({"max_commits": 5, "include_body": True}))
    assert len(items) == 1
    doc = indexer.transform(items[0])
    assert doc.source_type == "git"
    assert "PAY-99" in doc.tags
    assert "app.py" in doc.related_uris
    assert "issue:PAY-99" in doc.related_uris
    assert any(u.startswith("commit:") for u in doc.related_uris)
    assert doc.metadata["short_sha"]


def test_discover_skips_non_repo(tmp_path: Path) -> None:
    indexer = GitIndexer(tmp_path)
    assert list(indexer.discover({})) == []
