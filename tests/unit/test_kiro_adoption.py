"""Packaging / docs for Kiro adoption (Sprint 33)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_kiro_doc_exists() -> None:
    text = (ROOT / "docs" / "Kiro.md").read_text(encoding="utf-8")
    assert "build_context" in text
    assert "mcpServers" in text
    assert "dce doctor" in text


def test_bootstrap_github_script() -> None:
    path = ROOT / "scripts" / "bootstrap_github.sh"
    assert path.is_file()
    assert path.stat().st_mode & 0o111
    text = path.read_text(encoding="utf-8")
    assert "gh repo create" in text
    assert "cut_release" in text or "Missing tag" in text
