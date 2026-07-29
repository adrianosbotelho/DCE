"""Unit tests for MCP issue-key helper."""

from __future__ import annotations

from dce.interfaces.mcp.server import normalize_issue_key


def test_normalize_issue_key() -> None:
    assert normalize_issue_key("pay-12") == "PAY-12"
    assert normalize_issue_key("issue:pay-12") == "PAY-12"
    assert normalize_issue_key("  ISSUE:ABC-9  ") == "ABC-9"
    assert normalize_issue_key("") == ""
