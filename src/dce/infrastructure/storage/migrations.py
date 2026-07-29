"""Versioned SQLite schema migrations for DCE."""

from __future__ import annotations

import sqlite3

CURRENT_SCHEMA_VERSION = 1

_MIGRATION_1 = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    uri TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    project TEXT,
    component TEXT,
    technology TEXT,
    tags_json TEXT NOT NULL DEFAULT '[]',
    related_uris_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT,
    updated_at TEXT,
    indexed_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_source_type ON documents(source_type);
CREATE INDEX IF NOT EXISTS idx_documents_project ON documents(project);
CREATE INDEX IF NOT EXISTS idx_documents_component ON documents(component);
CREATE INDEX IF NOT EXISTS idx_documents_technology ON documents(technology);
CREATE INDEX IF NOT EXISTS idx_documents_updated_at ON documents(updated_at);
CREATE INDEX IF NOT EXISTS idx_documents_indexed_at ON documents(indexed_at);

-- unicode61 keeps technical tokens (e.g. ORA-12541) usable; porter stemming deferred.
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    id UNINDEXED,
    title,
    body,
    summary,
    tags,
    tokenize = 'unicode61'
);

CREATE TABLE IF NOT EXISTS index_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indexer_name TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    documents_upserted INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'running',
    detail TEXT NOT NULL DEFAULT ''
);
"""


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Return the highest applied schema version, or 0 if none."""
    row = conn.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name = 'schema_migrations'
        """
    ).fetchone()
    if row is None:
        return 0
    version_row = conn.execute(
        "SELECT COALESCE(MAX(version), 0) AS version FROM schema_migrations"
    ).fetchone()
    assert version_row is not None
    return int(version_row["version"])


def is_fts5_available(conn: sqlite3.Connection) -> bool:
    """Probe whether this SQLite build includes FTS5."""
    try:
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS _dce_fts5_probe USING fts5(x)")
        conn.execute("DROP TABLE IF EXISTS _dce_fts5_probe")
    except sqlite3.OperationalError:
        return False
    return True


def apply_migrations(conn: sqlite3.Connection) -> int:
    """Apply pending migrations. Returns resulting schema version."""
    if not is_fts5_available(conn):
        msg = "SQLite FTS5 is required but not available in this Python/SQLite build"
        raise RuntimeError(msg)

    current = get_schema_version(conn)
    if current < 1:
        conn.executescript(_MIGRATION_1)
        conn.execute(
            """
            INSERT INTO schema_migrations (version, applied_at)
            VALUES (1, datetime('now'))
            """
        )
        conn.commit()
        current = 1
    return current
