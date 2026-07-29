"""Integration: dce hooks CLI."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from dce.infrastructure.hooks import HOOK_MARKER
from dce.interfaces.cli.main import app

runner = CliRunner()
pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


def _git_init(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)


def test_cli_hooks_install_status_uninstall(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    assert runner.invoke(app, ["init", str(root), "--name", "hooks"]).exit_code == 0
    _git_init(root)

    install = runner.invoke(app, ["hooks", "install", str(root)])
    assert install.exit_code == 0, install.stdout
    assert "installed" in install.stdout

    status = runner.invoke(app, ["hooks", "status", str(root)])
    assert status.exit_code == 0
    assert "managed" in status.stdout

    hook = root / ".git" / "hooks" / "post-commit"
    assert HOOK_MARKER in hook.read_text(encoding="utf-8")

    doctor = runner.invoke(app, ["doctor", str(root)])
    assert doctor.exit_code == 0, doctor.stdout
    assert "git_hook" in doctor.stdout

    uninstall = runner.invoke(app, ["hooks", "uninstall", str(root)])
    assert uninstall.exit_code == 0
    assert not hook.exists()
