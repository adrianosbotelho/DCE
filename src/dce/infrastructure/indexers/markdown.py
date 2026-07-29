"""Markdown indexer — local files to canonical Documents."""

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

_DEFAULT_PATHS = ("docs/**/*.md", "README.md", "*.md")
_DEFAULT_EXCLUDE = (
    "docs/adr/**",
    ".dce/memory/**",
    "memory/**",
    ".dce/procedures/**",
    "procedures/**",
    "docs/procedures/**",
    ".dce/incidents/**",
    "incidents/**",
    "docs/incidents/**",
    ".dce/snippets/**",
    "snippets/**",
    "docs/snippets/**",
)


class MarkdownIndexer:
    """Indexer for local Markdown files (excludes typed source paths by default)."""

    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root.resolve()

    @property
    def name(self) -> str:
        return "markdown"

    @property
    def source_type(self) -> str:
        return SourceType.MARKDOWN.value

    def discover(self, config: Mapping[str, Any]) -> Iterator[TextFileItem]:
        patterns = config.get("paths") or list(_DEFAULT_PATHS)
        if isinstance(patterns, str):
            patterns = [patterns]
        exclude = config.get("exclude")
        if exclude is None:
            exclude = list(_DEFAULT_EXCLUDE)
        elif isinstance(exclude, str):
            exclude = [exclude]
        yield from discover_text_files(
            self._root,
            [str(p) for p in patterns],
            exclude=[str(p) for p in exclude],
        )

    def transform(self, item: TextFileItem) -> Document:
        frontmatter, body = split_frontmatter(item.text)
        title = extract_title(body, frontmatter, item.relative_path)
        tags = as_str_list(frontmatter.get("tags"))
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
