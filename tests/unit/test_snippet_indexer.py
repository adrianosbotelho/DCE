"""Unit tests for snippet indexer."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from dce.domain.ports import Indexer
from dce.infrastructure.indexers.common import TextFileItem
from dce.infrastructure.indexers.snippet import SnippetIndexer, extract_code_fence


def test_extract_code_fence() -> None:
    lang, code = extract_code_fence("Intro\n\n```bash\nlsnrctl status\n```\n")
    assert lang == "bash"
    assert code == "lsnrctl status"
    assert extract_code_fence("no fence") == (None, None)


def test_snippet_transform(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    root.mkdir()
    text = (
        "---\ntitle: Check listener\ntags: [oracle]\n---\n\n"
        "Quick check:\n\n```bash\nlsnrctl status\n```\n"
    )
    item = TextFileItem(
        relative_path=".dce/snippets/listener.md",
        absolute_path=root / ".dce" / "snippets" / "listener.md",
        text=text,
        mtime=datetime.now(UTC),
    )
    indexer = SnippetIndexer(root)
    assert isinstance(indexer, Indexer)
    doc = indexer.transform(item)
    assert doc.source_type == "snippet"
    assert "snippet" in doc.tags
    assert "bash" in doc.tags
    assert doc.metadata["language"] == "bash"
    assert doc.metadata["code"] == "lsnrctl status"
    assert doc.technology == "bash"


def test_snippet_discover(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    snip = root / "snippets"
    snip.mkdir(parents=True)
    (snip / "ping.md").write_text("# Ping\n\n```sh\nping -c1 db\n```\n", encoding="utf-8")
    indexer = SnippetIndexer(root)
    items = list(indexer.discover({}))
    assert len(items) == 1
    doc = indexer.transform(items[0])
    assert doc.metadata["language"] == "sh"
