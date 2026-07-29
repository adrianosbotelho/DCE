"""Packaging metadata for Windows portable distribution."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_windows_portable_packaging_files_exist() -> None:
    assert (ROOT / "packaging" / "pyinstaller" / "dce.spec").is_file()
    assert (ROOT / "packaging" / "pyinstaller" / "run_dce.py").is_file()
    assert (ROOT / "scripts" / "build_windows_portable.ps1").is_file()
    assert (ROOT / ".github" / "workflows" / "windows-portable.yml").is_file()
    assert (ROOT / "docs" / "Windows.md").is_file()
    assert (ROOT / "docs" / "ReleaseWindows.md").is_file()


def test_windows_doc_mentions_kiro_and_zip() -> None:
    text = (ROOT / "docs" / "Windows.md").read_text(encoding="utf-8")
    assert "dce.exe" in text
    assert "windows-x64.zip" in text
    assert "mcp" in text.lower()
    assert "SmartScreen" in text
    assert "sha256" in text.lower()


def test_windows_workflow_publishes_release_on_tags() -> None:
    text = (ROOT / ".github" / "workflows" / "windows-portable.yml").read_text(
        encoding="utf-8"
    )
    assert "softprops/action-gh-release" in text
    assert "refs/tags/" in text
    assert ".sha256" in text
    ps1 = (ROOT / "scripts" / "build_windows_portable.ps1").read_text(encoding="utf-8")
    assert "Get-FileHash" in ps1
    assert "SHA256" in ps1
