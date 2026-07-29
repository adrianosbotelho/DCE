"""Integration tests for schema migrations."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from dce.infrastructure.storage.migrations import (
    CURRENT_SCHEMA_VERSION,
    apply_migrations,
    get_schema_version,
    is_fts5_available,
)


def test_migrations_create_schema(tmp_path: Path) -> None:
    db = tmp_path / "t.sqlite"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    assert get_schema_version(conn) == 0
    assert is_fts5_available(conn) is True
    version = apply_migrations(conn)
    assert version == CURRENT_SCHEMA_VERSION
    assert get_schema_version(conn) == CURRENT_SCHEMA_VERSION

    tables = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')")
    }
    assert "documents" in tables
    assert "documents_fts" in tables
    assert "schema_migrations" in tables
    assert "index_runs" in tables

    # Idempotent
    assert apply_migrations(conn) == CURRENT_SCHEMA_VERSION
    conn.close()
