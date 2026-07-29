"""Version / release metadata checks."""

from __future__ import annotations

import tomllib
from pathlib import Path

from dce import __version__

ROOT = Path(__file__).resolve().parents[2]


def test_version_matches_pyproject() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert __version__ == data["project"]["version"] == "1.16.0"
    assert "Development Status :: 5 - Production/Stable" in data["project"]["classifiers"]


def test_release_checklist_exists() -> None:
    assert (ROOT / "docs" / "ReleaseChecklist-1.0.md").is_file()
    assert (ROOT / "scripts" / "publish.sh").is_file()
