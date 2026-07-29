"""Unit tests for optional git hooks."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from dce.domain.errors import WorkspaceError
from dce.infrastructure.hooks import (
    HOOK_MARKER,
    get_hook_status,
    install_post_commit_hook,
    uninstall_post_commit_hook,
)

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


def _git_init(path: Path) -> None:
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


def test_install_and_uninstall_managed_hook(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _git_init(root)

    status = get_hook_status(root)
    assert status.installed is False

    path = install_post_commit_hook(root)
    assert path.is_file()
    assert HOOK_MARKER in path.read_text(encoding="utf-8")
    assert path.stat().st_mode & 0o111

    status = get_hook_status(root)
    assert status.installed is True
    assert status.managed is True

    removed = uninstall_post_commit_hook(root)
    assert removed == path
    assert not path.exists()


def test_refuse_overwrite_foreign_hook(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _git_init(root)
    hook = root / ".git" / "hooks" / "post-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\necho foreign\n", encoding="utf-8")

    with pytest.raises(WorkspaceError, match="foreign"):
        install_post_commit_hook(root)

    path = install_post_commit_hook(root, force=True)
    assert HOOK_MARKER in path.read_text(encoding="utf-8")


def test_status_without_git(tmp_path: Path) -> None:
    status = get_hook_status(tmp_path)
    assert status.installed is False
    assert "not a git" in status.detail
