"""Unit tests for optional Jira REST indexer."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

from dce.infrastructure.indexers.jira_rest import (
    JiraRestCredentials,
    JiraRestIndexer,
    fetch_jira_search,
    resolve_jira_credentials,
)


def test_resolve_jira_credentials_basic_and_pat() -> None:
    assert resolve_jira_credentials(environ={}) is None
    basic = resolve_jira_credentials(
        environ={
            "JIRA_BASE_URL": "https://acme.atlassian.net",
            "JIRA_EMAIL": "dev@acme.com",
            "JIRA_API_TOKEN": "secret",
        }
    )
    assert basic is not None
    assert basic.base_url == "https://acme.atlassian.net"
    assert basic.authorization.startswith("Basic ")

    pat = resolve_jira_credentials(
        environ={
            "JIRA_BASE_URL": "https://jira.example/",
            "JIRA_PAT": "token-xyz",
        }
    )
    assert pat is not None
    assert pat.base_url == "https://jira.example"
    assert pat.authorization == "Bearer token-xyz"


def test_fetch_jira_search_parses_issues() -> None:
    payload = {
        "issues": [
            {
                "key": "PAY-1",
                "fields": {"summary": "Listener", "description": "ORA-12541"},
            }
        ]
    }

    class FakeResponse:
        def read(self) -> bytes:
            return json.dumps(payload).encode("utf-8")

        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    def fake_urlopen(request: Any, timeout: float = 0) -> FakeResponse:
        assert "search" in request.full_url
        assert request.get_header("Authorization") == "Bearer tok"
        return FakeResponse()

    creds = JiraRestCredentials(
        base_url="https://jira.example",
        authorization="Bearer tok",
    )
    issues = fetch_jira_search(creds, jql="project=PAY", max_results=10, opener=fake_urlopen)
    assert len(issues) == 1
    assert issues[0]["key"] == "PAY-1"


def test_discover_skips_without_credentials(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.delenv("JIRA_BASE_URL", raising=False)
    monkeypatch.delenv("JIRA_PAT", raising=False)
    monkeypatch.delenv("JIRA_TOKEN", raising=False)
    monkeypatch.delenv("JIRA_EMAIL", raising=False)
    monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
    indexer = JiraRestIndexer(tmp_path)
    assert list(indexer.discover({})) == []


def test_discover_and_transform_with_mock(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("JIRA_BASE_URL", "https://jira.example")
    monkeypatch.setenv("JIRA_PAT", "tok")

    payload = {
        "issues": [
            {
                "key": "PAY-9",
                "fields": {
                    "summary": "TNS down",
                    "description": "ORA-12541 in prod",
                    "issuetype": {"name": "Bug"},
                    "priority": {"name": "High"},
                    "project": {"key": "PAY"},
                },
            }
        ]
    }

    class FakeResponse:
        def read(self) -> bytes:
            return json.dumps(payload).encode("utf-8")

        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    def fake_urlopen(request: Any, timeout: float = 0) -> FakeResponse:
        return FakeResponse()

    monkeypatch.setattr(
        "dce.infrastructure.indexers.jira_rest.urllib.request.urlopen",
        fake_urlopen,
    )

    indexer = JiraRestIndexer(tmp_path)
    items = list(indexer.discover({"jql": "project = PAY", "max_results": 5}))
    assert len(items) == 1
    doc = indexer.transform(items[0])
    assert doc.source_type == "jira"
    assert doc.uri == "PAY-9"
    assert "ORA-12541" in doc.body


def test_discover_skips_on_network_error(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("JIRA_BASE_URL", "https://jira.example")
    monkeypatch.setenv("JIRA_PAT", "tok")

    def boom(request: Any, timeout: float = 0) -> io.BytesIO:
        raise TimeoutError("slow")

    monkeypatch.setattr(
        "dce.infrastructure.indexers.jira_rest.urllib.request.urlopen",
        boom,
    )
    indexer = JiraRestIndexer(tmp_path)
    assert list(indexer.discover({})) == []
