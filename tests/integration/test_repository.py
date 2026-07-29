"""Integration tests for SqliteDocumentRepository."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from dce.domain.models import Document, SearchFilters, SearchSpec
from dce.infrastructure.storage.connection import connect
from dce.infrastructure.storage.repository import SqliteDocumentRepository


class FixedClock:
    def __init__(self, moment: datetime) -> None:
        self._moment = moment

    def now(self) -> datetime:
        return self._moment


def _repo(tmp_path: Path) -> SqliteDocumentRepository:
    conn = connect(tmp_path / "dce.sqlite")
    return SqliteDocumentRepository(
        conn,
        clock=FixedClock(datetime(2026, 7, 29, 12, 0, tzinfo=UTC)),
    )


def _sample(doc_id: str, **kwargs: object) -> Document:
    base = {
        "id": doc_id,
        "source_type": "markdown",
        "uri": f"file:///{doc_id}.md",
        "title": f"Title {doc_id}",
        "body": "Connection refused ORA-12541 listener",
        "summary": "Oracle network error",
        "tags": ["oracle", "network"],
        "project": "payments",
        "component": "db",
        "technology": "oracle",
    }
    base.update(kwargs)
    return Document(**base)  # type: ignore[arg-type]


def test_upsert_get_and_idempotent(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    assert repo.upsert_many([_sample("doc-1")]) == 1
    assert repo.upsert_many([_sample("doc-1", title="Updated")]) == 1
    got = repo.get("doc-1")
    assert got is not None
    assert got.title == "Updated"
    assert got.indexed_at is not None
    assert repo.get("missing") is None


def test_search_fts_finds_error_code(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    repo.upsert_many(
        [
            _sample("a", body="ORA-12541 TNS no listener"),
            _sample(
                "b",
                body="unrelated markdown about CSS flexbox",
                title="Flex",
                tags=["css"],
                uri="file:///b.md",
            ),
        ]
    )
    hits = repo.search(SearchSpec(text="ORA-12541", limit=10))
    assert len(hits) >= 1
    assert hits[0].document.id == "a"
    assert hits[0].score >= 0


def test_search_with_filters(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    repo.upsert_many(
        [
            _sample("p1", project="payments", uri="file:///p1.md"),
            _sample(
                "p2",
                project="identity",
                body="ORA-12541 again",
                uri="file:///p2.md",
            ),
        ]
    )
    hits = repo.search(
        SearchSpec(
            text="ORA-12541",
            filters=SearchFilters(project="payments"),
            limit=10,
        )
    )
    assert [h.document.id for h in hits] == ["p1"]


def test_search_empty_text_lists_with_filters(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    repo.upsert_many(
        [
            _sample("1", source_type="adr", uri="file:///1.md"),
            _sample("2", source_type="markdown", uri="file:///2.md"),
        ]
    )
    hits = repo.search(SearchSpec(text="", filters=SearchFilters(source_types=["adr"]), limit=10))
    assert len(hits) == 1
    assert hits[0].document.source_type == "adr"


def test_list_recent_ordering_and_tag_filter(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    older = _sample(
        "old",
        uri="file:///old.md",
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        tags=["alpha"],
    )
    newer = _sample(
        "new",
        uri="file:///new.md",
        updated_at=datetime(2026, 6, 1, tzinfo=UTC),
        tags=["beta"],
    )
    repo.upsert_many([older, newer])
    recent = repo.list_recent(limit=10)
    assert [d.id for d in recent] == ["new", "old"]

    filtered = repo.list_recent(limit=10, filters=SearchFilters(tags=["beta"]))
    assert [d.id for d in filtered] == ["new"]


def test_upsert_many_empty(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    assert repo.upsert_many([]) == 0


def test_repository_satisfies_protocol(tmp_path: Path) -> None:
    from dce.domain.ports import DocumentRepository

    repo = _repo(tmp_path)
    assert isinstance(repo, DocumentRepository)


def test_connect_sets_row_factory(tmp_path: Path) -> None:
    conn = connect(tmp_path / "x.sqlite")
    assert conn.row_factory is sqlite3.Row
    conn.close()
