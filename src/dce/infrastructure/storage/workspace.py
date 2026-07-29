"""Workspace bootstrap and health checks (composition helpers)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from dce.application.anchors import AnchorPattern, compile_anchor_pattern, default_anchor_patterns
from dce.domain.errors import WorkspaceError
from dce.domain.models import ContextBudget
from dce.infrastructure.storage.connection import connect
from dce.infrastructure.storage.migrations import (
    CURRENT_SCHEMA_VERSION,
    apply_migrations,
    get_schema_version,
    is_fts5_available,
)

DEFAULT_CONFIG_NAME = "dce.yaml"
DEFAULT_DB_RELATIVE = ".dce/dce.sqlite"


def default_config_dict(workspace_name: str = "workspace") -> dict[str, Any]:
    """Return the skeleton dce.yaml content."""
    return {
        "workspace": {
            "name": workspace_name,
            "database": DEFAULT_DB_RELATIVE,
        },
        "budget": {
            "max_documents": 20,
            "max_chars": 24000,
            "max_per_source": 5,
        },
        "retrieval": {
            "synonyms": {
                # Example override / extension — merged with built-ins:
                # "ORA-12541": ["tns", "listener"]
            },
            "anchors": {
                # Extra regex patterns merged with builtins (issue / ora / path).
                # Same name replaces a builtin. Example:
                # extra_patterns:
                #   - name: err_code
                #     pattern: '\\b(ERR-\\d{4})\\b'
                #     kind: error_code
                #     case: upper
                #     ignore_case: false
                "extra_patterns": []
            },
        },
        "indexers": {
            "markdown": {
                "enabled": True,
                "paths": ["docs/**/*.md", "README.md", "*.md"],
                "exclude": [
                    "docs/adr/**",
                    ".dce/memory/**",
                    "memory/**",
                    ".dce/procedures/**",
                    "procedures/**",
                    "docs/procedures/**",
                    ".dce/incidents/**",
                    "incidents/**",
                    "docs/incidents/**",
                    ".dce/snippets/**",
                    "snippets/**",
                    "docs/snippets/**",
                ],
            },
            "adr": {
                "enabled": True,
                "paths": ["docs/adr/**/*.md"],
            },
            "memory": {
                "enabled": True,
                "paths": [".dce/memory/**/*.md", "memory/**/*.md"],
            },
            "procedure": {
                "enabled": True,
                "paths": [
                    ".dce/procedures/**/*.md",
                    "procedures/**/*.md",
                    "docs/procedures/**/*.md",
                ],
            },
            "incident": {
                "enabled": True,
                "paths": [
                    ".dce/incidents/**/*.md",
                    "incidents/**/*.md",
                    "docs/incidents/**/*.md",
                ],
            },
            "snippet": {
                "enabled": True,
                "paths": [
                    ".dce/snippets/**/*.md",
                    "snippets/**/*.md",
                    "docs/snippets/**/*.md",
                ],
            },
            "jira_import": {
                "enabled": False,
                "paths": ["imports/jira/**/*.json", "imports/jira/**/*.csv"],
                "field_map": {
                    "solution": "solution",
                    "lessons_learned": "lessons_learned",
                },
            },
            "jira_rest": {
                "enabled": False,
                "jql": "order by updated DESC",
                "max_results": 50,
                "timeout": 30,
                # base_url optional — prefers JIRA_BASE_URL env
                # credentials: JIRA_EMAIL+JIRA_API_TOKEN or JIRA_PAT (never in YAML)
            },
            "git": {
                "enabled": False,
                "repo_path": ".",
                "max_commits": 200,
                "include_body": True,
            },
        },
    }


@dataclass(frozen=True)
class InitResult:
    """Outcome of workspace initialization."""

    workspace_root: Path
    config_path: Path
    database_path: Path
    schema_version: int
    created_config: bool
    created_database: bool


@dataclass
class DoctorCheck:
    """Single doctor diagnostic row."""

    name: str
    ok: bool
    detail: str


@dataclass
class DoctorReport:
    """Aggregated workspace health report."""

    workspace_root: Path
    checks: list[DoctorCheck] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return all(check.ok for check in self.checks)


def resolve_database_path(workspace_root: Path, config: dict[str, Any]) -> Path:
    """Resolve database path from config relative to workspace root."""
    workspace = config.get("workspace") or {}
    relative = workspace.get("database") or DEFAULT_DB_RELATIVE
    path = Path(relative)
    if path.is_absolute():
        return path
    return (workspace_root / path).resolve()


def load_config(config_path: Path) -> dict[str, Any]:
    """Load YAML config or raise WorkspaceError."""
    if not config_path.is_file():
        msg = f"Config not found: {config_path}"
        raise WorkspaceError(msg)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        msg = f"Config must be a mapping: {config_path}"
        raise WorkspaceError(msg)
    return raw


def init_workspace(
    workspace_root: Path,
    *,
    name: str | None = None,
    force: bool = False,
) -> InitResult:
    """Create dce.yaml skeleton and migrated SQLite database."""
    root = workspace_root.resolve()
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)
    if not root.is_dir():
        msg = f"Workspace root is not a directory: {root}"
        raise WorkspaceError(msg)

    config_path = root / DEFAULT_CONFIG_NAME
    created_config = False
    if config_path.exists() and not force:
        config = load_config(config_path)
    else:
        workspace_name = name or root.name or "workspace"
        config = default_config_dict(workspace_name)
        config_path.write_text(
            yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        created_config = True

    database_path = resolve_database_path(root, config)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    memory_dir = root / ".dce" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    procedures_dir = root / ".dce" / "procedures"
    procedures_dir.mkdir(parents=True, exist_ok=True)
    incidents_dir = root / ".dce" / "incidents"
    incidents_dir.mkdir(parents=True, exist_ok=True)
    snippets_dir = root / ".dce" / "snippets"
    snippets_dir.mkdir(parents=True, exist_ok=True)
    imports_dir = root / "imports" / "jira"
    imports_dir.mkdir(parents=True, exist_ok=True)
    created_database = not database_path.exists()

    with connect(database_path) as conn:
        apply_migrations(conn)
        version = get_schema_version(conn)

    return InitResult(
        workspace_root=root,
        config_path=config_path,
        database_path=database_path,
        schema_version=version,
        created_config=created_config,
        created_database=created_database,
    )


def doctor_workspace(workspace_root: Path) -> DoctorReport:
    """Inspect workspace config, schema, and FTS5 availability."""
    root = workspace_root.resolve()
    report = DoctorReport(workspace_root=root)
    config_path = root / DEFAULT_CONFIG_NAME

    if not config_path.is_file():
        report.checks.append(
            DoctorCheck(
                name="config",
                ok=False,
                detail=f"Missing {DEFAULT_CONFIG_NAME} — run `dce init`",
            )
        )
        return report

    try:
        config = load_config(config_path)
        report.checks.append(DoctorCheck(name="config", ok=True, detail=str(config_path)))
    except WorkspaceError as exc:
        report.checks.append(DoctorCheck(name="config", ok=False, detail=exc.message))
        return report

    database_path = resolve_database_path(root, config)
    if not database_path.is_file():
        report.checks.append(
            DoctorCheck(
                name="database",
                ok=False,
                detail=f"Missing database {database_path} — run `dce init`",
            )
        )
        return report

    report.checks.append(DoctorCheck(name="database", ok=True, detail=str(database_path)))

    try:
        with connect(database_path) as conn:
            fts_ok = is_fts5_available(conn)
            report.checks.append(
                DoctorCheck(
                    name="fts5",
                    ok=fts_ok,
                    detail="available" if fts_ok else "FTS5 not available in this SQLite",
                )
            )
            version = get_schema_version(conn)
            schema_ok = version == CURRENT_SCHEMA_VERSION
            detail = (
                f"version {version} (expected {CURRENT_SCHEMA_VERSION})"
                if schema_ok
                else (f"version {version}, expected {CURRENT_SCHEMA_VERSION} — run `dce init`")
            )
            report.checks.append(DoctorCheck(name="schema", ok=schema_ok, detail=detail))
            count_row = conn.execute("SELECT COUNT(*) AS n FROM documents").fetchone()
            doc_count = int(count_row["n"]) if count_row is not None else 0
            docs_detail = (
                f"{doc_count} indexed documents"
                if doc_count
                else "0 documents — run `dce index` before MCP use"
            )
            report.checks.append(
                DoctorCheck(name="documents", ok=True, detail=docs_detail)
            )
    except OSError as exc:
        report.checks.append(DoctorCheck(name="database", ok=False, detail=str(exc)))

    from dce.interfaces.mcp.contract import PRIMARY_TOOL, STABLE_TOOLS

    report.checks.append(
        DoctorCheck(
            name="mcp",
            ok=True,
            detail=f"{len(STABLE_TOOLS)} stable tools; prefer {PRIMARY_TOOL}",
        )
    )

    from dce.infrastructure.hooks import get_hook_status

    hook = get_hook_status(root)
    if hook.repo_root is not None:
        report.checks.append(
            DoctorCheck(name="git_hook", ok=True, detail=hook.detail)
        )

    return report


def budget_from_config(config: dict[str, Any]) -> ContextBudget:
    """Load ContextBudget from dce.yaml ``budget`` section."""
    raw = config.get("budget") or {}
    if not isinstance(raw, dict):
        return ContextBudget()
    return ContextBudget(
        max_documents=int(raw.get("max_documents", 20)),
        max_chars=int(raw.get("max_chars", 24_000)),
        max_per_source=int(raw.get("max_per_source", 5)),
    )


def synonyms_from_config(config: dict[str, Any]) -> dict[str, list[str]]:
    """Load optional synonym overrides from ``retrieval.synonyms``."""
    retrieval = config.get("retrieval") or {}
    if not isinstance(retrieval, dict):
        return {}
    raw = retrieval.get("synonyms") or {}
    if not isinstance(raw, dict):
        return {}
    result: dict[str, list[str]] = {}
    for key, value in raw.items():
        term = str(key).strip()
        if not term:
            continue
        if isinstance(value, str):
            items = [value]
        elif isinstance(value, list):
            items = [str(item) for item in value]
        else:
            continue
        cleaned = [item.strip() for item in items if str(item).strip()]
        if cleaned:
            result[term] = cleaned
    return result


def anchor_patterns_from_config(config: dict[str, Any]) -> list[AnchorPattern]:
    """Load optional extra anchor patterns from ``retrieval.anchors``."""
    retrieval = config.get("retrieval") or {}
    if not isinstance(retrieval, dict):
        return default_anchor_patterns()
    anchors_cfg = retrieval.get("anchors") or {}
    if not isinstance(anchors_cfg, dict):
        return default_anchor_patterns()
    raw_extras = anchors_cfg.get("extra_patterns") or []
    if not isinstance(raw_extras, list):
        return default_anchor_patterns()

    extras: list[AnchorPattern] = []
    for item in raw_extras:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        pattern = str(item.get("pattern") or "").strip()
        if not name or not pattern:
            continue
        try:
            extras.append(
                compile_anchor_pattern(
                    name=name,
                    regex=pattern,
                    kind=str(item.get("kind") or "general"),
                    case=item.get("case"),
                    ignore_case=bool(item.get("ignore_case", False)),
                )
            )
        except re.error:
            continue
    return default_anchor_patterns(extras)


def load_workspace(workspace_root: Path) -> tuple[Path, dict[str, Any], Path]:
    """Resolve workspace root, config, and database path.

    Raises WorkspaceError when config or database is missing.
    """
    root = workspace_root.resolve()
    config_path = root / DEFAULT_CONFIG_NAME
    config = load_config(config_path)
    database_path = resolve_database_path(root, config)
    if not database_path.is_file():
        msg = f"Missing database {database_path} — run `dce init`"
        raise WorkspaceError(msg)
    return root, config, database_path
