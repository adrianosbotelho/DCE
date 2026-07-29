"""Snippet indexer — curated code/command snippets as dedicated documents."""

from __future__ import annotations

import re
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

_DEFAULT_PATHS = (
    ".dce/snippets/**/*.md",
    "snippets/**/*.md",
    "docs/snippets/**/*.md",
)
_FENCE_RE = re.compile(r"```([^\n`]*)\n(.*?)```", re.DOTALL)


def extract_code_fence(body: str) -> tuple[str | None, str | None]:
    """Return ``(language, code)`` from the first fenced code block, if any."""
    match = _FENCE_RE.search(body)
    if not match:
        return None, None
    language = match.group(1).strip() or None
    code = match.group(2).strip() or None
    return language, code


class SnippetIndexer:
    """Indexer for curated code/command snippets (typed markdown)."""

    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root.resolve()

    @property
    def name(self) -> str:
        return "snippet"

    @property
    def source_type(self) -> str:
        return SourceType.SNIPPET.value

    def discover(self, config: Mapping[str, Any]) -> Iterator[TextFileItem]:
        patterns = config.get("paths") or list(_DEFAULT_PATHS)
        if isinstance(patterns, str):
            patterns = [patterns]
        yield from discover_text_files(self._root, [str(p) for p in patterns])

    def transform(self, item: TextFileItem) -> Document:
        frontmatter, body = split_frontmatter(item.text)
        title = extract_title(body, frontmatter, item.relative_path)
        tags = as_str_list(frontmatter.get("tags"))
        if "snippet" not in {t.lower() for t in tags}:
            tags = [*tags, "snippet"]

        fence_lang, fence_code = extract_code_fence(body)
        language = optional_str(frontmatter.get("language")) or fence_lang
        code = optional_str(frontmatter.get("code")) or fence_code
        usage = optional_str(frontmatter.get("usage"))
        if language and language.lower() not in {t.lower() for t in tags}:
            tags = [*tags, language]

        summary = optional_str(frontmatter.get("summary"))
        if not summary:
            summary = (code or body.strip())[:240]

        metadata: dict[str, Any] = {
            "content_hash": content_hash(item.text),
            "path": item.relative_path,
            "language": language,
            "code": code,
            "usage": usage,
        }
        skip = {
            "title",
            "Title",
            "tags",
            "summary",
            "project",
            "component",
            "technology",
            "language",
            "code",
            "usage",
        }
        for key, value in frontmatter.items():
            if key in skip:
                continue
            metadata[key] = value

        technology = optional_str(frontmatter.get("technology")) or language

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
            technology=technology,
            updated_at=item.mtime,
            created_at=item.mtime,
        )
