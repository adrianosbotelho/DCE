"""CLI smoke tests via Typer CliRunner."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dce.interfaces.cli.main import app

runner = CliRunner()


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "dce" in result.stdout


def test_cli_init_and_doctor(tmp_path: Path) -> None:
    ws = tmp_path / "workspace"
    init_result = runner.invoke(app, ["init", str(ws), "--name", "cli-demo"])
    assert init_result.exit_code == 0, init_result.stdout
    assert "schema" in init_result.stdout

    doctor_result = runner.invoke(app, ["doctor", str(ws)])
    assert doctor_result.exit_code == 0, doctor_result.stdout
    assert "fts5" in doctor_result.stdout


def test_cli_doctor_fails_without_init(tmp_path: Path) -> None:
    result = runner.invoke(app, ["doctor", str(tmp_path / "missing")])
    assert result.exit_code == 1
