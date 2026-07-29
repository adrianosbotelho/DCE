"""Unit tests for Jira offline import normalization."""

from __future__ import annotations

from pathlib import Path

from dce.domain.ports import Indexer
from dce.infrastructure.indexers.jira_import import (
    JiraImportIndexer,
    build_issue_body,
    normalize_issue,
    parse_csv_issues,
    parse_json_issues,
)


def test_normalize_flat_issue() -> None:
    issue = normalize_issue(
        {
            "key": "proj-42",
            "title": "Listener down",
            "description": "ORA-12541",
            "type": "Bug",
            "priority": "High",
            "sprint": "Sprint 1",
            "components": ["db"],
            "labels": ["oracle"],
            "assignee": "alice",
            "comments": [{"author": "bob", "body": "restart listener"}],
            "solution": "Start tnslsnr",
            "lessons_learned": "Check firewall first",
            "related_prs": ["https://example/pr/1"],
        }
    )
    assert issue is not None
    assert issue["key"] == "PROJ-42"
    assert issue["project"] == "PROJ"
    assert issue["solution"] == "Start tnslsnr"
    assert issue["comments"][0]["body"] == "restart listener"
    body = build_issue_body(issue)
    assert "ORA-12541" in body
    assert "Lessons learned" in body


def test_normalize_jira_rest_ish_and_field_map() -> None:
    issue = normalize_issue(
        {
            "key": "PAY-7",
            "fields": {
                "summary": "Timeout",
                "description": "details",
                "issuetype": {"name": "Task"},
                "priority": {"name": "Low"},
                "components": [{"name": "api"}],
                "labels": ["net"],
                "assignee": {"displayName": "carol"},
                "comment": {"comments": [{"author": {"displayName": "dave"}, "body": "retry"}]},
                "customfield_10001": "Use pool",
                "customfield_10002": "Document pool sizing",
            },
        },
        field_map={
            "solution": "customfield_10001",
            "lessons_learned": "customfield_10002",
        },
    )
    assert issue is not None
    assert issue["title"] == "Timeout"
    assert issue["type"] == "Task"
    assert issue["assignee"] == "carol"
    assert issue["solution"] == "Use pool"
    assert issue["lessons_learned"] == "Document pool sizing"


def test_parse_json_wrapper_and_csv() -> None:
    issues = parse_json_issues('{"issues":[{"key":"A-1","title":"One","description":"x"}]}')
    assert len(issues) == 1
    assert issues[0]["key"] == "A-1"

    csv_text = "key,title,description,solution\nB-2,Two,desc,fix-it\n"
    csv_issues = parse_csv_issues(csv_text)
    assert len(csv_issues) == 1
    assert csv_issues[0]["key"] == "B-2"
    assert csv_issues[0]["solution"] == "fix-it"


def test_indexer_discover_transform(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    export = root / "imports" / "jira"
    export.mkdir(parents=True)
    (export / "bugs.json").write_text(
        '[{"key":"PAY-1","title":"ORA-12541","description":"no listener",'
        '"labels":["oracle"],"solution":"start listener"}]',
        encoding="utf-8",
    )
    (export / "more.csv").write_text(
        "key,title,description,type\nPAY-2,CSV bug,body,Bug\n",
        encoding="utf-8",
    )
    indexer = JiraImportIndexer(root)
    assert isinstance(indexer, Indexer)
    items = list(indexer.discover({}))
    assert len(items) == 2
    docs = [indexer.transform(item) for item in items]
    by_uri = {doc.uri: doc for doc in docs}
    assert by_uri["PAY-1"].source_type == "jira"
    assert "ORA-12541" in by_uri["PAY-1"].body
    assert by_uri["PAY-1"].metadata["solution"] == "start listener"
    assert by_uri["PAY-2"].tags
