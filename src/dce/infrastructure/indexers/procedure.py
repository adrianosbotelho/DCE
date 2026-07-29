"""Procedure indexer — operational runbooks as dedicated documents."""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping, Sequence
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
    ".dce/procedures/**/*.md",
    "procedures/**/*.md",
    "docs/procedures/**/*.md",
)
_NUMBERED_STEP_RE = re.compile(r"(?m)^\s*(?:\d+[.)]\s+|[-*]\s+\[[ xX]\]\s+)")


def extract_steps(frontmatter: Mapping[str, Any], body: str) -> list[str]:
    """Extract procedure steps from frontmatter list or numbered body lines."""
    raw = frontmatter.get("steps")
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
        steps = [str(item).strip() for item in raw if str(item).strip()]
        if steps:
            return steps
    steps = []
    for line in body.splitlines():
        if _NUMBERED_STEP_RE.match(line):
            cleaned = _NUMBERED_STEP_RE.sub("", line, count=1).strip()
            if cleaned:
                steps.append(cleaned)
    return steps


class ProcedureIndexer:
    """Indexer for operational procedures / runbooks (typed markdown)."""

    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root.resolve()

    @property
    def name(self) -> str:
        return "procedure"

    @property
    def source_type(self) -> str:
        return SourceType.PROCEDURE.value

    def discover(self, config: Mapping[str, Any]) -> Iterator[TextFileItem]:
        patterns = config.get("paths") or list(_DEFAULT_PATHS)
        if isinstance(patterns, str):
            patterns = [patterns]
        yield from discover_text_files(self._root, [str(p) for p in patterns])

    def transform(self, item: TextFileItem) -> Document:
        frontmatter, body = split_frontmatter(item.text)
        title = extract_title(body, frontmatter, item.relative_path)
        tags = as_str_list(frontmatter.get("tags"))
        if "procedure" not in {t.lower() for t in tags}:
            tags = [*tags, "procedure"]
        steps = extract_steps(frontmatter, body)
        severity = optional_str(frontmatter.get("severity"))
        audience = optional_str(frontmatter.get("audience"))
        if severity and severity.lower() not in {t.lower() for t in tags}:
            tags = [*tags, severity]
        summary = optional_str(frontmatter.get("summary")) or body.strip()[:240]

        metadata: dict[str, Any] = {
            "content_hash": content_hash(item.text),
            "path": item.relative_path,
            "steps": steps,
            "step_count": len(steps),
            "severity": severity,
            "audience": audience,
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
                "steps",
                "severity",
                "audience",
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
