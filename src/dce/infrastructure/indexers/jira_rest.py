"""Jira REST indexer — optional live search via JQL (never required for offline use)."""

from __future__ import annotations

import base64
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dce.domain.models import Document
from dce.infrastructure.indexers.jira_import import (
    JiraImportIndexer,
    JiraIssueItem,
    normalize_issue,
)

logger = logging.getLogger(__name__)

_DEFAULT_JQL = "order by updated DESC"
_DEFAULT_MAX_RESULTS = 50
_DEFAULT_TIMEOUT = 30.0
_DEFAULT_FIELDS = (
    "summary,description,status,issuetype,priority,components,labels,"
    "assignee,resolution,comment,project"
)


@dataclass(frozen=True)
class JiraRestCredentials:
    """Auth material resolved from environment variables."""

    base_url: str
    authorization: str


def resolve_jira_credentials(
    *,
    base_url: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> JiraRestCredentials | None:
    """Resolve Jira Cloud/Server credentials from env.

    Supported:
    - ``JIRA_BASE_URL`` (+ optional config ``base_url``)
    - Basic: ``JIRA_EMAIL`` + ``JIRA_API_TOKEN``
    - Bearer: ``JIRA_PAT`` / ``JIRA_TOKEN``
    """
    env = environ if environ is not None else os.environ
    url = (base_url or env.get("JIRA_BASE_URL") or "").strip().rstrip("/")
    if not url:
        return None

    pat = (env.get("JIRA_PAT") or env.get("JIRA_TOKEN") or "").strip()
    if pat:
        return JiraRestCredentials(base_url=url, authorization=f"Bearer {pat}")

    email = (env.get("JIRA_EMAIL") or "").strip()
    token = (env.get("JIRA_API_TOKEN") or "").strip()
    if email and token:
        raw = f"{email}:{token}".encode()
        encoded = base64.b64encode(raw).decode("ascii")
        return JiraRestCredentials(base_url=url, authorization=f"Basic {encoded}")

    return None


def fetch_jira_search(
    credentials: JiraRestCredentials,
    *,
    jql: str,
    max_results: int,
    fields: str = _DEFAULT_FIELDS,
    timeout: float = _DEFAULT_TIMEOUT,
    opener: Any | None = None,
) -> list[dict[str, Any]]:
    """Call Jira ``/rest/api/2/search`` and return raw issue objects."""
    query = urllib.parse.urlencode(
        {
            "jql": jql,
            "maxResults": max(1, min(max_results, 100)),
            "fields": fields,
        }
    )
    url = f"{credentials.base_url}/rest/api/2/search?{query}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": credentials.authorization,
            "User-Agent": "dev-context-engine/jira-rest",
        },
        method="GET",
    )
    urlopen = opener or urllib.request.urlopen
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    issues = payload.get("issues") if isinstance(payload, dict) else None
    if not isinstance(issues, list):
        return []
    return [issue for issue in issues if isinstance(issue, dict)]


class JiraRestIndexer:
    """Optional live Jira search indexer. Disabled / skipped without credentials."""

    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root.resolve()
        self._delegate = JiraImportIndexer(self._root)

    @property
    def name(self) -> str:
        return "jira_rest"

    @property
    def source_type(self) -> str:
        return self._delegate.source_type

    def discover(self, config: Mapping[str, Any]) -> Iterator[JiraIssueItem]:
        base_url = optional_str_config(config.get("base_url"))
        credentials = resolve_jira_credentials(base_url=base_url)
        if credentials is None:
            logger.warning(
                "jira_rest skipped — set JIRA_BASE_URL and "
                "JIRA_EMAIL+JIRA_API_TOKEN or JIRA_PAT"
            )
            return

        jql = str(config.get("jql") or _DEFAULT_JQL)
        max_results = int(config.get("max_results") or _DEFAULT_MAX_RESULTS)
        timeout = float(config.get("timeout") or _DEFAULT_TIMEOUT)
        field_map = config.get("field_map")
        mapping = field_map if isinstance(field_map, Mapping) else None

        try:
            raw_issues = fetch_jira_search(
                credentials,
                jql=jql,
                max_results=max_results,
                timeout=timeout,
            )
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            OSError,
            ValueError,
        ) as exc:
            logger.warning("jira_rest fetch failed — skipping: %s", exc)
            return

        for raw in raw_issues:
            issue = normalize_issue(raw, field_map=mapping)
            if issue is None:
                continue
            key = str(issue["key"])
            yield JiraIssueItem(issue=issue, source_file=f"jira-rest:{key}")

    def transform(self, item: JiraIssueItem) -> Document:
        """Reuse offline import transform so Documents stay identical."""
        return self._delegate.transform(item)


def optional_str_config(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
