"""Jira offline import indexer (JSON / CSV) — no network."""

from __future__ import annotations

import csv
import json
import logging
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dce.application.related_uris import (
    extract_pr_uris,
    issue_uri,
    merge_unique,
    normalize_related_uris,
)
from dce.domain.models import Document, SourceType
from dce.infrastructure.indexers.common import (
    content_hash,
    discover_text_files,
    optional_str,
    stable_document_id,
)

logger = logging.getLogger(__name__)

_DEFAULT_PATHS = ("imports/jira/**/*.json", "imports/jira/**/*.csv")

_DEFAULT_FIELD_MAP: dict[str, str] = {
    "solution": "solution",
    "lessons_learned": "lessons_learned",
}


@dataclass(frozen=True)
class JiraIssueItem:
    """Normalized issue payload discovered from an import file."""

    issue: dict[str, Any]
    source_file: str


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",") if part.strip()]
        return parts or ([value] if value.strip() else [])
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, dict):
                name = item.get("name") or item.get("value") or item.get("displayName")
                if name:
                    out.append(str(name).strip())
            else:
                text = str(item).strip()
                if text:
                    out.append(text)
        return out
    if isinstance(value, dict):
        name = value.get("name") or value.get("value") or value.get("displayName")
        return [str(name).strip()] if name else []
    text = str(value).strip()
    return [text] if text else []


def _named(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, dict):
        for key in ("name", "displayName", "value", "key"):
            if value.get(key):
                return str(value[key]).strip()
        return None
    return optional_str(value)


def _lookup(data: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data and data[key] not in (None, ""):
            return data[key]
    return None


def _mapped_value(data: Mapping[str, Any], field_map: Mapping[str, str], logical: str) -> Any:
    source_key = field_map.get(logical, logical)
    if source_key in data:
        return data[source_key]
    # Also allow nested fields dict already flattened.
    return data.get(logical)


def normalize_issue(
    raw: Mapping[str, Any],
    *,
    field_map: Mapping[str, str] | None = None,
) -> dict[str, Any] | None:
    """Normalize flat DCE or Jira REST-ish issue into a canonical dict."""
    mapping = {**_DEFAULT_FIELD_MAP, **(field_map or {})}
    payload: dict[str, Any] = dict(raw)
    fields = payload.get("fields")
    if isinstance(fields, dict):
        # Prefer top-level key; merge fields underneath without clobbering key.
        merged = dict(fields)
        for top_key, value in payload.items():
            if top_key != "fields":
                merged[top_key] = value
        payload = merged

    key_raw = optional_str(_lookup(payload, "key", "issue_key", "issueKey", "id"))
    if key_raw is None:
        return None
    key = key_raw.upper()

    title = optional_str(_lookup(payload, "title", "summary", "Summary")) or key
    description = optional_str(_lookup(payload, "description", "Description")) or ""
    issue_type = _named(_lookup(payload, "type", "issuetype", "issue_type", "Issue Type"))
    priority = _named(_lookup(payload, "priority", "Priority"))
    sprint = optional_str(_lookup(payload, "sprint", "Sprint"))
    components = _as_list(_lookup(payload, "components", "component", "Components"))
    labels = _as_list(_lookup(payload, "labels", "Labels", "tags"))
    assignee = _named(_lookup(payload, "assignee", "Assignee", "responsible"))
    resolution = _named(_lookup(payload, "resolution", "Resolution"))
    solution = optional_str(_mapped_value(payload, mapping, "solution"))
    lessons = optional_str(_mapped_value(payload, mapping, "lessons_learned"))
    related_files = _as_list(_lookup(payload, "related_files", "files", "attachments"))
    related_prs = _as_list(_lookup(payload, "related_prs", "pull_requests", "prs"))

    comments_raw = _lookup(payload, "comments", "comment")
    comments: list[dict[str, str]] = []
    if isinstance(comments_raw, dict):
        comments_raw = comments_raw.get("comments") or comments_raw.get("items") or []
    if isinstance(comments_raw, list):
        for item in comments_raw:
            if isinstance(item, dict):
                author = _named(item.get("author")) or optional_str(item.get("author")) or ""
                body = optional_str(item.get("body")) or optional_str(item.get("text")) or ""
                if body:
                    comments.append({"author": author, "body": body})
            else:
                text = str(item).strip()
                if text:
                    comments.append({"author": "", "body": text})
    elif isinstance(comments_raw, str) and comments_raw.strip():
        comments.append({"author": "", "body": comments_raw.strip()})

    project = optional_str(_lookup(payload, "project", "Project"))
    if not project and "-" in key:
        project = key.split("-", 1)[0]

    return {
        "key": key,
        "title": title,
        "description": description,
        "type": issue_type,
        "priority": priority,
        "sprint": sprint,
        "components": components,
        "labels": labels,
        "assignee": assignee,
        "comments": comments,
        "resolution": resolution,
        "solution": solution,
        "lessons_learned": lessons,
        "related_files": related_files,
        "related_prs": related_prs,
        "project": project,
    }


def build_issue_body(issue: Mapping[str, Any]) -> str:
    """Compose an FTS-friendly body from structured issue fields."""
    lines: list[str] = [
        f"Issue: {issue.get('key')}",
        f"Title: {issue.get('title')}",
    ]
    if issue.get("type"):
        lines.append(f"Type: {issue['type']}")
    if issue.get("priority"):
        lines.append(f"Priority: {issue['priority']}")
    if issue.get("sprint"):
        lines.append(f"Sprint: {issue['sprint']}")
    if issue.get("components"):
        lines.append("Components: " + ", ".join(issue["components"]))
    if issue.get("labels"):
        lines.append("Labels: " + ", ".join(issue["labels"]))
    if issue.get("assignee"):
        lines.append(f"Assignee: {issue['assignee']}")
    if issue.get("resolution"):
        lines.append(f"Resolution: {issue['resolution']}")
    lines.append("")
    lines.append("Description:")
    lines.append(str(issue.get("description") or "").strip() or "(none)")
    if issue.get("solution"):
        lines.extend(["", "Solution:", str(issue["solution"])])
    if issue.get("lessons_learned"):
        lines.extend(["", "Lessons learned:", str(issue["lessons_learned"])])
    comments = issue.get("comments") or []
    if comments:
        lines.extend(["", "Comments:"])
        for comment in comments:
            author = comment.get("author") or "unknown"
            lines.append(f"- {author}: {comment.get('body', '')}")
    if issue.get("related_files"):
        lines.extend(["", "Related files:", ", ".join(issue["related_files"])])
    if issue.get("related_prs"):
        lines.extend(["", "Related PRs:", ", ".join(issue["related_prs"])])
    return "\n".join(lines).strip()


def _iter_issue_dicts(payload: Any) -> Iterator[Mapping[str, Any]]:
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, Mapping):
                yield item
        return
    if isinstance(payload, Mapping):
        if "issues" in payload and isinstance(payload["issues"], list):
            for item in payload["issues"]:
                if isinstance(item, Mapping):
                    yield item
            return
        if "key" in payload or "fields" in payload or "summary" in payload or "title" in payload:
            yield payload
            return
        # Map of key -> issue
        for value in payload.values():
            if isinstance(value, Mapping) and (
                "key" in value or "fields" in value or "summary" in value or "title" in value
            ):
                yield value


