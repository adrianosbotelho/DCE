"""Structured MCP response wrappers (schema_versioned)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from dce.domain.models import Document, ScoredDocument, WorkspaceFacets
from dce.interfaces.mcp.contract import MCP_SCHEMA_VERSION, PRIMARY_TOOL, STABLE_TOOLS

if TYPE_CHECKING:
    from dce.infrastructure.storage.workspace import DoctorReport


class SearchContextResult(BaseModel):
    """Result of ``search_context``."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = MCP_SCHEMA_VERSION
    documents: list[ScoredDocument] = Field(default_factory=list)


class ListFacetsResult(BaseModel):
    """Result of ``list_facets``."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = MCP_SCHEMA_VERSION
    facets: WorkspaceFacets = Field(default_factory=WorkspaceFacets)


class StatusCheck(BaseModel):
    """One doctor / workspace_status check row."""

    model_config = ConfigDict(extra="forbid")

    name: str
    ok: bool
    detail: str


class McpToolInfo(BaseModel):
    """Stable MCP tool inventory for agents."""

    model_config = ConfigDict(extra="forbid")

    primary_tool: str
    stable_tools: list[str] = Field(default_factory=list)


class WorkspaceStatusResult(BaseModel):
    """Result of ``workspace_status`` (aligned with ``dce doctor --json``)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = MCP_SCHEMA_VERSION
    healthy: bool
    workspace_root: str
    checks: list[StatusCheck] = Field(default_factory=list)
    mcp: McpToolInfo
    document_count: int = 0
    counts_by_source: dict[str, int] = Field(default_factory=dict)
    newest_indexed_at: str | None = None

    @classmethod
    def from_doctor_report(cls, report: DoctorReport) -> WorkspaceStatusResult:
        """Build status payload from a ``doctor_workspace`` report."""
        return cls(
            healthy=report.healthy,
            workspace_root=str(report.workspace_root),
            checks=[
                StatusCheck(name=check.name, ok=check.ok, detail=check.detail)
                for check in report.checks
            ],
            mcp=McpToolInfo(
                primary_tool=PRIMARY_TOOL,
                stable_tools=sorted(STABLE_TOOLS),
            ),
            document_count=report.document_count,
            counts_by_source=dict(report.counts_by_source),
            newest_indexed_at=report.newest_indexed_at,
        )


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
