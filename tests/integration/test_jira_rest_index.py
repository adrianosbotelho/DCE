"""Integration: jira_rest CLI path with mocked HTTP."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from dce.domain.models import SearchFilters, SearchSpec
from dce.infrastructure.storage.connection import connect
from dce.infrastructure.storage.repository import SqliteDocumentRepository
from dce.interfaces.cli.main import app

runner = CliRunner()


def test_cli_index_jira_rest_mocked(tmp_path: Path, monkeypatch: Any) -> None:
    root = tmp_path / "ws"
    assert runner.invoke(app, ["init", str(root), "--name", "jr"]).exit_code == 0

    monkeypatch.setenv("JIRA_BASE_URL", "https://jira.example")
    monkeypatch.setenv("JIRA_PAT", "tok")

    payload = {
        "issues": [
            {
                "key": "PAY-77",
                "fields": {
                    "summary": "Listener flap",
                    "description": "ORA-12541 again",
                    "issuetype": {"name": "Bug"},
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

    monkeypatch.setattr(
        "dce.infrastructure.indexers.jira_rest.urllib.request.urlopen",
        lambda request, timeout=0: FakeResponse(),
    )

    result = runner.invoke(app, ["index", str(root), "--source", "jira_rest"])
    assert result.exit_code == 0, result.stdout
    assert "jira_rest" in result.stdout

    with connect(root / ".dce" / "dce.sqlite") as conn:
        repo = SqliteDocumentRepository(conn)
        hits = repo.search(
            SearchSpec(text="ORA-12541", filters=SearchFilters(source_types=["jira"]))
        )
        assert len(hits) == 1
        assert hits[0].document.uri == "PAY-77"
