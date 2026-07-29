"""SQLite connection helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def connect(database_path: Path | str) -> sqlite3.Connection:
    """Open a SQLite connection with sensible defaults for DCE."""
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn
