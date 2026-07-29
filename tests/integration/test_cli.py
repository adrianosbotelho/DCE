"""CLI smoke tests via Typer CliRunner."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dce.interfaces.cli.main import app

runner = CliRunner()


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "dce" in result.stdout


def test_cli_init_and_doctor(tmp_path: Path) -> None:
    ws = tmp_path / "workspace"
    init_result = runner.invoke(app, ["init", str(ws), "--name", "cli-demo"])
    assert init_result.exit_code == 0, init_result.stdout
    assert "schema" in init_result.stdout

    doctor_result = runner.invoke(app, ["doctor", str(ws)])
    assert doctor_result.exit_code == 0, doctor_result.stdout
    assert "fts5" in doctor_result.stdout


def test_cli_facets(tmp_path: Path) -> None:
    import json

    ws = tmp_path / "workspace"
    assert runner.invoke(app, ["init", str(ws)]).exit_code == 0
    docs = ws / "docs"
    docs.mkdir()
    (docs / "note.md").write_text(
        "---\ntitle: Facet doc\nproject: payments\ncomponent: db\n"
        "technology: oracle\ntags: [oracle]\n---\n\nbody\n",
        encoding="utf-8",
    )
    assert runner.invoke(app, ["index", str(ws)]).exit_code == 0
    table = runner.invoke(app, ["facets", str(ws)])
    assert table.exit_code == 0, table.stdout
    assert "payments" in table.stdout
    as_json = runner.invoke(app, ["facets", str(ws), "--json"])
    assert as_json.exit_code == 0, as_json.stdout
    payload = json.loads(as_json.stdout)
    assert payload["schema_version"] == "1"
    assert any(item["value"] == "payments" for item in payload["facets"]["projects"])


def test_cli_index_json(tmp_path: Path) -> None:
    import json

    ws = tmp_path / "workspace"
    assert runner.invoke(app, ["init", str(ws)]).exit_code == 0
    docs = ws / "docs"
    docs.mkdir()
    (docs / "note.md").write_text(
        "---\ntitle: Indexed\n---\n\nORA-12541 body\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["index", str(ws), "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "1"
    assert payload["total_upserted"] >= 1
    assert isinstance(payload["runs"], list)
    assert any(run["name"] == "markdown" and run["upserted"] >= 1 for run in payload["runs"])


def test_cli_doctor_json(tmp_path: Path) -> None:
    import json

    ws = tmp_path / "workspace"
    assert runner.invoke(app, ["init", str(ws)]).exit_code == 0
    result = runner.invoke(app, ["doctor", str(ws), "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "1"
    assert payload["healthy"] is True
    assert payload["mcp"]["primary_tool"] == "build_context"
    assert "search_by_tag" in payload["mcp"]["stable_tools"]
    assert payload["document_count"] == 0
    assert payload["counts_by_source"] == {}
    assert payload["newest_indexed_at"] is None
    names = {item["name"] for item in payload["checks"]}
    assert {"config", "database", "fts5", "schema", "documents", "mcp"} <= names


def test_cli_doctor_fails_without_init(tmp_path: Path) -> None:
    result = runner.invoke(app, ["doctor", str(tmp_path / "missing")])
    assert result.exit_code == 1
