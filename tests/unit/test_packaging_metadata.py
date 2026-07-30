"""Unit checks for packaging metadata (PB-090)."""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_pyproject_distribution_name_and_script() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]
    assert project["name"] == "dev-context-engine"
    assert project["scripts"]["dce"] == "dce.interfaces.cli.main:app"
    assert "License :: OSI Approved :: MIT License" in project["classifiers"]
    assert "Homepage" in project["urls"]

    wheel = data["tool"]["hatch"]["build"]["targets"]["wheel"]
    assert wheel["packages"] == ["src/dce"]
    assert wheel["force-include"] == {
        "src/dce/interfaces/web/static/index.html": (
            "dce/interfaces/web/static/index.html"
        )
    }


def test_packaging_docs_exist() -> None:
    assert (ROOT / "docs" / "Packaging.md").is_file()
    assert (ROOT / "docs" / "adr" / "ADR-005.md").is_file()
    assert (ROOT / "src" / "dce" / "py.typed").is_file()
    assert (ROOT / "LICENSE").is_file()
