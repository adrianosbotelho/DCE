"""SQLite database backup and restore (WAL-safe, portable snapshots)."""

from __future__ import annotations

import json
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dce import __version__
from dce.domain.errors import StorageError, WorkspaceError
from dce.infrastructure.storage.connection import connect
from dce.infrastructure.storage.migrations import get_schema_version


@dataclass(frozen=True)
class BackupResult:
    """Outcome of a database backup."""

    source_path: Path
    backup_path: Path
    manifest_path: Path | None
    schema_version: int
    bytes_written: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_path": str(self.source_path),
            "backup_path": str(self.backup_path),
            "manifest_path": str(self.manifest_path) if self.manifest_path else None,
            "schema_version": self.schema_version,
            "bytes_written": self.bytes_written,
            "dce_version": __version__,
        }


@dataclass(frozen=True)
class RestoreResult:
    """Outcome of a database restore."""

    backup_path: Path
    destination_path: Path
    schema_version: int
    bytes_restored: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "backup_path": str(self.backup_path),
            "destination_path": str(self.destination_path),
            "schema_version": self.schema_version,
            "bytes_restored": self.bytes_restored,
            "dce_version": __version__,
        }


def _remove_sqlite_sidecars(path: Path) -> None:
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = Path(str(path) + suffix)
        if sidecar.exists():
            sidecar.unlink()


def _connect_portable(database_path: Path) -> sqlite3.Connection:
    """Open/create a DB without WAL — suitable for single-file backups."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = DELETE")
    return conn


def _finalize_portable(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.execute("PRAGMA journal_mode = DELETE")
    conn.commit()


def backup_database(
    source_path: Path,
    backup_path: Path,
    *,
    write_manifest: bool = True,
) -> BackupResult:
    """Create a consistent, portable SQLite snapshot at ``backup_path``."""
    source = source_path.resolve()
    if not source.is_file():
        msg = f"Database not found: {source}"
        raise WorkspaceError(msg)

    destination = backup_path.resolve()
    if destination.exists() and destination.samefile(source):
        msg = "Backup path must differ from the live database"
        raise StorageError(msg)

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    _remove_sqlite_sidecars(destination)

    with connect(source) as src, _connect_portable(destination) as dst:
        schema_version = get_schema_version(src)
        src.backup(dst)
        _finalize_portable(dst)

    _remove_sqlite_sidecars(destination)
    bytes_written = destination.stat().st_size
    manifest_path: Path | None = None
    if write_manifest:
        manifest_path = Path(str(destination) + ".manifest.json")
        payload = {
            "schema_version": schema_version,
            "dce_version": __version__,
            "source_path": str(source),
            "backup_path": str(destination),
            "created_at": datetime.now(UTC).isoformat(),
            "bytes": bytes_written,
        }
        manifest_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return BackupResult(
        source_path=source,
        backup_path=destination,
        manifest_path=manifest_path,
        schema_version=schema_version,
        bytes_written=bytes_written,
    )


def restore_database(
    backup_path: Path,
    destination_path: Path,
    *,
    force: bool = False,
) -> RestoreResult:
    """Restore ``backup_path`` into the live database path."""
    backup = backup_path.resolve()
    if not backup.is_file():
        msg = f"Backup not found: {backup}"
        raise WorkspaceError(msg)

    destination = destination_path.resolve()
    if destination.exists() and not force:
        msg = f"Destination exists: {destination} (pass --force to overwrite)"
        raise StorageError(msg)

    if destination.exists() and destination.samefile(backup):
        msg = "Cannot restore a database onto itself"
        raise StorageError(msg)

    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_suffix(destination.suffix + ".restore-tmp")
    if temp_path.exists():
        temp_path.unlink()
    _remove_sqlite_sidecars(temp_path)

    with _connect_portable(backup) as src, _connect_portable(temp_path) as dst:
        schema_version = get_schema_version(src)
        src.backup(dst)
        _finalize_portable(dst)

    _remove_sqlite_sidecars(temp_path)
    if destination.exists():
        destination.unlink()
    _remove_sqlite_sidecars(destination)
    shutil.move(str(temp_path), str(destination))
    _remove_sqlite_sidecars(destination)

    return RestoreResult(
        backup_path=backup,
        destination_path=destination,
        schema_version=schema_version,
        bytes_restored=destination.stat().st_size,
    )
