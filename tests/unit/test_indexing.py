"""Unit tests for indexing orchestration."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from dce.application.indexing import normalize_source_name, run_indexing
from dce.domain.models import Document, ScoredDocument, SearchFilters, SearchSpec


class FakeRepo:
    def __init__(self) -> None:
        self.stored: list[Document] = []

    def upsert_many(self, documents: Sequence[Document]) -> int:
        self.stored.extend(documents)
        return len(documents)

    def get(self, document_id: str) -> Document | None:
        return None

    def search(self, spec: SearchSpec) -> list[ScoredDocument]:
        return []

    def list_recent(
        self,
        limit: int = 20,
        filters: SearchFilters | None = None,
    ) -> list[Document]:
        return []


class FakeIndexer:
    def __init__(self, name: str, items: list[Document]) -> None:
        self._name = name
        self._items = items

    @property
    def name(self) -> str:
        return self._name

    @property
    def source_type(self) -> str:
        return self._name

    def discover(self, config: Mapping[str, Any]) -> Iterable[Document]:
        return list(self._items)

    def transform(self, item: Document) -> Document:
        return item


def _doc(doc_id: str) -> Document:
    return Document(id=doc_id, source_type="markdown", uri=f"{doc_id}.md", title=doc_id)


def test_normalize_source_aliases() -> None:
    assert normalize_source_name("MD") == "markdown"
    assert normalize_source_name("markdown") == "markdown"
    assert normalize_source_name("ADR") == "adr"
    assert normalize_source_name("mem") == "memory"
    assert normalize_source_name("proc") == "procedure"
    assert normalize_source_name("procedures") == "procedure"
    assert normalize_source_name("inc") == "incident"
    assert normalize_source_name("incidents") == "incident"
    assert normalize_source_name("snip") == "snippet"
    assert normalize_source_name("snippets") == "snippet"
    assert normalize_source_name("jira") == "jira_import"
    assert normalize_source_name("jira_api") == "jira_rest"
    assert normalize_source_name("jira_rest") == "jira_rest"
    assert normalize_source_name("git") == "git"
    assert normalize_source_name(None) is None


def test_run_indexing_respects_enabled_flag() -> None:
    repo = FakeRepo()
    indexer = FakeIndexer("markdown", [_doc("a")])
    result = run_indexing(
        repo,
        [indexer],
        {"markdown": {"enabled": False}},
    )
    assert result.total_upserted == 0
    assert result.runs[0].skipped is True


def test_run_indexing_only_source_ignores_enabled() -> None:
    repo = FakeRepo()
    indexer = FakeIndexer("markdown", [_doc("a"), _doc("b")])
    result = run_indexing(
        repo,
        [indexer],
        {"markdown": {"enabled": False}},
        only_source="md",
    )
    assert result.total_upserted == 2
    assert result.runs[0].discovered == 2


def test_run_indexing_unknown_source() -> None:
    repo = FakeRepo()
    result = run_indexing(repo, [], {}, only_source="jira")
    assert result.runs[0].skipped is True
    assert "unknown" in result.runs[0].detail
