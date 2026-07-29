"""Canonical related_uris helpers and post-index issue↔commit linking."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable, Sequence

from dce.domain.models import Document, SearchFilters, SearchSpec, SourceType
from dce.domain.ports import DocumentRepository

logger = logging.getLogger(__name__)

_ISSUE_URI_RE = re.compile(r"^issue:([A-Z][A-Z0-9]+-\d+)$", re.IGNORECASE)
_COMMIT_URI_RE = re.compile(r"^commit:([0-9a-f]{7,40})$", re.IGNORECASE)
_PR_HTTP_RE = re.compile(
    r"https?://[^\s<>\]\)]+/(?:pull|pulls|merge_requests)/\d+[^\s<>\]\)]*",
    re.IGNORECASE,
)
_PR_REF_RE = re.compile(
    r"\b(?:PR|MR|pull(?:\s+request)?|merge\s+request)\s*[#!]?\s*(\d+)\b",
    re.IGNORECASE,
)

_LINK_FETCH_LIMIT = 500


def issue_uri(key: str) -> str:
    """Canonical URI for a Jira-like issue key."""
    return f"issue:{key.strip().upper()}"


def commit_uri(sha: str) -> str:
    """Canonical URI for a git commit SHA."""
    return f"commit:{sha.strip().lower()}"


def pr_uri(ref: str | int) -> str:
    """Canonical URI for a pull/merge request number (when no full URL)."""
    return f"pr:{int(ref)}"


def merge_unique(*groups: Iterable[str]) -> list[str]:
    """Preserve first-seen order across URI groups."""
    out: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for raw in group:
            value = raw.strip()
            if not value or value in seen:
                continue
            seen.add(value)
            out.append(value)
    return out


def extract_pr_uris(*texts: str) -> list[str]:
    """Extract PR/MR URLs and numbered refs from free text."""
    found: list[str] = []
    seen: set[str] = set()
    for text in texts:
        for match in _PR_HTTP_RE.findall(text):
            url = match.rstrip(".,);]")
            if url not in seen:
                seen.add(url)
                found.append(url)
        for match in _PR_REF_RE.finditer(text):
            uri = pr_uri(match.group(1))
            if uri not in seen:
                seen.add(uri)
                found.append(uri)
    return found


def normalize_related_uri(value: str) -> str:
    """Normalize known related URI shapes; leave paths/URLs otherwise."""
    raw = value.strip()
    if not raw:
        return raw
    issue = _ISSUE_URI_RE.match(raw)
    if issue:
        return issue_uri(issue.group(1))
    commit = _COMMIT_URI_RE.match(raw)
    if commit:
        return commit_uri(commit.group(1))
    if re.fullmatch(r"[A-Z][A-Z0-9]+-\d+", raw, flags=re.IGNORECASE):
        return issue_uri(raw)
    if re.fullmatch(r"[0-9a-f]{7,40}", raw, flags=re.IGNORECASE):
        return commit_uri(raw)
    if _PR_HTTP_RE.fullmatch(raw):
        return raw.rstrip(".,);]")
    pr_num = re.fullmatch(r"pr:(\d+)", raw, flags=re.IGNORECASE)
    if pr_num:
        return pr_uri(pr_num.group(1))
    return raw


def normalize_related_uris(uris: Sequence[str]) -> list[str]:
    """Normalize and de-dupe a related_uris list."""
    return merge_unique(normalize_related_uri(u) for u in uris)


def issue_keys_from_uris(uris: Sequence[str]) -> list[str]:
    """Return issue keys referenced by ``issue:KEY`` URIs."""
    keys: list[str] = []
    seen: set[str] = set()
    for uri in uris:
        match = _ISSUE_URI_RE.match(uri.strip())
        if not match:
            continue
        key = match.group(1).upper()
        if key not in seen:
            seen.add(key)
            keys.append(key)
    return keys


def _fetch_source(repository: DocumentRepository, source_type: str) -> list[Document]:
    hits = repository.search(
        SearchSpec(
            text="",
            filters=SearchFilters(source_types=[source_type]),
            limit=_LINK_FETCH_LIMIT,
        )
    )
    return [hit.document for hit in hits]


def link_related_uris(repository: DocumentRepository) -> int:
    """Bidirectionally link jira issues and git commits via related_uris.

    - Git docs mentioning issue keys receive ``commit:SHA`` and ``issue:KEY``.
    - Jira docs receive ``commit:SHA`` (and PR URIs) from matching commits.

    Returns the number of documents upserted with updates.
    """
    git_docs = _fetch_source(repository, SourceType.GIT.value)
    jira_docs = _fetch_source(repository, SourceType.JIRA.value)
    if not git_docs and not jira_docs:
        return 0

    commits_by_issue: dict[str, list[Document]] = {}
    for doc in git_docs:
        keys = list(doc.metadata.get("issue_keys") or [])
        keys.extend(issue_keys_from_uris(doc.related_uris))
        for tag in doc.tags:
            if re.fullmatch(r"[A-Z][A-Z0-9]+-\d+", tag, flags=re.IGNORECASE):
                keys.append(tag.upper())
        for key in dict.fromkeys(k.upper() for k in keys if k):
            commits_by_issue.setdefault(key, []).append(doc)

    updates: list[Document] = []

    for doc in git_docs:
        sha = str(doc.metadata.get("sha") or doc.uri)
        keys = list(doc.metadata.get("issue_keys") or [])
        keys.extend(issue_keys_from_uris(doc.related_uris))
        for tag in doc.tags:
            if re.fullmatch(r"[A-Z][A-Z0-9]+-\d+", tag, flags=re.IGNORECASE):
                keys.append(tag.upper())
        unique_keys = list(dict.fromkeys(k.upper() for k in keys if k))
        desired = normalize_related_uris(
            merge_unique(
                doc.related_uris,
                [commit_uri(sha)],
                [issue_uri(k) for k in unique_keys],
                extract_pr_uris(doc.title, doc.body, doc.summary),
            )
        )
        if desired != normalize_related_uris(doc.related_uris):
            updates.append(doc.model_copy(update={"related_uris": desired}))

    jira_by_key = {str(doc.metadata.get("key") or doc.uri).upper(): doc for doc in jira_docs}
    for key, doc in jira_by_key.items():
        matching = commits_by_issue.get(key, [])
        commit_links = [commit_uri(str(c.metadata.get("sha") or c.uri)) for c in matching]
        pr_links: list[str] = []
        for c in matching:
            pr_links.extend(extract_pr_uris(c.title, c.body, c.summary))
            pr_links.extend(
                u for u in c.related_uris if u.startswith(("pr:", "http://", "https://"))
            )
        desired = normalize_related_uris(
            merge_unique(
                doc.related_uris,
                [issue_uri(key)],
                commit_links,
                pr_links,
            )
        )
        if desired != normalize_related_uris(doc.related_uris):
            updates.append(doc.model_copy(update={"related_uris": desired}))

    if not updates:
        return 0
    count = repository.upsert_many(updates)
    logger.info("related_uris linked documents=%s", count)
    return count
