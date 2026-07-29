"""Unit tests for MCP contract constants."""

from __future__ import annotations

from dce.domain.models import SCHEMA_VERSION
from dce.interfaces.mcp.contract import (
    DIAGNOSTICS_KEYS,
    MCP_SCHEMA_VERSION,
    PRIMARY_TOOL,
    STABLE_TOOLS,
)


def test_schema_version_aligned() -> None:
    assert MCP_SCHEMA_VERSION == SCHEMA_VERSION == "1"


def test_stable_tools_freeze() -> None:
    assert {
        "build_context",
        "search_context",
        "get_document",
        "recent_documents",
        "search_memory",
        "search_by_issue",
        "search_by_project",
        "search_by_component",
        "search_by_technology",
    } == STABLE_TOOLS
    assert PRIMARY_TOOL == "build_context"
    assert "query_kind" in DIAGNOSTICS_KEYS
    assert "synonym_expansions" in DIAGNOSTICS_KEYS
