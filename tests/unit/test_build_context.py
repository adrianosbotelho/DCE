"""Unit tests for package assembler and build_context."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from dce.application.assembler import (
    apply_ranking_boosts,
    assemble_package,
    dedupe_keep_best,
    freshness_boost,
    section_name_for,
)
from dce.application.build_context import build_context
from dce.application.planner import QueryKind
from dce.domain.models import (
    ContextBudget,
    ContextQuery,
    Document,
    ScoredDocument,
    SearchFilters,
    SearchSpec,
)


def _doc(
    doc_id: str,
    *,
    source: str = "markdown",
    title: str = "",
    body: str = "",
    tags: list[str] | None = None,
    updated_at: datetime | None = None,
) -> Document:
    return Document(
        id=doc_id,
        source_type=source,
        uri=f"{doc_id}.md",
        title=title or doc_id,
        body=body or doc_id,
        tags=tags or [],
        updated_at=updated_at,
    )


def test_dedupe_keep_best() -> None:
    items = [
        ScoredDocument(document=_doc("a"), score=1.0),
        ScoredDocument(document=_doc("a", title="better"), score=5.0),
        ScoredDocument(document=_doc("b"), score=2.0),
    ]
    unique = dedupe_keep_best(items)
    by_id = {item.document.id: item for item in unique}
    assert by_id["a"].score == 5.0
    assert by_id["a"].document.title == "better"


def test_freshness_and_preferred_source_boosts() -> None:
    now = datetime(2026, 7, 29, tzinfo=UTC)
    fresh = ScoredDocument(
        document=_doc(
            "1",
            source="jira",
            title="ORA-12541 listener",
            tags=["ORA-12541"],
            updated_at=now,
        ),
        score=1.0,
    )
    stale = ScoredDocument(
        document=_doc(
            "2",
            source="markdown",
            title="Other",
            updated_at=now - timedelta(days=400),
        ),
        score=1.5,
    )
    assert freshness_boost(fresh.document, now=now) > freshness_boost(stale.document, now=now)
    boosted = apply_ranking_boosts(
        fresh,
        anchors=["ORA-12541"],
        preferred_sources=["jira", "markdown"],
        now=now,
    )
    assert boosted.score > fresh.score + 5.0


def test_assemble_boosts_anchor_and_sections() -> None:
    now = datetime(2026, 7, 29, tzinfo=UTC)
    hits = [
        ScoredDocument(
            document=_doc(
                "1",
                title="ORA-12541 listener",
                body="x" * 10,
                source="jira",
                updated_at=now,
            ),
            score=1.0,
        ),
        ScoredDocument(
            document=_doc("2", title="Other", body="y" * 10, source="adr", updated_at=now),
            score=1.5,
        ),
        ScoredDocument(
            document=_doc("3", title="Noise", body="z" * 10, updated_at=now),
            score=1.2,
        ),
    ]
    package = assemble_package(
        hits,
        ContextQuery(
            text="ORA-12541",
            budget=ContextBudget(max_documents=2, max_chars=100000, max_per_source=5),
        ),
        anchors=["ORA-12541"],
        planner_notes=["anchor search"],
        elapsed_ms=12.5,
        preferred_sources=["jira", "markdown"],
        query_kind=QueryKind.ERROR_CODE,
        now=now,
        steps=["anchor:ORA-12541", "synonym:ORA-12541->tns", "full_text"],
        synonym_expansions={"ORA-12541": ["tns", "listener"]},
    )
    assert len(package.documents) == 2
    assert package.documents[0].document.id == "1"
    assert package.documents[0].score > 1.0
    assert package.diagnostics.truncated is True
    assert package.diagnostics.query_kind == "error_code"
    assert package.diagnostics.preferred_sources == ["jira", "markdown"]
    assert package.diagnostics.steps[0] == "anchor:ORA-12541"
    assert package.diagnostics.synonym_expansions == {"ORA-12541": ["tns", "listener"]}
    assert "similar_bugs" in {section.name for section in package.sections}


def test_section_name_for_kind() -> None:
    assert section_name_for("jira", QueryKind.ERROR_CODE) == "similar_bugs"
    assert section_name_for("adr", QueryKind.GENERAL) == "adrs"


class FakeRepo:
    def __init__(self, hits: dict[str, list[ScoredDocument]]) -> None:
        self._hits = hits
        self.calls: list[SearchSpec] = []

    def upsert_many(self, documents: Sequence[Document]) -> int:
        return 0

    def get(self, document_id: str) -> Document | None:
        return None

    def search(self, spec: SearchSpec) -> list[ScoredDocument]:
        self.calls.append(spec)
        if spec.filters.source_types:
            source = spec.filters.source_types[0]
            keyed = self._hits.get(f"{spec.text}|{source}")
            if keyed is not None:
                return list(keyed)
        return list(self._hits.get(spec.text, self._hits.get("*", [])))

    def list_recent(
        self,
        limit: int = 20,
        filters: SearchFilters | None = None,
    ) -> list[Document]:
        return []


def test_build_context_end_to_end_with_fake_repo() -> None:
    hit = ScoredDocument(
        document=_doc("hit", title="ORA-12541", body="listener down", source="jira"),
        score=2.0,
    )
    repo = FakeRepo(
        {
            "ORA-12541": [hit],
            "problem ORA-12541": [hit],
            "ORA-12541|jira": [hit],
        }
    )

    package = build_context(
        repo,
        ContextQuery(text="problem ORA-12541", budget=ContextBudget(max_documents=5)),
    )
    assert package.schema_version == "1"
    assert len(package.documents) == 1
    assert package.documents[0].document.id == "hit"
    assert package.diagnostics.hits_by_source.get("jira") == 1
    assert package.diagnostics.query_kind == "error_code"
    assert "jira" in package.diagnostics.preferred_sources
    assert any(step.startswith("synonym:ORA-12541->") for step in package.diagnostics.steps)
    assert "ORA-12541" in package.diagnostics.synonym_expansions
    assert any(section.name == "similar_bugs" for section in package.sections)
    assert any(call.filters.source_types == ["jira"] for call in repo.calls)
    assert any(call.text == "tns" for call in repo.calls)
