"""Assemble ranked context packages from raw retrieval hits."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from dce.application.planner import QueryKind
from dce.domain.models import (
    ContextPackage,
    ContextQuery,
    ContextSection,
    Document,
    RetrievalDiagnostics,
    ScoredDocument,
    apply_budget,
)

_SECTION_BY_SOURCE: dict[str, str] = {
    "jira": "issues",
    "adr": "adrs",
    "git": "commits",
    "memory": "memory",
    "markdown": "documentation",
    "incident": "incidents",
    "procedure": "procedures",
    "snippet": "snippets",
}

_SECTION_BY_KIND: dict[tuple[QueryKind, str], str] = {
    (QueryKind.ERROR_CODE, "jira"): "similar_bugs",
    (QueryKind.ERROR_CODE, "incident"): "incidents",
    (QueryKind.ERROR_CODE, "procedure"): "procedures",
    (QueryKind.ISSUE, "jira"): "related_issues",
    (QueryKind.ISSUE, "git"): "related_commits",
    (QueryKind.ARCHITECTURE, "adr"): "adrs",
    (QueryKind.PATH, "git"): "related_commits",
}


def _document_timestamp(document: Document) -> datetime | None:
    return document.updated_at or document.indexed_at or document.created_at


def freshness_boost(document: Document, *, now: datetime | None = None) -> float:
    """Return a small freshness bonus (0..2) based on document age."""
    stamp = _document_timestamp(document)
    if stamp is None:
        return 0.0
    current = now or datetime.now(UTC)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)
    age_days = max(0.0, (current - stamp.astimezone(UTC)).total_seconds() / 86400.0)
    # ~2.0 for brand new, ~0 after ~365 days.
    return max(0.0, 2.0 * (1.0 - min(age_days, 365.0) / 365.0))


def apply_ranking_boosts(
    item: ScoredDocument,
    *,
    anchors: list[str],
    preferred_sources: list[str],
    now: datetime | None = None,
) -> ScoredDocument:
    """Apply lexical/metadata boosts on top of the repository score."""
    score = item.score
    document = item.document
    title = document.title.lower()
    body = document.body.lower()
    summary = document.summary.lower()
    tags = {tag.lower() for tag in document.tags}

    for anchor in anchors:
        needle = anchor.lower()
        if title == needle or title.startswith(f"{needle} ") or title.startswith(f"{needle}:"):
            score += 6.0
        elif needle in title:
            score += 5.0
        elif needle in tags:
            score += 4.0
        elif needle in summary:
            score += 3.0
        elif needle in body:
            score += 2.0

    if preferred_sources and document.source_type in preferred_sources:
        # Stronger boost for earlier preferred sources.
        rank = preferred_sources.index(document.source_type)
        score += max(0.5, 2.0 - (0.35 * rank))

    score += freshness_boost(document, now=now)
    return ScoredDocument(document=document, score=score)


def dedupe_keep_best(items: list[ScoredDocument]) -> list[ScoredDocument]:
    """Keep the highest-scoring instance of each document id."""
    best: dict[str, ScoredDocument] = {}
    for item in items:
        current = best.get(item.document.id)
        if current is None or item.score > current.score:
            best[item.document.id] = item
    return list(best.values())


def section_name_for(source_type: str, query_kind: QueryKind) -> str:
    """Map source_type (+ query kind) to a semantic section name."""
    kind_name = _SECTION_BY_KIND.get((query_kind, source_type))
    if kind_name is not None:
        return kind_name
    return _SECTION_BY_SOURCE.get(source_type, source_type)


def build_sections(
    documents: list[ScoredDocument],
    *,
    query_kind: QueryKind = QueryKind.GENERAL,
) -> list[ContextSection]:
    """Group document ids into semantic sections."""
    grouped: dict[str, list[str]] = defaultdict(list)
    for item in documents:
        name = section_name_for(item.document.source_type, query_kind)
        grouped[name].append(item.document.id)
    sections: list[ContextSection] = []
    for name, ids in grouped.items():
        sections.append(
            ContextSection(
                name=name,
                document_ids=ids,
                rationale=f"Grouped as {name} for query_kind={query_kind.value}",
            )
        )
    return sections


def assemble_package(
    hits: list[ScoredDocument],
    query: ContextQuery,
    *,
    anchors: list[str],
    planner_notes: list[str],
    elapsed_ms: float,
    preferred_sources: list[str] | None = None,
    query_kind: QueryKind = QueryKind.GENERAL,
    now: datetime | None = None,
    steps: list[str] | None = None,
    synonym_expansions: dict[str, list[str]] | None = None,
) -> ContextPackage:
    """Dedupe, boost, rank, trim to budget, and build sections."""
    preferred = list(preferred_sources or [])
    boosted = [
        apply_ranking_boosts(
            item,
            anchors=anchors,
            preferred_sources=preferred,
            now=now,
        )
        for item in hits
    ]
    unique = dedupe_keep_best(boosted)
    ranked = sorted(unique, key=lambda item: item.score, reverse=True)
    kept, truncated = apply_budget(ranked, query.budget)

    hits_by_source: dict[str, int] = defaultdict(int)
    for item in kept:
        hits_by_source[item.document.source_type] += 1

    notes = list(planner_notes)
    if not kept:
        notes.append("no documents matched")
    if truncated:
        notes.append("package truncated by ContextBudget")

    return ContextPackage(
        query=query,
        sections=build_sections(kept, query_kind=query_kind),
        documents=kept,
        diagnostics=RetrievalDiagnostics(
            elapsed_ms=elapsed_ms,
            hits_by_source=dict(hits_by_source),
            truncated=truncated,
            notes=notes,
            query_kind=query_kind.value,
            preferred_sources=preferred,
            steps=list(steps or []),
            synonym_expansions=dict(synonym_expansions or {}),
        ),
    )
