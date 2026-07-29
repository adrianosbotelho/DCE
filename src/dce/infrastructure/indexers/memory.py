"""Memory indexer — curated local notes for agents."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

from dce.domain.models import Document, SourceType
from dce.infrastructure.indexers.common import (
    TextFileItem,
    as_str_list,
    content_hash,
    discover_text_files,
    extract_title,
    optional_str,
    split_frontmatter,
    stable_document_id,
)

_DEFAULT_PATHS = (".dce/memory/**/*.md", "memory/**/*.md")


class MemoryIndexer:
    """Indexer for curated memory notes (not a parallel product)."""

    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root.resolve()

    @property
    def name(self) -> str:
        return "memory"

    @property
    def source_type(self) -> str:
        return SourceType.MEMORY.value

    def discover(self, config: Mapping[str, Any]) -> Iterator[TextFileItem]:
        patterns = config.get("paths") or list(_DEFAULT_PATHS)
        if isinstance(patterns, str):
            patterns = [patterns]
        yield from discover_text_files(self._root, [str(p) for p in patterns])

    def transform(self, item: TextFileItem) -> Document:
        frontmatter, body = split_frontmatter(item.text)
        title = extract_title(body, frontmatter, item.relative_path)
        tags = as_str_list(frontmatter.get("tags"))
        if "memory" not in {t.lower() for t in tags}:
            tags = [*tags, "memory"]
        summary = optional_str(frontmatter.get("summary")) or body.strip()[:240]

        metadata: dict[str, Any] = {
            "content_hash": content_hash(item.text),
            "path": item.relative_path,
        }
        for key, value in frontmatter.items():
            if key in {
                "title",
                "Title",
                "tags",
                "summary",
                "project",
                "component",
                "technology",
            }:
                continue
            metadata[key] = value

        return Document(
            id=stable_document_id(self.source_type, item.relative_path),
            source_type=self.source_type,
            uri=item.relative_path,
            title=title,
            body=body.strip(),
            summary=summary,
            metadata=metadata,
            tags=tags,
            project=optional_str(frontmatter.get("project")),
            component=optional_str(frontmatter.get("component")),
            technology=optional_str(frontmatter.get("technology")),
            updated_at=item.mtime,
            created_at=item.mtime,
        )
