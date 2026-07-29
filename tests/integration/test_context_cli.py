"""Integration tests for build/search/show CLI and context builder."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from dce.interfaces.cli.main import app

runner = CliRunner()


def _seed_workspace(root: Path) -> None:
    assert runner.invoke(app, ["init", str(root), "--name", "ctx"]).exit_code == 0
    docs = root / "docs"
    docs.mkdir()
    (docs / "oracle.md").write_text(
        "---\ntitle: Oracle listener\ntags: [oracle]\n---\n\n"
        "Troubleshooting ORA-12541 TNS no listener.\n",
        encoding="utf-8",
    )
    (docs / "other.md").write_text("# CSS Flex\n\nLayout tips.\n", encoding="utf-8")
    assert runner.invoke(app, ["index", str(root)]).exit_code == 0


def test_cli_build_returns_context_package_json(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    _seed_workspace(root)

    result = runner.invoke(
        app,
        ["build", "ORA-12541", "--path", str(root), "--format", "json"],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "1"
    assert payload["query"]["text"] == "ORA-12541"
    assert len(payload["documents"]) >= 1
    titles = [item["document"]["title"] for item in payload["documents"]]
    assert "Oracle listener" in titles
    assert "diagnostics" in payload


def test_cli_search_and_show(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    _seed_workspace(root)

    search = runner.invoke(
        app,
        ["search", "ORA-12541", "--path", str(root), "--format", "json"],
    )
    assert search.exit_code == 0, search.stdout
    hits = json.loads(search.stdout)
    assert len(hits) >= 1
    doc_id = hits[0]["document"]["id"]

    show = runner.invoke(app, ["show", doc_id, "--path", str(root)])
    assert show.exit_code == 0, show.stdout
    document = json.loads(show.stdout)
    assert document["id"] == doc_id
    assert "ORA-12541" in document["body"]


def test_cli_show_missing(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    assert runner.invoke(app, ["init", str(root)]).exit_code == 0
    result = runner.invoke(app, ["show", "missing-id", "--path", str(root)])
    assert result.exit_code == 1


def test_cli_build_table_format(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    _seed_workspace(root)
    result = runner.invoke(
        app,
        ["build", "listener", "--path", str(root), "--format", "table"],
    )
    assert result.exit_code == 0, result.stdout
    assert "dce build" in result.stdout or "Score" in result.stdout
