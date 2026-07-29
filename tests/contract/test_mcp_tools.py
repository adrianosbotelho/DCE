"""Contract tests for MCP tool shapes (Kiro-facing)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from dce.interfaces.cli.main import app
from dce.interfaces.mcp.contract import (
    DIAGNOSTICS_KEYS,
    MCP_SCHEMA_VERSION,
    PRIMARY_TOOL,
    STABLE_TOOLS,
)
from dce.interfaces.mcp.server import create_mcp_server

runner = CliRunner()


def _seed(workspace: Path) -> None:
    assert runner.invoke(app, ["init", str(workspace), "--name", "mcp"]).exit_code == 0
    docs = workspace / "docs"
    docs.mkdir()
    (docs / "oracle.md").write_text(
        "---\ntitle: Oracle listener\ntags: [oracle]\nproject: payments\n---\n\n"
        "Fix ORA-12541 by checking listener status.\n",
        encoding="utf-8",
    )
    memory = workspace / ".dce" / "memory"
    memory.mkdir(parents=True, exist_ok=True)
    (memory / "note.md").write_text(
        "---\ntitle: Listener tip\ntags: [oracle]\n---\n\n"
        "Remember to bounce the listener after ORA-12541.\n",
        encoding="utf-8",
    )
    jira_dir = workspace / "imports" / "jira"
    jira_dir.mkdir(parents=True, exist_ok=True)
    (jira_dir / "export.json").write_text(
        """
        {
          "issues": [
            {
              "key": "PAY-125",
              "title": "TNS listener",
              "description": "ORA-12541 in prod",
              "type": "Bug"
            }
          ]
        }
        """,
        encoding="utf-8",
    )
    assert runner.invoke(app, ["index", str(workspace)]).exit_code == 0
    assert runner.invoke(app, ["index", str(workspace), "--source", "jira"]).exit_code == 0


def _call(server: Any, name: str, arguments: dict[str, Any]) -> Any:
    return asyncio.run(server.call_tool(name, arguments))


def test_mcp_lists_expected_tools(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    _seed(root)
    server = create_mcp_server(root)
    tools = asyncio.run(server.list_tools())
    names = {tool.name for tool in tools}
    assert names == set(STABLE_TOOLS)
    assert PRIMARY_TOOL in names
    build = next(tool for tool in tools if tool.name == PRIMARY_TOOL)
    assert build.output_schema is not None
    assert "schema_version" in (build.output_schema.get("properties") or {})
    for tool in tools:
        assert tool.output_schema is not None
        props = tool.output_schema.get("properties") or {}
        assert "schema_version" in props


def test_mcp_build_context_structured(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    _seed(root)
    server = create_mcp_server(root)
    result = _call(server, "build_context", {"text": "ORA-12541"})
    assert result.is_error is False
    payload = result.structured_content
    assert payload is not None
    assert payload["schema_version"] == MCP_SCHEMA_VERSION
    assert payload["query"]["text"] == "ORA-12541"
    assert isinstance(payload["documents"], list)
    assert len(payload["documents"]) >= 1
    assert "diagnostics" in payload
    diagnostics = payload["diagnostics"]
    assert DIAGNOSTICS_KEYS.issubset(diagnostics.keys())
    assert diagnostics["query_kind"] == "error_code"
    assert isinstance(diagnostics["steps"], list)
    assert len(diagnostics["steps"]) >= 1
    assert isinstance(diagnostics["synonym_expansions"], dict)
    titles = {item["document"]["title"] for item in payload["documents"]}
    assert "Oracle listener" in titles or "TNS listener" in titles


def test_mcp_build_context_empty_query_still_versioned(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    _seed(root)
    server = create_mcp_server(root)
    result = _call(server, "build_context", {"text": ""})
    assert result.is_error is False
    payload = result.structured_content
    assert payload is not None
    assert payload["schema_version"] == MCP_SCHEMA_VERSION
    assert DIAGNOSTICS_KEYS.issubset(payload["diagnostics"].keys())


def test_mcp_search_context_structured(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    _seed(root)
    server = create_mcp_server(root)
    result = _call(server, "search_context", {"text": "ORA-12541", "limit": 5})
    assert result.is_error is False
    payload = result.structured_content
    assert payload is not None
    assert payload["schema_version"] == MCP_SCHEMA_VERSION
    assert len(payload["documents"]) >= 1


def test_mcp_get_document_found_and_missing(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    _seed(root)
    server = create_mcp_server(root)

    search = _call(server, "search_context", {"text": "ORA-12541"})
    doc_id = search.structured_content["documents"][0]["document"]["id"]

    found = _call(server, "get_document", {"document_id": doc_id})
    assert found.structured_content["schema_version"] == MCP_SCHEMA_VERSION
    assert found.structured_content["found"] is True
    assert found.structured_content["document"]["id"] == doc_id

    missing = _call(server, "get_document", {"document_id": "does-not-exist"})
    assert missing.structured_content["schema_version"] == MCP_SCHEMA_VERSION
    assert missing.structured_content["found"] is False
    assert missing.structured_content["document"] is None


def test_mcp_recent_documents(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    _seed(root)
    server = create_mcp_server(root)
    result = _call(
        server,
        "recent_documents",
        {"limit": 10, "project": "payments"},
    )
    assert result.is_error is False
    payload = result.structured_content
    assert payload["schema_version"] == MCP_SCHEMA_VERSION
    assert len(payload["documents"]) >= 1
    assert payload["documents"][0]["project"] == "payments"


def test_mcp_search_memory_only_memory_sources(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    _seed(root)
    server = create_mcp_server(root)
    result = _call(server, "search_memory", {"text": "ORA-12541", "limit": 10})
    assert result.is_error is False
    payload = result.structured_content
    assert payload["schema_version"] == MCP_SCHEMA_VERSION
    assert len(payload["documents"]) >= 1
    assert all(item["document"]["source_type"] == "memory" for item in payload["documents"])
    assert payload["documents"][0]["document"]["title"] == "Listener tip"


def test_mcp_search_by_issue_finds_jira_key(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    _seed(root)
    server = create_mcp_server(root)
    result = _call(server, "search_by_issue", {"issue_key": "issue:pay-125", "limit": 10})
    assert result.is_error is False
    payload = result.structured_content
    assert payload["schema_version"] == MCP_SCHEMA_VERSION
    assert len(payload["documents"]) >= 1
    uris = {item["document"]["uri"] for item in payload["documents"]}
    assert "PAY-125" in uris


def test_mcp_search_by_project_scopes_hits(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    _seed(root)
    server = create_mcp_server(root)
    result = _call(
        server,
        "search_by_project",
        {"project": "project:payments", "text": "ORA-12541", "limit": 10},
    )
    assert result.is_error is False
    payload = result.structured_content
    assert payload["schema_version"] == MCP_SCHEMA_VERSION
    assert len(payload["documents"]) >= 1
    assert all(item["document"]["project"] == "payments" for item in payload["documents"])
    titles = {item["document"]["title"] for item in payload["documents"]}
    assert "Oracle listener" in titles


def test_mcp_search_by_project_empty_slug(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    _seed(root)
    server = create_mcp_server(root)
    result = _call(server, "search_by_project", {"project": "project:", "limit": 10})
    assert result.is_error is False
    payload = result.structured_content
    assert payload["schema_version"] == MCP_SCHEMA_VERSION
    assert payload["documents"] == []


def test_cli_mcp_requires_workspace(tmp_path: Path) -> None:
    result = runner.invoke(app, ["mcp", "--path", str(tmp_path / "missing")])
    assert result.exit_code == 1
