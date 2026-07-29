"""Unit tests for domain models and budget trimming."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from dce.domain.models import (
    ContextBudget,
    ContextPackage,
    ContextQuery,
    Document,
    ScoredDocument,
    SearchSpec,
    apply_budget,
    document_char_size,
)
from dce.domain.ports import Clock, DocumentRepository, Indexer


def _doc(
    doc_id: str,
    *,
    source: str = "markdown",
    body: str = "body",
    title: str = "title",
) -> Document:
    return Document(
        id=doc_id,
        source_type=source,
        uri=f"uri:{doc_id}",
        title=title,
        body=body,
    )


def test_document_rejects_blank_id() -> None:
    with pytest.raises(ValidationError):
        Document(id="  ", source_type="markdown", uri="a.md")


def test_document_strips_fields() -> None:
    doc = Document(id=" x ", source_type=" markdown ", uri=" a.md ")
    assert doc.id == "x"
    assert doc.source_type == "markdown"
    assert doc.uri == "a.md"


def test_search_spec_limit_bounds() -> None:
    with pytest.raises(ValidationError):
        SearchSpec(limit=0)


def test_context_package_defaults() -> None:
    package = ContextPackage(query=ContextQuery(text="ORA-12541"))
    assert package.schema_version == "1"
    assert package.documents == []
    assert package.diagnostics.truncated is False


def test_document_char_size() -> None:
    doc = Document(
        id="1",
        source_type="markdown",
        uri="u",
        title="ab",
        body="cd",
        summary="e",
    )
    assert document_char_size(doc) == 5


def test_apply_budget_max_documents() -> None:
    scored = [
        ScoredDocument(document=_doc("1"), score=3),
        ScoredDocument(document=_doc("2"), score=2),
        ScoredDocument(document=_doc("3"), score=1),
    ]
    kept, truncated = apply_budget(scored, ContextBudget(max_documents=2, max_chars=100000))
    assert [item.document.id for item in kept] == ["1", "2"]
    assert truncated is True


def test_apply_budget_max_per_source() -> None:
    scored = [
        ScoredDocument(document=_doc("1", source="jira"), score=3),
        ScoredDocument(document=_doc("2", source="jira"), score=2),
        ScoredDocument(document=_doc("3", source="adr"), score=1),
    ]
    kept, truncated = apply_budget(
        scored,
        ContextBudget(max_documents=10, max_per_source=1, max_chars=100000),
    )
    assert [item.document.id for item in kept] == ["1", "3"]
    assert truncated is True


def test_apply_budget_max_chars() -> None:
    scored = [
        ScoredDocument(document=_doc("1", body="aaaa"), score=2),
        ScoredDocument(document=_doc("2", body="bbbb"), score=1),
    ]
    # title "title" (5) + body (4) = 9 per doc with empty summary
    kept, truncated = apply_budget(
        scored,
        ContextBudget(max_documents=10, max_per_source=10, max_chars=12),
    )
    assert len(kept) == 1
    assert truncated is True


def test_apply_budget_zero_documents() -> None:
    scored = [ScoredDocument(document=_doc("1"), score=1)]
    kept, truncated = apply_budget(scored, ContextBudget(max_documents=0))
    assert kept == []
    assert truncated is True


def test_protocols_are_runtime_checkable() -> None:
    assert DocumentRepository is not None
    assert Indexer is not None
    assert Clock is not None


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 7, 29, tzinfo=UTC)


def test_clock_protocol_structural() -> None:
    clock: Clock = _FixedClock()
    assert clock.now().year == 2026
