"""Context Builder use case — product core."""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence

from dce.application.anchors import AnchorPattern
from dce.application.assembler import assemble_package
from dce.application.planner import plan_retrieval
from dce.domain.models import ContextPackage, ContextQuery, SearchSpec
from dce.domain.ports import DocumentRepository


def build_context(
    repository: DocumentRepository,
    query: ContextQuery,
    *,
    synonym_dictionary: Mapping[str, Sequence[str]] | None = None,
    anchor_patterns: Sequence[AnchorPattern] | None = None,
) -> ContextPackage:
    """Plan retrieval, search, assemble a structured ContextPackage."""
    started = time.perf_counter()
    plan = plan_retrieval(
        query,
        synonym_dictionary=synonym_dictionary,
        anchor_patterns=anchor_patterns,
    )

    hits = []
    for step in plan.steps:
        hits.extend(
            repository.search(
                SearchSpec(
                    text=step.text,
                    filters=step.filters,
                    limit=step.limit,
                )
            )
        )

    elapsed_ms = (time.perf_counter() - started) * 1000.0
    return assemble_package(
        hits,
        query,
        anchors=plan.anchors,
        planner_notes=plan.notes,
        elapsed_ms=elapsed_ms,
        preferred_sources=plan.preferred_sources,
        query_kind=plan.query_kind,
        steps=[step.label for step in plan.steps],
        synonym_expansions=plan.synonym_expansions,
    )
