"""Packaging metadata for git cut-release."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_cut_release_script_exists_and_is_executable() -> None:
    path = ROOT / "scripts" / "cut_release.sh"
    assert path.is_file()
    assert path.stat().st_mode & 0o111


def test_cut_release_script_guards() -> None:
    text = (ROOT / "scripts" / "cut_release.sh").read_text(encoding="utf-8")
    assert "pyproject.toml" in text
    assert "__version__" in text
    assert "Working tree is dirty" in text
    assert "--push" in text
    assert 'TAG="v${VERSION}"' in text


def test_release_git_doc_exists() -> None:
    text = (ROOT / "docs" / "ReleaseGit.md").read_text(encoding="utf-8")
    assert "cut_release.sh" in text
    assert "vX.Y.Z" in text
