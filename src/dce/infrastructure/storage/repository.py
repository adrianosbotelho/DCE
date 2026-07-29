"""SQLite implementation of DocumentRepository with FTS5 search."""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from dce.domain.models import Document, ScoredDocument, SearchFilters, SearchSpec
from dce.domain.ports import Clock
from dce.infrastructure.storage.migrations import apply_migrations


class SystemClock:
    """Default clock using timezone-aware UTC now."""

    def now(self) -> datetime:
        return datetime.now(UTC)


_FTS_SPECIAL = re.compile(r'[\s"^~*(){}:]+')


def escape_fts5_query(text: str) -> str:
    """Build a safe FTS5 MATCH query from free text.

    Each token becomes a quoted phrase prefix query: ``"ora"*``.
    Empty / whitespace-only input yields an empty string (caller handles).
    """
    tokens = [t for t in _FTS_SPECIAL.split(text.strip()) if t]
    if not tokens:
        return ""
    parts: list[str] = []
    for token in tokens:
        safe = token.replace('"', '""')
        parts.append(f'"{safe}"*')
    return " AND ".join(parts)


def _dt_to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


def _parse_dt(value: str | None) -> datetime | None:
    if value is None or value == "":
        return None
    # Support SQLite datetime('now') and ISO-8601.
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _row_to_document(row: sqlite3.Row) -> Document:
    metadata = json.loads(row["metadata_json"] or "{}")
    tags = json.loads(row["tags_json"] or "[]")
    related = json.loads(row["related_uris_json"] or "[]")
    return Document(
        id=row["id"],
        source_type=row["source_type"],
        uri=row["uri"],
        title=row["title"] or "",
        body=row["body"] or "",
        summary=row["summary"] or "",
        metadata=metadata if isinstance(metadata, dict) else {},
        tags=list(tags) if isinstance(tags, list) else [],
        project=row["project"],
        component=row["component"],
        technology=row["technology"],
        related_uris=list(related) if isinstance(related, list) else [],
        created_at=_parse_dt(row["created_at"]),
        updated_at=_parse_dt(row["updated_at"]),
        indexed_at=_parse_dt(row["indexed_at"]),
    )


class SqliteDocumentRepository:
    """DocumentRepository backed by SQLite + FTS5."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        *,
        clock: Clock | None = None,
        migrate: bool = True,
    ) -> None:
        self._conn = conn
        self._clock: Clock = clock or SystemClock()
        if migrate:
            apply_migrations(self._conn)

    def upsert_many(self, documents: Sequence[Document]) -> int:
        if not documents:
            return 0

        now = self._clock.now()
        count = 0
        for document in documents:
            indexed_at = document.indexed_at or now
            updated_at = document.updated_at or indexed_at
            created_at = document.created_at or indexed_at
            tags_text = " ".join(document.tags)

            self._conn.execute(
                """
                INSERT INTO documents (
                    id, source_type, uri, title, body, summary,
                    metadata_json, project, component, technology,
                    tags_json, related_uris_json,
                    created_at, updated_at, indexed_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?,
                    ?, ?, ?
                )
                ON CONFLICT(id) DO UPDATE SET
                    source_type = excluded.source_type,
                    uri = excluded.uri,
                    title = excluded.title,
                    body = excluded.body,
                    summary = excluded.summary,
                    metadata_json = excluded.metadata_json,
                    project = excluded.project,
                    component = excluded.component,
                    technology = excluded.technology,
                    tags_json = excluded.tags_json,
                    related_uris_json = excluded.related_uris_json,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at,
                    indexed_at = excluded.indexed_at
                """,
                (
                    document.id,
                    document.source_type,
                    document.uri,
                    document.title,
                    document.body,
                    document.summary,
                    json.dumps(document.metadata, ensure_ascii=False),
                    document.project,
                    document.component,
                    document.technology,
                    json.dumps(document.tags, ensure_ascii=False),
                    json.dumps(document.related_uris, ensure_ascii=False),
                    _dt_to_iso(created_at),
                    _dt_to_iso(updated_at),
                    _dt_to_iso(indexed_at),
                ),
            )
            self._conn.execute("DELETE FROM documents_fts WHERE id = ?", (document.id,))
            self._conn.execute(
                """
                INSERT INTO documents_fts (id, title, body, summary, tags)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    document.id,
                    document.title,
                    document.body,
                    document.summary,
                    tags_text,
                ),
            )
            count += 1

        self._conn.commit()
        return count

    def get(self, document_id: str) -> Document | None:
        row = self._conn.execute(
            "SELECT * FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()
        if row is None:
            return None
        return _row_to_document(row)

    def search(self, spec: SearchSpec) -> list[ScoredDocument]:
        filters = spec.filters
        match = escape_fts5_query(spec.text)
        params: list[Any] = []
        where: list[str] = []

        if match:
            sql = """
                SELECT d.*, bm25(documents_fts) AS rank
                FROM documents_fts
                JOIN documents d ON d.id = documents_fts.id
                WHERE documents_fts MATCH ?
            """
            params.append(match)
        else:
            sql = """
                SELECT d.*, 0.0 AS rank
                FROM documents d
                WHERE 1 = 1
            """

        self._append_filters(where, params, filters, table_alias="d")
        if where:
            sql += " AND " + " AND ".join(where)

        if match:
            sql += " ORDER BY rank ASC, d.updated_at DESC"
        else:
            sql += " ORDER BY COALESCE(d.updated_at, d.indexed_at) DESC"

        sql += " LIMIT ?"
        params.append(spec.limit)

        rows = self._conn.execute(sql, params).fetchall()
        results: list[ScoredDocument] = []
        for row in rows:
            # bm25() in SQLite returns lower (more negative) for better matches.
            raw_rank = float(row["rank"])
            score = -raw_rank if match else 0.0
            results.append(ScoredDocument(document=_row_to_document(row), score=score))
        return results

    def list_recent(
        self,
        limit: int = 20,
        filters: SearchFilters | None = None,
    ) -> list[Document]:
        limit = max(1, min(limit, 500))
        params: list[Any] = []
        where: list[str] = []
        sql = "SELECT d.* FROM documents d WHERE 1 = 1"
        self._append_filters(where, params, filters or SearchFilters(), table_alias="d")
        if where:
            sql += " AND " + " AND ".join(where)
        sql += " ORDER BY COALESCE(d.updated_at, d.indexed_at) DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(sql, params).fetchall()
        return [_row_to_document(row) for row in rows]

    @staticmethod
    def _append_filters(
        where: list[str],
        params: list[Any],
        filters: SearchFilters,
        *,
        table_alias: str,
    ) -> None:
        alias = table_alias
        if filters.project:
            where.append(f"{alias}.project = ?")
            params.append(filters.project)
        if filters.component:
            where.append(f"{alias}.component = ?")
            params.append(filters.component)
        if filters.technology:
            where.append(f"{alias}.technology = ?")
            params.append(filters.technology)
        if filters.source_types:
            placeholders = ", ".join("?" for _ in filters.source_types)
            where.append(f"{alias}.source_type IN ({placeholders})")
            params.extend(filters.source_types)
        for tag in filters.tags:
            where.append(f"{alias}.tags_json LIKE ?")
            params.append(f'%"{tag}"%')
