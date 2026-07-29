"""Tests for SQLite backup/restore (PB-093)."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from dce.domain.errors import StorageError
from dce.domain.models import Document, SearchSpec
from dce.infrastructure.storage.backup import backup_database, restore_database
from dce.infrastructure.storage.connection import connect
from dce.infrastructure.storage.migrations import apply_migrations
from dce.infrastructure.storage.repository import SqliteDocumentRepository
from dce.interfaces.cli.main import app

runner = CliRunner()


def _seed_db(path: Path) -> None:
    with connect(path) as conn:
        apply_migrations(conn)
        repo = SqliteDocumentRepository(conn)
        repo.upsert_many(
            [
                Document(
                    id="doc-1",
                    source_type="markdown",
                    uri="a.md",
                    title="Hello",
                    body="ORA-12541 listener",
                )
            ]
        )


def test_backup_and_restore_roundtrip(tmp_path: Path) -> None:
    source = tmp_path / "live.sqlite"
    backup = tmp_path / "copy.sqlite"
    restored = tmp_path / "restored.sqlite"
    _seed_db(source)

    result = backup_database(source, backup, write_manifest=True)
    assert result.backup_path.is_file()
    assert result.manifest_path is not None
    assert result.manifest_path.is_file()
    assert result.bytes_written > 0
    assert result.schema_version >= 1

    restored_result = restore_database(backup, restored, force=False)
    assert restored_result.destination_path.is_file()

    with connect(restored) as conn:
        repo = SqliteDocumentRepository(conn)
        hits = repo.search(SearchSpec(text="ORA-12541", limit=5))
    assert len(hits) == 1
    assert hits[0].document.id == "doc-1"


def test_restore_requires_force(tmp_path: Path) -> None:
    source = tmp_path / "live.sqlite"
    backup = tmp_path / "copy.sqlite"
    _seed_db(source)
    backup_database(source, backup, write_manifest=False)
    with pytest.raises(StorageError):
        restore_database(backup, source, force=False)
    restore_database(backup, source, force=True)


def test_cli_backup_restore(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    assert runner.invoke(app, ["init", str(ws), "--name", "bak"]).exit_code == 0
    docs = ws / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("# Hello\n\nORA-12541\n", encoding="utf-8")
    assert runner.invoke(app, ["index", str(ws)]).exit_code == 0

    backup = tmp_path / "out.sqlite"
    bak = runner.invoke(
        app,
        ["backup", "--path", str(ws), "--output", str(backup), "--format", "json"],
    )
    assert bak.exit_code == 0, bak.output
    assert backup.is_file()
    assert Path(str(backup) + ".manifest.json").is_file()

    # Wipe live DB (+ WAL sidecars) then restore
    db = ws / ".dce" / "dce.sqlite"
    db.unlink()
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = Path(str(db) + suffix)
        if sidecar.exists():
            sidecar.unlink()
    rst = runner.invoke(
        app,
        [
            "restore",
            "--path",
            str(ws),
            "--input",
            str(backup),
            "--format",
            "json",
        ],
    )
    assert rst.exit_code == 0, rst.output
    assert db.is_file()

    search = runner.invoke(app, ["search", "ORA-12541", "--path", str(ws)])
    assert search.exit_code == 0
    assert "ORA-12541" in search.output or "Hello" in search.output
