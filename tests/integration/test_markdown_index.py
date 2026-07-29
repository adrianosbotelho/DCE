"""Integration: markdown discover → repository → FTS."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dce.domain.models import SearchSpec
from dce.infrastructure.indexers.markdown import MarkdownIndexer
from dce.infrastructure.storage.connection import connect
from dce.infrastructure.storage.repository import SqliteDocumentRepository
from dce.infrastructure.storage.workspace import init_workspace
from dce.interfaces.cli.main import app

runner = CliRunner()


def test_discover_and_search_roundtrip(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    init_workspace(root, name="md-demo")
    docs = root / "docs"
    docs.mkdir()
    (docs / "oracle.md").write_text(
        "---\ntitle: Listener errors\ntags: [oracle]\n---\n\nWe saw ORA-12541 in production.\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text("# Demo Workspace\n\nIntro.\n", encoding="utf-8")

    indexer = MarkdownIndexer(root)
    items = list(indexer.discover({"paths": ["docs/**/*.md", "README.md"]}))
    assert len(items) == 2
    documents = [indexer.transform(item) for item in items]

    with connect(root / ".dce" / "dce.sqlite") as conn:
        repo = SqliteDocumentRepository(conn)
        assert repo.upsert_many(documents) == 2
        hits = repo.search(SearchSpec(text="ORA-12541"))
        assert len(hits) == 1
        assert hits[0].document.title == "Listener errors"
        assert hits[0].document.tags == ["oracle"]


def test_skips_path_outside_via_symlink(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    root.mkdir()
    outside = tmp_path / "secret.md"
    outside.write_text("# Secret\n", encoding="utf-8")
    link = root / "leak.md"
    try:
        link.symlink_to(outside)
    except OSError:
        # Some environments restrict symlinks; skip assertion path.
        return

    indexer = MarkdownIndexer(root)
    items = list(indexer.discover({"paths": ["*.md"]}))
    assert items == []


def test_cli_index_indexes_markdown(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    assert runner.invoke(app, ["init", str(root), "--name", "cli"]).exit_code == 0
    (root / "note.md").write_text("# Note\n\nORA-12541 troubleshooting.\n", encoding="utf-8")

    result = runner.invoke(app, ["index", str(root)])
    assert result.exit_code == 0, result.stdout
    assert "markdown" in result.stdout
    assert "total upserted" in result.stdout

    # Idempotent second run
    again = runner.invoke(app, ["index", str(root), "--source", "md"])
    assert again.exit_code == 0, again.stdout

    with connect(root / ".dce" / "dce.sqlite") as conn:
        repo = SqliteDocumentRepository(conn)
        hits = repo.search(SearchSpec(text="ORA-12541"))
        assert len(hits) >= 1


def test_cli_index_unknown_source_fails(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    assert runner.invoke(app, ["init", str(root)]).exit_code == 0
    result = runner.invoke(app, ["index", str(root), "--source", "slack"])
    assert result.exit_code == 1
