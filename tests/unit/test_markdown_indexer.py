"""Unit tests for markdown frontmatter and transform helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from dce.domain.ports import Indexer
from dce.infrastructure.indexers.common import (
    TextFileItem,
    extract_title,
    is_under_root,
    split_frontmatter,
    stable_document_id,
)
from dce.infrastructure.indexers.markdown import MarkdownIndexer


def test_split_frontmatter_present() -> None:
    text = "---\ntitle: Hello\ntags: [a, b]\n---\n\n# Body\n"
    meta, body = split_frontmatter(text)
    assert meta["title"] == "Hello"
    assert meta["tags"] == ["a", "b"]
    assert body.lstrip().startswith("# Body")


def test_split_frontmatter_absent() -> None:
    meta, body = split_frontmatter("# Just a heading\n")
    assert meta == {}
    assert body.startswith("# Just")


def test_split_frontmatter_invalid_yaml_keeps_text() -> None:
    text = "---\n: bad: [\n---\ncontent\n"
    meta, body = split_frontmatter(text)
    assert meta == {}
    assert body == text


def test_extract_title_priority() -> None:
    assert extract_title("# H1\n", {"title": "From FM"}, "x.md") == "From FM"
    assert extract_title("# Heading One\n", {}, "x.md") == "Heading One"
    assert extract_title("no heading", {}, "notes/demo.md") == "demo"


def test_document_id_stable() -> None:
    assert stable_document_id("markdown", "docs/a.md") == stable_document_id(
        "markdown", "docs/a.md"
    )
    assert stable_document_id("markdown", "docs/a.md") != stable_document_id(
        "markdown", "docs/b.md"
    )
    assert stable_document_id("markdown", "docs/a.md") != stable_document_id("adr", "docs/a.md")


def test_is_under_root(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    root.mkdir()
    inside = root / "docs" / "a.md"
    inside.parent.mkdir()
    inside.write_text("x", encoding="utf-8")
    assert is_under_root(inside, root) is True
    outside = tmp_path / "other.md"
    outside.write_text("x", encoding="utf-8")
    assert is_under_root(outside, root) is False


def test_transform_builds_document(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    root.mkdir()
    indexer = MarkdownIndexer(root)
    assert isinstance(indexer, Indexer)
    item = TextFileItem(
        relative_path="README.md",
        absolute_path=root / "README.md",
        text="---\ntitle: Root\nproject: demo\ntags: [intro]\n---\n\nHello ORA-12541\n",
        mtime=datetime(2026, 7, 29, tzinfo=UTC),
    )
    doc = indexer.transform(item)
    assert doc.source_type == "markdown"
    assert doc.title == "Root"
    assert doc.project == "demo"
    assert doc.tags == ["intro"]
    assert "ORA-12541" in doc.body
    assert doc.metadata["content_hash"]
    assert doc.uri == "README.md"


def test_markdown_excludes_adr_paths_by_default(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    (root / "docs" / "adr").mkdir(parents=True)
    (root / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
    (root / "docs" / "adr" / "ADR-001.md").write_text("# ADR-001\n", encoding="utf-8")
    indexer = MarkdownIndexer(root)
    items = list(indexer.discover({}))
    paths = {item.relative_path for item in items}
    assert "docs/guide.md" in paths
    assert "docs/adr/ADR-001.md" not in paths
