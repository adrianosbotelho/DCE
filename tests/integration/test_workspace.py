"""Integration tests for workspace init and doctor."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from dce.domain.errors import WorkspaceError
from dce.infrastructure.storage.migrations import CURRENT_SCHEMA_VERSION
from dce.infrastructure.storage.workspace import (
    doctor_workspace,
    init_workspace,
    load_config,
)


def test_init_creates_config_and_db(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    result = init_workspace(root, name="demo")
    assert result.created_config is True
    assert result.created_database is True
    assert result.schema_version == CURRENT_SCHEMA_VERSION
    assert result.config_path.is_file()
    assert result.database_path.is_file()

    config = yaml.safe_load(result.config_path.read_text(encoding="utf-8"))
    assert config["workspace"]["name"] == "demo"

    again = init_workspace(root)
    assert again.created_config is False
    assert again.schema_version == CURRENT_SCHEMA_VERSION


def test_init_force_overwrites_config(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    init_workspace(root, name="first")
    init_workspace(root, name="second", force=True)
    config = yaml.safe_load((root / "dce.yaml").read_text(encoding="utf-8"))
    assert config["workspace"]["name"] == "second"


def test_doctor_healthy_after_init(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    init_workspace(root)
    report = doctor_workspace(root)
    assert report.healthy is True
    names = {c.name for c in report.checks}
    assert names == {"config", "database", "fts5", "schema"}


def test_doctor_missing_config(tmp_path: Path) -> None:
    report = doctor_workspace(tmp_path / "empty")
    assert report.healthy is False
    assert report.checks[0].name == "config"
    assert report.checks[0].ok is False


def test_doctor_missing_database(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    root.mkdir()
    (root / "dce.yaml").write_text(
        yaml.safe_dump(
            {"workspace": {"name": "x", "database": ".dce/dce.sqlite"}},
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    report = doctor_workspace(root)
    assert report.healthy is False
    assert any(c.name == "database" and not c.ok for c in report.checks)


def test_load_config_rejects_non_mapping(tmp_path: Path) -> None:
    path = tmp_path / "dce.yaml"
    path.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(WorkspaceError):
        load_config(path)
