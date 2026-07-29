"""MCP server factory optimized for Kiro (stdio)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

from dce import __version__
from dce.application.build_context import build_context as build_context_uc
from dce.domain.models import (
    ContextBudget,
    ContextPackage,
    ContextQuery,
    SearchFilters,
    SearchSpec,
)
from dce.infrastructure.storage.connection import connect
from dce.infrastructure.storage.repository import SqliteDocumentRepository
from dce.infrastructure.storage.workspace import (
    anchor_patterns_from_config,
    budget_from_config,
    load_workspace,
    synonyms_from_config,
)
from dce.interfaces.mcp.schemas import (
    GetDocumentResult,
    RecentDocumentsResult,
    SearchContextResult,
)


def normalize_issue_key(raw: str) -> str:
    """Normalize ``PAY-12`` / ``issue:pay-12`` into canonical uppercase key."""
    key = raw.strip()
    if key.lower().startswith("issue:"):
        key = key.split(":", 1)[1].strip()
    return key.upper()


def normalize_project_slug(raw: str) -> str:
    """Normalize ``payments`` / ``project:payments`` into a project filter slug."""
    value = raw.strip()
    if value.lower().startswith("project:"):
        value = value.split(":", 1)[1].strip()
    return value


def normalize_component_slug(raw: str) -> str:
    """Normalize ``listener`` / ``component:listener`` into a component filter slug."""
    value = raw.strip()
    if value.lower().startswith("component:"):
        value = value.split(":", 1)[1].strip()
    return value


def normalize_technology_slug(raw: str) -> str:
    """Normalize ``oracle`` / ``technology:oracle`` into a technology filter slug."""
    value = raw.strip()
    if value.lower().startswith("technology:"):
        value = value.split(":", 1)[1].strip()
    return value


def _merge_budget(
    base: ContextBudget,
    *,
    max_documents: int | None,
    max_chars: int | None,
    max_per_source: int | None,
) -> ContextBudget:
    return ContextBudget(
        max_documents=base.max_documents if max_documents is None else max_documents,
        max_chars=base.max_chars if max_chars is None else max_chars,
        max_per_source=base.max_per_source if max_per_source is None else max_per_source,
    )


def create_mcp_server(workspace_path: Path) -> MCPServer:
    """Create an MCP server bound to a DCE workspace."""
    root, config, database_path = load_workspace(workspace_path)
    default_budget = budget_from_config(config)
    synonym_dictionary = synonyms_from_config(config)
    anchor_patterns = anchor_patterns_from_config(config)
    raw_workspace = config.get("workspace")
    workspace_cfg: dict[str, Any] = raw_workspace if isinstance(raw_workspace, dict) else {}
    workspace_name = str(workspace_cfg.get("name") or root.name)

    server = MCPServer(
        name="dce",
        title="Dev Context Engine",
        description=(
            "Offline context builder for AI coding agents. "
            "Prefer build_context to assemble a structured ContextPackage. "
            f"Workspace: {workspace_name}."
        ),
        version=__version__,
        instructions=(
            "Use build_context for development questions. "
            "Use search_context for raw ranked hits. "
            "Use search_memory for curated local memory notes only. "
            "Use search_by_issue for Jira-like keys (PAY-123). "
            "Use search_by_project to scope hits to one project slug. "
            "Use search_by_component to scope hits to one component slug. "
            "Use search_by_technology to scope hits to one technology slug. "
            "Use get_document / recent_documents for direct lookups. "
            "All responses are structured JSON with schema_version."
        ),
    )

    def _filters(
        *,
        project: str | None,
        component: str | None,
        technology: str | None,
        tags: list[str] | None,
        source_types: list[str] | None,
    ) -> SearchFilters:
        return SearchFilters(
            project=project,
            component=component,
            technology=technology,
            tags=list(tags or []),
            source_types=list(source_types or []),
        )

    @server.tool()
    def build_context(
        text: str,
        anchors: list[str] | None = None,
        project: str | None = None,
        component: str | None = None,
        technology: str | None = None,
        tags: list[str] | None = None,
        source_types: list[str] | None = None,
        max_documents: int | None = None,
        max_chars: int | None = None,
        max_per_source: int | None = None,
    ) -> ContextPackage:
        """Build a structured ContextPackage from corporate knowledge.

        This is the primary DCE tool. Prefer it over raw search when answering
        development questions (bugs, procedures, ADRs, similar incidents).
        """
        query = ContextQuery(
            text=text,
            anchors=list(anchors or []),
            filters=_filters(
                project=project,
                component=component,
                technology=technology,
                tags=tags,
                source_types=source_types,
            ),
            budget=_merge_budget(
                default_budget,
                max_documents=max_documents,
                max_chars=max_chars,
                max_per_source=max_per_source,
            ),
        )
        with connect(database_path) as conn:
            repository = SqliteDocumentRepository(conn)
            return build_context_uc(
                repository,
                query,
                synonym_dictionary=synonym_dictionary,
                anchor_patterns=anchor_patterns,
            )

    @server.tool()
    def search_context(
        text: str = "",
        limit: int = 20,
        project: str | None = None,
        component: str | None = None,
        technology: str | None = None,
        tags: list[str] | None = None,
        source_types: list[str] | None = None,
    ) -> SearchContextResult:
        """Full-text search returning ranked documents (primitive; prefer build_context)."""
        spec = SearchSpec(
            text=text,
            filters=_filters(
                project=project,
                component=component,
                technology=technology,
                tags=tags,
                source_types=source_types,
            ),
            limit=max(1, min(limit, 500)),
        )
        with connect(database_path) as conn:
            repository = SqliteDocumentRepository(conn)
            hits = repository.search(spec)
        return SearchContextResult(documents=hits)

    @server.tool()
    def search_memory(
        text: str = "",
        limit: int = 20,
        project: str | None = None,
        component: str | None = None,
        technology: str | None = None,
        tags: list[str] | None = None,
    ) -> SearchContextResult:
        """Search curated local memory notes (source_type=memory only).

        Convenience alias over search_context with source_types fixed to memory.
        Prefer build_context for broader development questions.
        """
        spec = SearchSpec(
            text=text,
            filters=_filters(
                project=project,
                component=component,
                technology=technology,
                tags=tags,
                source_types=["memory"],
            ),
            limit=max(1, min(limit, 500)),
        )
        with connect(database_path) as conn:
            repository = SqliteDocumentRepository(conn)
            hits = repository.search(spec)
        return SearchContextResult(documents=hits)

    @server.tool()
    def search_by_issue(
        issue_key: str,
        limit: int = 20,
        project: str | None = None,
        component: str | None = None,
        technology: str | None = None,
        source_types: list[str] | None = None,
    ) -> SearchContextResult:
        """Search documents related to a Jira-like issue key (e.g. PAY-125).

        Convenience alias over search_context with the key normalized and used as
        the FTS query. Prefer build_context for broader development questions.
        """
        key = normalize_issue_key(issue_key)
        if not key:
            return SearchContextResult(documents=[])
        spec = SearchSpec(
            text=key,
            filters=_filters(
                project=project,
                component=component,
                technology=technology,
                tags=None,
                source_types=source_types,
            ),
            limit=max(1, min(limit, 500)),
        )
        with connect(database_path) as conn:
            repository = SqliteDocumentRepository(conn)
            hits = repository.search(spec)
        return SearchContextResult(documents=hits)

    @server.tool()
    def search_by_project(
        project: str,
        text: str = "",
        limit: int = 20,
        component: str | None = None,
        technology: str | None = None,
        tags: list[str] | None = None,
        source_types: list[str] | None = None,
    ) -> SearchContextResult:
        """Search documents scoped to a single project slug (e.g. payments).

        Convenience alias over search_context with filters.project set.
        Prefer build_context for broader development questions.
        """
        slug = normalize_project_slug(project)
        if not slug:
            return SearchContextResult(documents=[])
        spec = SearchSpec(
            text=text,
            filters=_filters(
                project=slug,
                component=component,
                technology=technology,
                tags=tags,
                source_types=source_types,
            ),
            limit=max(1, min(limit, 500)),
        )
        with connect(database_path) as conn:
            repository = SqliteDocumentRepository(conn)
            hits = repository.search(spec)
        return SearchContextResult(documents=hits)

    @server.tool()
    def search_by_component(
        component: str,
        text: str = "",
        limit: int = 20,
        project: str | None = None,
        technology: str | None = None,
        tags: list[str] | None = None,
        source_types: list[str] | None = None,
    ) -> SearchContextResult:
        """Search documents scoped to a single component slug (e.g. listener).

        Convenience alias over search_context with filters.component set.
        Prefer build_context for broader development questions.
        """
        slug = normalize_component_slug(component)
        if not slug:
            return SearchContextResult(documents=[])
        spec = SearchSpec(
            text=text,
            filters=_filters(
                project=project,
                component=slug,
                technology=technology,
                tags=tags,
                source_types=source_types,
            ),
            limit=max(1, min(limit, 500)),
        )
        with connect(database_path) as conn:
            repository = SqliteDocumentRepository(conn)
            hits = repository.search(spec)
        return SearchContextResult(documents=hits)

    @server.tool()
    def search_by_technology(
        technology: str,
        text: str = "",
        limit: int = 20,
        project: str | None = None,
        component: str | None = None,
        tags: list[str] | None = None,
        source_types: list[str] | None = None,
    ) -> SearchContextResult:
        """Search documents scoped to a single technology slug (e.g. oracle).

        Convenience alias over search_context with filters.technology set.
        Prefer build_context for broader development questions.
        """
        slug = normalize_technology_slug(technology)
        if not slug:
            return SearchContextResult(documents=[])
        spec = SearchSpec(
            text=text,
            filters=_filters(
                project=project,
                component=component,
                technology=slug,
                tags=tags,
                source_types=source_types,
            ),
            limit=max(1, min(limit, 500)),
        )
        with connect(database_path) as conn:
            repository = SqliteDocumentRepository(conn)
            hits = repository.search(spec)
        return SearchContextResult(documents=hits)

    @server.tool()
    def get_document(document_id: str) -> GetDocumentResult:
        """Fetch a single document by id."""
        with connect(database_path) as conn:
            repository = SqliteDocumentRepository(conn)
            document = repository.get(document_id)
        if document is None:
            return GetDocumentResult(found=False, document=None)
        return GetDocumentResult(found=True, document=document)

    @server.tool()
    def recent_documents(
        limit: int = 20,
        project: str | None = None,
        component: str | None = None,
        technology: str | None = None,
        tags: list[str] | None = None,
        source_types: list[str] | None = None,
    ) -> RecentDocumentsResult:
        """List newest indexed documents."""
        filters = _filters(
            project=project,
            component=component,
            technology=technology,
            tags=tags,
            source_types=source_types,
        )
        with connect(database_path) as conn:
            repository = SqliteDocumentRepository(conn)
            documents = repository.list_recent(limit=max(1, min(limit, 500)), filters=filters)
        return RecentDocumentsResult(documents=documents)

    return server


def run_mcp_stdio(workspace_path: Path) -> None:  # pragma: no cover
    """Run the MCP server over stdio (blocking)."""
    server = create_mcp_server(workspace_path)
    server.run(transport="stdio")
