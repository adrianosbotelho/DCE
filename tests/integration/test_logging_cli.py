"""CLI accepts logging flags without breaking commands."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dce.interfaces.cli.main import app

runner = CliRunner()


def test_cli_verbose_json_log_flags(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    result = runner.invoke(
        app,
        ["--verbose", "--log-format", "json", "init", str(root), "--name", "logs"],
    )
    assert result.exit_code == 0, result.stdout
    assert (root / "dce.yaml").is_file()
