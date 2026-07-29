"""Incident indexer — postmortems and incident notes as dedicated documents."""

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

_DEFAULT_PATHS = (
    ".dce/incidents/**/*.md",
    "incidents/**/*.md",
    "docs/incidents/**/*.md",
)

_META_KEYS = (
    "severity",
    "impact",
    "status",
    "resolution",
    "root_cause",
    "started_at",
    "resolved_at",
    "error_codes",
)


class IncidentIndexer:
    """Indexer for incident reports / postmortems (typed markdown)."""

    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root.resolve()

    @property
    def name(self) -> str:
        return "incident"

    @property
    def source_type(self) -> str:
        return SourceType.INCIDENT.value

    def discover(self, config: Mapping[str, Any]) -> Iterator[TextFileItem]:
        patterns = config.get("paths") or list(_DEFAULT_PATHS)
        if isinstance(patterns, str):
            patterns = [patterns]
        yield from discover_text_files(self._root, [str(p) for p in patterns])

    def transform(self, item: TextFileItem) -> Document:
        frontmatter, body = split_frontmatter(item.text)
        title = extract_title(body, frontmatter, item.relative_path)
        tags = as_str_list(frontmatter.get("tags"))
        if "incident" not in {t.lower() for t in tags}:
            tags = [*tags, "incident"]

        severity = optional_str(frontmatter.get("severity"))
        status = optional_str(frontmatter.get("status"))
        impact = optional_str(frontmatter.get("impact"))
        resolution = optional_str(frontmatter.get("resolution"))
        root_cause = optional_str(frontmatter.get("root_cause"))
        error_codes = as_str_list(frontmatter.get("error_codes"))

        for label in (severity, status, *error_codes):
            if label and label.lower() not in {t.lower() for t in tags}:
                tags = [*tags, label]

        summary = optional_str(frontmatter.get("summary"))
        if not summary:
            summary = f"{title} — {resolution}"[:240] if resolution else body.strip()[:240]

        metadata: dict[str, Any] = {
            "content_hash": content_hash(item.text),
            "path": item.relative_path,
            "severity": severity,
            "impact": impact,
            "status": status,
            "resolution": resolution,
            "root_cause": root_cause,
            "started_at": optional_str(frontmatter.get("started_at")),
            "resolved_at": optional_str(frontmatter.get("resolved_at")),
            "error_codes": error_codes,
        }
        skip = {
            "title",
            "Title",
            "tags",
            "summary",
            "project",
            "component",
            "technology",
            *_META_KEYS,
        }
        for key, value in frontmatter.items():
            if key in skip:
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
