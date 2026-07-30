"""Setup wizard use-cases exposed to the local web UI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dce import __version__
from dce.application.build_context import build_context
from dce.application.indexing import run_indexing
from dce.domain.errors import WorkspaceError
from dce.domain.models import ContextQuery
from dce.infrastructure.indexers.registry import build_default_indexers
from dce.infrastructure.storage.connection import connect
from dce.infrastructure.storage.repository import SqliteDocumentRepository
from dce.infrastructure.storage.workspace import (
    DEFAULT_CONFIG_NAME,
    doctor_workspace,
    init_workspace,
    load_workspace,
)
from dce.interfaces.kiro_steering import steering_payload as kiro_steering_payload
from dce.interfaces.mcp.schemas import WorkspaceStatusResult


def resolve_workspace_path(raw: str | None, *, default: Path | None = None) -> Path:
    """Normalize a workspace path from UI/API input."""
    text = (raw or "").strip()
    if text:
        return Path(text).expanduser().resolve()
    if default is not None:
        return default.resolve()
    return Path.cwd().resolve()


def workspace_exists(path: Path) -> bool:
    return (path / DEFAULT_CONFIG_NAME).is_file()


def status_payload(path: Path) -> dict[str, Any]:
    """Doctor + facets summary for the UI."""
    if not workspace_exists(path):
        return {
            "ok": False,
            "initialized": False,
            "workspace_path": str(path),
            "dce_version": __version__,
            "error": f"Missing {DEFAULT_CONFIG_NAME} — initialize the workspace first.",
        }
    report = doctor_workspace(path)
    status = WorkspaceStatusResult.from_doctor_report(report)
    facets: dict[str, Any] = {}
    try:
        _root, _config, database_path = load_workspace(path)
        with connect(database_path) as conn:
            facets = SqliteDocumentRepository(conn).list_facets().model_dump(mode="json")
    except WorkspaceError:
        facets = {}
    return {
        "ok": report.healthy,
        "initialized": True,
        "workspace_path": str(path),
        "dce_version": __version__,
        "status": status.model_dump(mode="json"),
        "facets": facets,
    }


def init_payload(path: Path, *, name: str | None = None, force: bool = False) -> dict[str, Any]:
    result = init_workspace(path, name=name, force=force)
    return {
        "ok": True,
        "workspace_path": str(result.workspace_root),
        "config_path": str(result.config_path),
        "database_path": str(result.database_path),
        "schema_version": result.schema_version,
        "created_config": result.created_config,
        "created_database": result.created_database,
    }


def index_payload(path: Path, *, source: str | None = None) -> dict[str, Any]:
    root, config, database_path = load_workspace(path)
    indexers_config = config.get("indexers") or {}
    if not isinstance(indexers_config, dict):
        return {"ok": False, "error": "indexers config must be a mapping"}
    with connect(database_path) as conn:
        result = run_indexing(
            SqliteDocumentRepository(conn),
            build_default_indexers(root),
            indexers_config,
            only_source=source,
        )
    return {
        "ok": True,
        "total_upserted": result.total_upserted,
        "related_uris_linked": result.related_uris_linked,
        "runs": [
            {
                "name": run.name,
                "source_type": run.source_type,
                "discovered": run.discovered,
                "upserted": run.upserted,
                "skipped": run.skipped,
                "detail": run.detail,
            }
            for run in result.runs
        ],
    }


def build_payload(path: Path, text: str) -> dict[str, Any]:
    _root, config, database_path = load_workspace(path)
    from dce.infrastructure.storage.workspace import (
        anchor_patterns_from_config,
        synonyms_from_config,
    )

    with connect(database_path) as conn:
        package = build_context(
            SqliteDocumentRepository(conn),
            ContextQuery(text=text),
            synonym_dictionary=synonyms_from_config(config),
            anchor_patterns=anchor_patterns_from_config(config),
        )
    return {
        "ok": True,
        "schema_version": package.schema_version,
        "document_count": len(package.documents),
        "titles": [item.document.title for item in package.documents[:10]],
        "diagnostics": package.diagnostics.model_dump(mode="json"),
    }


def steering_payload() -> dict[str, Any]:
    """Kiro steering text for the setup wizard / CLI."""
    return dict(kiro_steering_payload())


def mcp_config_payload(path: Path, *, dce_command: str = "dce") -> dict[str, Any]:
    """Kiro MCP JSON using absolute paths where possible."""
    workspace = str(path.resolve())
    # On Windows portable, callers should pass the absolute path to dce.exe.
    command = dce_command
    config = {
        "mcpServers": {
            "dce": {
                "command": command,
                "args": ["mcp", "--path", workspace],
            }
        }
    }
    return {
        "ok": True,
        "workspace_path": workspace,
        "command": command,
        "config": config,
        "config_json": __import__("json").dumps(config, indent=2, ensure_ascii=False),
        "notes": [
            "Cole o JSON nas configurações MCP do Kiro.",
            "No Windows use caminho absoluto do exe (ex.: C:\\Tools\\dce\\dce.exe).",
            "Reinicie / recarregue o servidor MCP após salvar.",
        ],
    }


def seed_sample_doc(path: Path) -> dict[str, Any]:
    """Create a sample markdown doc so first-time users can smoke-test build."""
    docs = path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    target = docs / "oracle-listener.md"
    if target.is_file():
        return {"ok": True, "created": False, "path": str(target)}
    target.write_text(
        "---\n"
        "title: Oracle listener tip\n"
        "project: payments\n"
        "component: listener\n"
        "technology: oracle\n"
        "tags: [oracle, network]\n"
        "---\n\n"
        "Fix ORA-12541 by checking listener status and bouncing the listener "
        "after config changes.\n",
        encoding="utf-8",
    )
    return {"ok": True, "created": True, "path": str(target)}
