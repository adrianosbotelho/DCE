"""Frozen MCP contract constants for Kiro (schema_version 1)."""

from __future__ import annotations

from typing import Final

from dce.domain.models import SCHEMA_VERSION

MCP_SCHEMA_VERSION: Final[str] = SCHEMA_VERSION

STABLE_TOOLS: Final[frozenset[str]] = frozenset(
    {
        "build_context",
        "search_context",
        "get_document",
        "recent_documents",
        "search_memory",
        "search_by_issue",
    }
)

PRIMARY_TOOL: Final[str] = "build_context"

# Additive diagnostics keys expected on ContextPackage.diagnostics (schema_version 1).
DIAGNOSTICS_KEYS: Final[frozenset[str]] = frozenset(
    {
        "elapsed_ms",
        "hits_by_source",
        "truncated",
        "notes",
        "query_kind",
        "preferred_sources",
        "steps",
        "synonym_expansions",
    }
)