def parse_json_issues(
    text: str,
    *,
    field_map: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Parse JSON text into normalized issues."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Skipping invalid JSON import")
        return []
    issues: list[dict[str, Any]] = []
    for raw in _iter_issue_dicts(payload):
        normalized = normalize_issue(raw, field_map=field_map)
        if normalized:
            issues.append(normalized)
    return issues


def parse_csv_issues(
    text: str,
    *,
    field_map: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Parse CSV text into normalized issues."""
    reader = csv.DictReader(text.splitlines())
    issues: list[dict[str, Any]] = []
    for row in reader:
        cleaned = {key: value for key, value in row.items() if key}
        normalized = normalize_issue(cleaned, field_map=field_map)
        if normalized:
            issues.append(normalized)
    return issues


class JiraImportIndexer:
    """Indexer for offline Jira JSON/CSV exports."""

    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root.resolve()

    @property
    def name(self) -> str:
        return "jira_import"

    @property
    def source_type(self) -> str:
        return SourceType.JIRA.value

    def discover(self, config: Mapping[str, Any]) -> Iterator[JiraIssueItem]:
        patterns = config.get("paths") or list(_DEFAULT_PATHS)
        if isinstance(patterns, str):
            patterns = [patterns]
        field_map_raw = config.get("field_map") or {}
        field_map: dict[str, str] = (
            {str(k): str(v) for k, v in field_map_raw.items()}
            if isinstance(field_map_raw, Mapping)
            else {}
        )

        # Reuse text discovery for JSON; CSV also as text.
        for item in discover_text_files(
            self._root,
            [str(p) for p in patterns],
            suffixes=frozenset({".json", ".csv"}),
        ):
            suffix = item.absolute_path.suffix.lower()
            if suffix == ".json":
                issues = parse_json_issues(item.text, field_map=field_map)
            elif suffix == ".csv":
                issues = parse_csv_issues(item.text, field_map=field_map)
            else:
                continue
            for issue in issues:
                yield JiraIssueItem(issue=issue, source_file=item.relative_path)

    def transform(self, item: JiraIssueItem) -> Document:
        issue = item.issue
        key = str(issue["key"])
        title = str(issue.get("title") or key)
        body = build_issue_body(issue)
        labels = list(issue.get("labels") or [])
        issue_type = optional_str(issue.get("type"))
        tags = list(labels)
        if key not in tags:
            tags.append(key)
        if issue_type and issue_type not in tags:
            tags.append(issue_type)

        components = list(issue.get("components") or [])
        related_files = list(issue.get("related_files") or [])
        related_prs = list(issue.get("related_prs") or [])
        related = normalize_related_uris(
            merge_unique(
                related_files,
                related_prs,
                [issue_uri(key)],
                extract_pr_uris(
                    title,
                    str(issue.get("description") or ""),
                    str(issue.get("solution") or ""),
                    *related_prs,
                ),
            )
        )
        summary_parts = [title]
        if issue.get("solution"):
            summary_parts.append(f"Solution: {issue['solution']}")
        summary = " — ".join(summary_parts)[:240]

        metadata: dict[str, Any] = {
            "content_hash": content_hash(json.dumps(issue, sort_keys=True, ensure_ascii=False)),
            "source_file": item.source_file,
            "key": key,
            "type": issue_type,
            "priority": issue.get("priority"),
            "sprint": issue.get("sprint"),
            "components": components,
            "labels": labels,
            "assignee": issue.get("assignee"),
            "comments": issue.get("comments") or [],
            "resolution": issue.get("resolution"),
            "solution": issue.get("solution"),
            "lessons_learned": issue.get("lessons_learned"),
            "related_files": issue.get("related_files") or [],
            "related_prs": issue.get("related_prs") or [],
        }

        now = datetime.now(UTC)
        return Document(
            id=stable_document_id(self.source_type, key),
            source_type=self.source_type,
            uri=key,
            title=title,
            body=body,
            summary=summary,
            metadata=metadata,
            tags=tags,
            project=optional_str(issue.get("project")),
            component=components[0] if components else None,
            technology=None,
            related_uris=related,
            updated_at=now,
            created_at=now,
        )
