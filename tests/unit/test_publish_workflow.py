"""Publish workflow uses Trusted Publisher (OIDC)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_publish_workflow_uses_trusted_publisher() -> None:
    text = (ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
    assert "pypa/gh-action-pypi-publish" in text
    assert "id-token: write" in text
    assert "environment: pypi" in text
    assert "workflow_dispatch" in text


def test_release_verify_doc() -> None:
    text = (ROOT / "docs" / "ReleaseVerify.md").read_text(encoding="utf-8")
    assert "Trusted Publisher" in text
    assert "Windows Portable" in text
    assert "adrianosbotelho/DCE" in text
