"""Anchor detection and retrieval planning for the Context Builder."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum

from dce.application.anchors import (
    AnchorKind,
    AnchorPattern,
    DetectedAnchor,
    classify_from_anchors,
    default_anchor_patterns,
    detect_anchors_with_patterns,
    normalize_anchor_value,
)
from dce.application.synonyms import (
    collect_expansion_terms,
    default_synonym_dictionary,
    expand_synonyms,
)
from dce.domain.models import ContextQuery, SearchFilters

_ARCH_RE = re.compile(
    r"\b(adr|arquitetur|architecture|trade-?off|por que usamos|why (?:did|do) we|"
    r"decis[aã]o arquitet|design decision)\b",
    re.IGNORECASE,
)


class QueryKind(StrEnum):
    """Coarse query classes used by the retrieval planner."""

    ERROR_CODE = "error_code"
    ISSUE = "issue"
    ARCHITECTURE = "architecture"
    PATH = "path"
    GENERAL = "general"


PREFERRED_SOURCES: dict[QueryKind, tuple[str, ...]] = {
    QueryKind.ERROR_CODE: (
        "jira",
        "incident",
        "procedure",
        "snippet",
        "markdown",
        "memory",
        "git",
    ),
    QueryKind.ISSUE: ("jira", "git", "incident", "markdown", "memory", "procedure"),
    QueryKind.ARCHITECTURE: ("adr", "markdown", "memory"),
    QueryKind.PATH: ("git", "markdown", "snippet", "adr"),
    QueryKind.GENERAL: (),
}


@dataclass(frozen=True)
class RetrievalStep:
    """One repository search issued by the planner."""

    text: str
    filters: SearchFilters
    limit: int
    label: str


@dataclass
class RetrievalPlan:
    """Ordered retrieval steps plus planner notes."""

    steps: list[RetrievalStep] = field(default_factory=list)
    anchors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    query_kind: QueryKind = QueryKind.GENERAL
    preferred_sources: list[str] = field(default_factory=list)
    synonym_expansions: dict[str, list[str]] = field(default_factory=dict)


def _to_query_kind(kind: AnchorKind | QueryKind | None) -> QueryKind | None:
    if kind is None:
        return None
    if isinstance(kind, QueryKind):
        return kind
    try:
        return QueryKind(kind.value)
    except ValueError:
        return QueryKind.GENERAL


def detect_anchors(
    text: str,
    *,
    patterns: Sequence[AnchorPattern] | None = None,
) -> list[str]:
    """Extract strong identifiers from free text (issue keys, ORA codes, paths, extras)."""
    resolved = default_anchor_patterns() if patterns is None else list(patterns)
    return [item.value for item in detect_anchors_with_patterns(text, resolved)]


def _canonicalize_explicit(
    anchor: str,
    patterns: Sequence[AnchorPattern],
) -> DetectedAnchor | None:
    stripped = anchor.strip()
    if not stripped:
        return None
    for pattern in patterns:
        match = pattern.pattern.fullmatch(stripped) or pattern.pattern.fullmatch(stripped.upper())
        if match:
            raw = match.group(1) if match.lastindex else match.group(0)
            value = normalize_anchor_value(str(raw).strip(), pattern.case)
            if value:
                return DetectedAnchor(
                    value=value,
                    kind=pattern.kind,
                    pattern_name=pattern.name,
                )
    return DetectedAnchor(
        value=stripped,
        kind=AnchorKind.GENERAL,
        pattern_name="explicit",
    )


def merge_anchors(
    query: ContextQuery,
    *,
    patterns: Sequence[AnchorPattern] | None = None,
) -> list[str]:
    """Combine explicit anchors with anchors detected in query text."""
    return [item.value for item in merge_detected_anchors(query, patterns=patterns)]


def merge_detected_anchors(
    query: ContextQuery,
    *,
    patterns: Sequence[AnchorPattern] | None = None,
) -> list[DetectedAnchor]:
    """Combine explicit + detected anchors with kinds and dedupe."""
    resolved = default_anchor_patterns() if patterns is None else list(patterns)
    merged: list[DetectedAnchor] = []
    seen: set[str] = set()

    for raw in query.anchors:
        item = _canonicalize_explicit(raw, resolved)
        if item is None:
            continue
        key = item.value.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)

    for item in detect_anchors_with_patterns(query.text, resolved):
        key = item.value.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged


def classify_query(
    query: ContextQuery,
    anchors: list[str] | None = None,
    *,
    patterns: Sequence[AnchorPattern] | None = None,
    detected: Sequence[DetectedAnchor] | None = None,
) -> QueryKind:
    """Classify a query into a coarse retrieval kind (rules only)."""
    resolved_patterns = default_anchor_patterns() if patterns is None else list(patterns)
    if detected is not None:
        resolved_detected = list(detected)
    elif anchors is not None:
        resolved_detected = []
        for raw in anchors:
            item = _canonicalize_explicit(raw, resolved_patterns)
            if item is not None:
                resolved_detected.append(item)
    else:
        resolved_detected = merge_detected_anchors(query, patterns=resolved_patterns)

    from_anchors = _to_query_kind(classify_from_anchors(resolved_detected))
    if from_anchors is not None:
        return from_anchors

    text = query.text.strip()
    if text and _ARCH_RE.search(text):
        return QueryKind.ARCHITECTURE
    return QueryKind.GENERAL


def _with_source(filters: SearchFilters, source_type: str) -> SearchFilters:
    return SearchFilters(
        project=filters.project,
        component=filters.component,
        technology=filters.technology,
        tags=list(filters.tags),
        source_types=[source_type],
    )


def plan_retrieval(
    query: ContextQuery,
    *,
    synonym_dictionary: Mapping[str, Sequence[str]] | None = None,
    anchor_patterns: Sequence[AnchorPattern] | None = None,
) -> RetrievalPlan:
    """Build a multi-step retrieval plan biased by query kind and synonyms."""
    patterns = default_anchor_patterns() if anchor_patterns is None else list(anchor_patterns)
    detected = merge_detected_anchors(query, patterns=patterns)
    anchors = [item.value for item in detected]
    kind = classify_query(query, detected=detected, patterns=patterns)
    notes: list[str] = [f"query_kind={kind.value}"]
    steps: list[RetrievalStep] = []

    limit = query.budget.max_documents or 20
    limit = max(1, min(limit, 100))
    filters = query.filters
    user_locked_sources = bool(filters.source_types)
    preferred = list(PREFERRED_SOURCES.get(kind, ()))
    if user_locked_sources:
        preferred = []
        notes.append("respecting user source_types filter")
    elif preferred:
        notes.append("preferred sources: " + ", ".join(preferred))

    extra_names = [
        pattern.name for pattern in patterns if pattern.name not in {"issue", "ora", "path"}
    ]
    if extra_names:
        notes.append("custom anchor patterns: " + ", ".join(extra_names))

    dictionary = (
        default_synonym_dictionary(synonym_dictionary)
        if synonym_dictionary is not None
        else default_synonym_dictionary()
    )
    expansion_terms = collect_expansion_terms(query.text, anchors)
    expansions = expand_synonyms(expansion_terms, dictionary)
    if expansions:
        notes.append(
            "synonym expansions: "
            + ", ".join(f"{term}->{'|'.join(syns)}" for term, syns in expansions.items())
        )

    primary_text = anchors[0] if anchors else query.text.strip()

    for anchor in anchors:
        steps.append(
            RetrievalStep(
                text=anchor,
                filters=filters,
                limit=min(10, limit),
                label=f"anchor:{anchor}",
            )
        )
        notes.append(f"anchor search for {anchor}")

    if preferred and primary_text:
        for source in preferred[:4]:
            steps.append(
                RetrievalStep(
                    text=primary_text,
                    filters=_with_source(filters, source),
                    limit=min(5, limit),
                    label=f"preferred:{source}",
                )
            )

    for term, syns in expansions.items():
        for synonym in syns:
            steps.append(
                RetrievalStep(
                    text=synonym,
                    filters=filters,
                    limit=min(5, limit),
                    label=f"synonym:{term}->{synonym}",
                )
            )

    text = query.text.strip()
    if text:
        steps.append(
            RetrievalStep(
                text=text,
                filters=filters,
                limit=limit,
                label="full_text",
            )
        )
        notes.append("full-text search")
    elif not anchors:
        steps.append(
            RetrievalStep(
                text="",
                filters=filters,
                limit=limit,
                label="recent_fallback",
            )
        )
        notes.append("empty query — recent documents fallback")

    return RetrievalPlan(
        steps=steps,
        anchors=anchors,
        notes=notes,
        query_kind=kind,
        preferred_sources=preferred,
        synonym_expansions=expansions,
    )
