"""ADR indexer — Architecture Decision Records as dedicated documents."""

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

_DEFAULT_PATHS = ("docs/adr/**/*.md",)
_ADR_NUM_RE = re.compile(r"ADR-?0*(\d+)", re.IGNORECASE)
_STATUS_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?Status(?:\*\*)?\s*:\s*(?:\*\*)?(.+?)(?:\*\*)?\s*$"
)


def extract_adr_number(
    relative_path: str,
    title: str,
    frontmatter: Mapping[str, Any],
) -> str | None:
    """Extract ADR number from frontmatter, title, or filename."""
    for key in ("adr_number", "number", "id"):
        value = frontmatter.get(key)
        if value is None:
            continue
        text = str(value).strip()
        match = _ADR_NUM_RE.search(text)
        if match:
            return match.group(1).zfill(3)
        if re.fullmatch(r"\d+", text):
            return text.zfill(3)
    for candidate in (title, Path(relative_path).stem):
        match = _ADR_NUM_RE.search(candidate)
        if match:
            return match.group(1).zfill(3)
    return None


def extract_adr_status(body: str, frontmatter: Mapping[str, Any]) -> str | None:
    """Extract ADR status from frontmatter or body convention."""
    for key in ("status", "Status"):
        value = optional_str(frontmatter.get(key))
        if value:
            return value
    match = _STATUS_RE.search(body)
    if match:
        return match.group(1).strip().strip("*").strip()
    return None


class AdrIndexer:
    """Indexer for Architecture Decision Records."""

    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root.resolve()

    @property
    def name(self) -> str:
        return "adr"

    @property
    def source_type(self) -> str:
        return SourceType.ADR.value

    def discover(self, config: Mapping[str, Any]) -> Iterator[TextFileItem]:
        patterns = config.get("paths") or list(_DEFAULT_PATHS)
        if isinstance(patterns, str):
            patterns = [patterns]
        yield from discover_text_files(self._root, [str(p) for p in patterns])

    def transform(self, item: TextFileItem) -> Document:
        frontmatter, body = split_frontmatter(item.text)
        title = extract_title(body, frontmatter, item.relative_path)
        adr_number = extract_adr_number(item.relative_path, title, frontmatter)
        status = extract_adr_status(body, frontmatter)
        tags = as_str_list(frontmatter.get("tags"))
        if adr_number and f"ADR-{adr_number}" not in tags:
            tags = [*tags, f"ADR-{adr_number}"]
        if status and status.lower() not in {t.lower() for t in tags}:
            tags = [*tags, status]

        summary = optional_str(frontmatter.get("summary")) or body.strip()[:240]
        metadata: dict[str, Any] = {
            "content_hash": content_hash(item.text),
            "path": item.relative_path,
            "adr_number": adr_number,
            "status": status,
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
                "status",
                "Status",
                "adr_number",
                "number",
                "id",
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
