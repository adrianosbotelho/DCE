"""Canonical domain models for indexed documents and context packages."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

SCHEMA_VERSION = "1"


class SourceType(StrEnum):
    """Known source types. Open for extension via plain strings in Document."""

    MARKDOWN = "markdown"
    JIRA = "jira"
    GIT = "git"
    ADR = "adr"
    SNIPPET = "snippet"
    PROCEDURE = "procedure"
    INCIDENT = "incident"
    MEMORY = "memory"


class RetrievalMode(StrEnum):
    """Retrieval bias for the Context Builder (v1 uses balanced)."""

    BALANCED = "balanced"
    PRECISION = "precision"
    RECALL = "recall"


class Document(BaseModel):
    """Canonical indexed unit shared by all indexers."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    uri: str = Field(min_length=1)
    title: str = ""
    body: str = ""
    summary: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    project: str | None = None
    component: str | None = None
    technology: str | None = None
    related_uris: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    indexed_at: datetime | None = None

    @field_validator("tags", "related_uris", mode="before")
    @classmethod
    def _coerce_none_list(cls, value: Any) -> Any:
        return [] if value is None else value

    @field_validator("id", "source_type", "uri")
    @classmethod
    def _strip_required(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            msg = "id, source_type, and uri must be non-empty"
            raise ValueError(msg)
        return stripped


class SearchFilters(BaseModel):
    """Optional filters applied with FTS search / recent listing."""

    model_config = ConfigDict(extra="forbid")

    project: str | None = None
    component: str | None = None
    technology: str | None = None
    tags: list[str] = Field(default_factory=list)
    source_types: list[str] = Field(default_factory=list)


class SearchSpec(BaseModel):
    """Specification for a repository search."""

    model_config = ConfigDict(extra="forbid")

    text: str = ""
    filters: SearchFilters = Field(default_factory=SearchFilters)
    limit: int = Field(default=20, ge=1, le=500)


class ScoredDocument(BaseModel):
    """Document paired with a retrieval score (higher is better)."""

    model_config = ConfigDict(extra="forbid")

    document: Document
    score: float = 0.0


class ContextBudget(BaseModel):
    """Hard limits so context packages fit agent windows."""

    model_config = ConfigDict(extra="forbid")

    max_documents: int = Field(default=20, ge=0)
    max_chars: int = Field(default=24_000, ge=0)
    max_per_source: int = Field(default=5, ge=0)


class ContextQuery(BaseModel):
    """Input to the Context Builder."""

    model_config = ConfigDict(extra="forbid")

    text: str = ""
    anchors: list[str] = Field(default_factory=list)
    filters: SearchFilters = Field(default_factory=SearchFilters)
    budget: ContextBudget = Field(default_factory=ContextBudget)
    mode: RetrievalMode = RetrievalMode.BALANCED


class ContextSection(BaseModel):
    """Semantic grouping inside a context package."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    document_ids: list[str] = Field(default_factory=list)
    rationale: str = ""


class RetrievalDiagnostics(BaseModel):
    """Transparency for agents and operators."""

    model_config = ConfigDict(extra="forbid")

    elapsed_ms: float = 0.0
    hits_by_source: dict[str, int] = Field(default_factory=dict)
    truncated: bool = False
    notes: list[str] = Field(default_factory=list)
    query_kind: str | None = None
    preferred_sources: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    synonym_expansions: dict[str, list[str]] = Field(default_factory=dict)


class ContextPackage(BaseModel):
    """Structured context delivered to Kiro (and CLI)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = SCHEMA_VERSION
    query: ContextQuery
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    sections: list[ContextSection] = Field(default_factory=list)
    documents: list[ScoredDocument] = Field(default_factory=list)
    diagnostics: RetrievalDiagnostics = Field(default_factory=RetrievalDiagnostics)


def document_char_size(document: Document) -> int:
    """Approximate character weight used by budget trimming."""
    return len(document.title) + len(document.body) + len(document.summary)


def apply_budget(
    scored: list[ScoredDocument],
    budget: ContextBudget,
) -> tuple[list[ScoredDocument], bool]:
    """Trim scored documents to fit budget.

    Preserves input order (caller ranks first). Returns (kept, truncated).
    """
    if budget.max_documents == 0:
        return [], bool(scored)

    kept: list[ScoredDocument] = []
    per_source: dict[str, int] = {}
    chars = 0
    truncated = False

    for item in scored:
        if len(kept) >= budget.max_documents:
            truncated = True
            break

        source = item.document.source_type
        source_count = per_source.get(source, 0)
        if budget.max_per_source and source_count >= budget.max_per_source:
            truncated = True
            continue

        weight = document_char_size(item.document)
        if budget.max_chars and chars + weight > budget.max_chars:
            truncated = True
            continue

        kept.append(item)
        per_source[source] = source_count + 1
        chars += weight

    if len(kept) < len(scored):
        truncated = True

    return kept, truncated
