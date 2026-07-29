"""Structured MCP response wrappers (schema_versioned)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from dce.domain.models import Document, ScoredDocument
from dce.interfaces.mcp.contract import MCP_SCHEMA_VERSION


class SearchContextResult(BaseModel):
    """Result of ``search_context``."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = MCP_SCHEMA_VERSION
    documents: list[ScoredDocument] = Field(default_factory=list)


class GetDocumentResult(BaseModel):
    """Result of ``get_document``."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = MCP_SCHEMA_VERSION
    found: bool
    document: Document | None = None


class RecentDocumentsResult(BaseModel):
    """Result of ``recent_documents``."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = MCP_SCHEMA_VERSION
    documents: list[Document] = Field(default_factory=list)
