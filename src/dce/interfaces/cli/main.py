"""Typer CLI entrypoint for DCE."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.table import Table

from dce import __version__
from dce.application.build_context import build_context
from dce.application.indexing import run_indexing
from dce.domain.errors import StorageError, WorkspaceError
from dce.domain.models import ContextQuery, SearchFilters, SearchSpec
from dce.infrastructure.hooks import (
    get_hook_status,
    install_post_commit_hook,
    uninstall_post_commit_hook,
)
from dce.infrastructure.indexers.registry import build_default_indexers
from dce.infrastructure.logging import configure_logging, resolve_log_format
from dce.infrastructure.storage.backup import backup_database, restore_database
from dce.infrastructure.storage.connection import connect
from dce.infrastructure.storage.repository import SqliteDocumentRepository
from dce.infrastructure.storage.workspace import (
    anchor_patterns_from_config,
    budget_from_config,
    doctor_workspace,
    init_workspace,
    load_workspace,
    synonyms_from_config,
)

app = typer.Typer(
    name="dce",
    help="Dev Context Engine — offline context builder for AI coding agents.",
    no_args_is_help=True,
)
console = Console()
err_console = Console(stderr=True)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"dce {__version__}")
        raise typer.Exit(0)


def _print_json(payload: Any) -> None:
    console.print_json(json.dumps(payload, ensure_ascii=False, default=str))


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-V",
            callback=_version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable DEBUG logs on stderr (or set DCE_LOG_LEVEL).",
        ),
    ] = False,
    log_format: Annotated[
        str,
        typer.Option(
            "--log-format",
            help="Log format: text|json (or DCE_LOG_FORMAT). Always on stderr.",
        ),
    ] = "text",
) -> None:
    """Dev Context Engine CLI."""
    fmt = resolve_log_format(log_format=log_format)
    configure_logging(verbose=verbose, log_format=fmt, force=True)


@app.command("init")
def init_cmd(
    path: Annotated[
        Path,
        typer.Argument(help="Workspace directory (created if missing)."),
    ] = Path("."),
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="Workspace name written to dce.yaml."),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite dce.yaml with the skeleton."),
    ] = False,
) -> None:
    """Create dce.yaml and a migrated SQLite database."""
    try:
        result = init_workspace(path, name=name, force=force)
    except WorkspaceError as exc:
        err_console.print(f"[red]error:[/red] {exc.message}")
        raise typer.Exit(code=1) from exc
    except RuntimeError as exc:
        err_console.print(f"[red]error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    config_state = "created" if result.created_config else "reused"
    db_state = "created" if result.created_database else "migrated"
    console.print(f"[green]ok[/green] workspace {result.workspace_root}")
    console.print(f"  config:   {result.config_path} ({config_state})")
    console.print(f"  database: {result.database_path} ({db_state})")
    console.print(f"  schema:   v{result.schema_version}")


@app.command("doctor")
def doctor_cmd(
    path: Annotated[
        Path,
        typer.Argument(help="Workspace directory containing dce.yaml."),
    ] = Path("."),
) -> None:
    """Check config, database, schema, FTS5, index size, MCP readiness, git hook."""
    report = doctor_workspace(path)
    table = Table(title="dce doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")
    for check in report.checks:
        status = "[green]ok[/green]" if check.ok else "[red]fail[/red]"
        table.add_row(check.name, status, check.detail)
    console.print(table)
    if not report.healthy:
        raise typer.Exit(code=1)


hooks_app = typer.Typer(help="Optional git hooks (post-commit index).")
app.add_typer(hooks_app, name="hooks")


@hooks_app.command("status")
def hooks_status_cmd(
    path: Annotated[
        Path,
        typer.Argument(help="Workspace directory (git root)."),
    ] = Path("."),
) -> None:
    """Show whether the managed post-commit hook is installed."""
    status = get_hook_status(path)
    console.print(f"hook: {status.detail}")
    if status.hook_path is not None:
        console.print(f"path: {status.hook_path}")


@hooks_app.command("install")
def hooks_install_cmd(
    path: Annotated[
        Path,
        typer.Argument(help="Workspace directory (git root)."),
    ] = Path("."),
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite a foreign post-commit hook."),
    ] = False,
) -> None:
    """Install a soft-fail post-commit hook that runs ``dce index --source git``."""
    try:
        hook_path = install_post_commit_hook(path, force=force)
    except WorkspaceError as exc:
        err_console.print(f"[red]error:[/red] {exc.message}")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]ok[/green] installed {hook_path}")


@hooks_app.command("uninstall")
def hooks_uninstall_cmd(
    path: Annotated[
        Path,
        typer.Argument(help="Workspace directory (git root)."),
    ] = Path("."),
    force: Annotated[
        bool,
        typer.Option("--force", help="Remove even if the hook is not dce-managed."),
    ] = False,
) -> None:
    """Remove the managed post-commit hook."""
    try:
        removed = uninstall_post_commit_hook(path, force=force)
    except WorkspaceError as exc:
        err_console.print(f"[red]error:[/red] {exc.message}")
        raise typer.Exit(code=1) from exc
    if removed is None:
        console.print("nothing to uninstall")
        return
    console.print(f"[green]ok[/green] removed {removed}")


@app.command("index")
def index_cmd(
    path: Annotated[
        Path,
        typer.Argument(help="Workspace directory containing dce.yaml."),
    ] = Path("."),
    source: Annotated[
        str | None,
        typer.Option(
            "--source",
            "-s",
            help="Run a single indexer (e.g. markdown, md). Ignores enabled flags.",
        ),
    ] = None,
) -> None:
    """Index configured sources into the local SQLite store."""
    try:
        root, config, database_path = load_workspace(path)
    except WorkspaceError as exc:
        err_console.print(f"[red]error:[/red] {exc.message}")
        raise typer.Exit(code=1) from exc

    indexers_config = config.get("indexers") or {}
    if not isinstance(indexers_config, dict):
        err_console.print("[red]error:[/red] indexers config must be a mapping")
        raise typer.Exit(code=1)

    indexers = build_default_indexers(root)

    with connect(database_path) as conn:
        repository = SqliteDocumentRepository(conn)
        result = run_indexing(
            repository,
            indexers,
            indexers_config,
            only_source=source,
        )

    table = Table(title="dce index")
    table.add_column("Indexer")
    table.add_column("Discovered")
    table.add_column("Upserted")
    table.add_column("Detail")
    for run in result.runs:
        table.add_row(
            run.name,
            str(run.discovered),
            str(run.upserted),
            run.detail if not run.skipped else f"skipped ({run.detail})",
        )
    console.print(table)
    console.print(f"[green]ok[/green] total upserted: {result.total_upserted}")
    if result.related_uris_linked:
        console.print(f"related_uris linked: {result.related_uris_linked}")

    if source and all(run.skipped for run in result.runs):
        raise typer.Exit(code=1)


def _filters_from_options(
    *,
    project: str | None,
    component: str | None,
    technology: str | None,
    tag: list[str] | None,
    source_type: list[str] | None,
) -> SearchFilters:
    return SearchFilters(
        project=project,
        component=component,
        technology=technology,
        tags=list(tag or []),
        source_types=list(source_type or []),
    )


@app.command("build")
def build_cmd(
    query: Annotated[str, typer.Argument(help="Question or search text for context.")],
    path: Annotated[
        Path,
        typer.Option("--path", "-p", help="Workspace directory."),
    ] = Path("."),
    project: Annotated[str | None, typer.Option(help="Filter by project.")] = None,
    component: Annotated[str | None, typer.Option(help="Filter by component.")] = None,
    technology: Annotated[str | None, typer.Option(help="Filter by technology.")] = None,
    tag: Annotated[
        list[str] | None,
        typer.Option(help="Filter by tag (repeatable)."),
    ] = None,
    source_type: Annotated[
        list[str] | None,
        typer.Option("--source-type", help="Filter by source_type (repeatable)."),
    ] = None,
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: json|table."),
    ] = "json",
) -> None:
    """Build a structured ContextPackage (product core)."""
    try:
        _root, config, database_path = load_workspace(path)
    except WorkspaceError as exc:
        err_console.print(f"[red]error:[/red] {exc.message}")
        raise typer.Exit(code=1) from exc

    context_query = ContextQuery(
        text=query,
        filters=_filters_from_options(
            project=project,
            component=component,
            technology=technology,
            tag=tag,
            source_type=source_type,
        ),
        budget=budget_from_config(config),
    )

    with connect(database_path) as conn:
        repository = SqliteDocumentRepository(conn)
        package = build_context(
            repository,
            context_query,
            synonym_dictionary=synonyms_from_config(config),
            anchor_patterns=anchor_patterns_from_config(config),
        )

    fmt = format.lower().strip()
    if fmt == "json":
        _print_json(package.model_dump(mode="json"))
        return
    if fmt == "table":
        table = Table(title="dce build")
        table.add_column("Score")
        table.add_column("Source")
        table.add_column("Title")
        table.add_column("URI")
        for item in package.documents:
            table.add_row(
                f"{item.score:.2f}",
                item.document.source_type,
                item.document.title[:60],
                item.document.uri,
            )
        console.print(table)
        diag = package.diagnostics
        console.print(
            f"docs={len(package.documents)} truncated={diag.truncated} "
            f"elapsed_ms={diag.elapsed_ms:.1f} "
            f"query_kind={diag.query_kind or '-'} "
            f"steps={len(diag.steps)}"
        )
        if diag.synonym_expansions:
            console.print(f"synonyms={diag.synonym_expansions}")
        return

    err_console.print("[red]error:[/red] --format must be json or table")
    raise typer.Exit(code=1)


@app.command("search")
def search_cmd(
    query: Annotated[str, typer.Argument(help="Full-text query.")],
    path: Annotated[
        Path,
        typer.Option("--path", "-p", help="Workspace directory."),
    ] = Path("."),
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max results.")] = 20,
    project: Annotated[str | None, typer.Option(help="Filter by project.")] = None,
    component: Annotated[str | None, typer.Option(help="Filter by component.")] = None,
    technology: Annotated[str | None, typer.Option(help="Filter by technology.")] = None,
    tag: Annotated[
        list[str] | None,
        typer.Option(help="Filter by tag (repeatable)."),
    ] = None,
    source_type: Annotated[
        list[str] | None,
        typer.Option("--source-type", help="Filter by source_type (repeatable)."),
    ] = None,
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: json|table."),
    ] = "json",
) -> None:
    """Search the index and return ranked documents."""
    try:
        _root, _config, database_path = load_workspace(path)
    except WorkspaceError as exc:
        err_console.print(f"[red]error:[/red] {exc.message}")
        raise typer.Exit(code=1) from exc

    spec = SearchSpec(
        text=query,
        filters=_filters_from_options(
            project=project,
            component=component,
            technology=technology,
            tag=tag,
            source_type=source_type,
        ),
        limit=max(1, min(limit, 500)),
    )

    with connect(database_path) as conn:
        repository = SqliteDocumentRepository(conn)
        hits = repository.search(spec)

    fmt = format.lower().strip()
    if fmt == "json":
        _print_json([hit.model_dump(mode="json") for hit in hits])
        return
    if fmt == "table":
        table = Table(title="dce search")
        table.add_column("Score")
        table.add_column("Source")
        table.add_column("Title")
        table.add_column("URI")
        for item in hits:
            table.add_row(
                f"{item.score:.2f}",
                item.document.source_type,
                item.document.title[:60],
                item.document.uri,
            )
        console.print(table)
        return

    err_console.print("[red]error:[/red] --format must be json or table")
    raise typer.Exit(code=1)


@app.command("show")
def show_cmd(
    document_id: Annotated[str, typer.Argument(help="Document id.")],
    path: Annotated[
        Path,
        typer.Option("--path", "-p", help="Workspace directory."),
    ] = Path("."),
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: json|table."),
    ] = "json",
) -> None:
    """Show a single document by id."""
    try:
        _root, _config, database_path = load_workspace(path)
    except WorkspaceError as exc:
        err_console.print(f"[red]error:[/red] {exc.message}")
        raise typer.Exit(code=1) from exc

    with connect(database_path) as conn:
        repository = SqliteDocumentRepository(conn)
        document = repository.get(document_id)

    if document is None:
        err_console.print(f"[red]error:[/red] document not found: {document_id}")
        raise typer.Exit(code=1)

    fmt = format.lower().strip()
    if fmt == "json":
        _print_json(document.model_dump(mode="json"))
        return
    if fmt == "table":
        console.print(f"[bold]{document.title}[/bold] ({document.source_type})")
        console.print(f"id:  {document.id}")
        console.print(f"uri: {document.uri}")
        console.print(document.body[:2000])
        return

    err_console.print("[red]error:[/red] --format must be json or table")
    raise typer.Exit(code=1)


@app.command("bench")
def bench_cmd(
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Workspace directory (DB used only with --workspace).",
        ),
    ] = Path("."),
    docs: Annotated[
        int,
        typer.Option("--docs", help="Synthetic documents to seed."),
    ] = 200,
    iterations: Annotated[
        int,
        typer.Option("--iterations", "-n", help="Samples per operation."),
    ] = 20,
    query: Annotated[
        str,
        typer.Option("--query", "-q", help="Benchmark query text."),
    ] = "ORA-12541",
    ephemeral: Annotated[
        bool,
        typer.Option(
            "--ephemeral/--workspace",
            help="Ephemeral temp DB (default) or reuse workspace database.",
        ),
    ] = True,
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: json|table."),
    ] = "json",
) -> None:
    """Measure local build/search/get latency against documented SLOs."""
    from dce.application.benchmarks import prepare_bench_database, run_benchmark

    if ephemeral:
        database_path = prepare_bench_database(path.resolve() / ".dce" / "bench.sqlite")
        if database_path.exists():
            database_path.unlink()
    else:
        try:
            _root, _config, database_path = load_workspace(path)
        except WorkspaceError as exc:
            err_console.print(f"[red]error:[/red] {exc.message}")
            raise typer.Exit(code=1) from exc

    report = run_benchmark(
        database_path,
        document_count=docs,
        iterations=iterations,
        query_text=query,
        force_seed=ephemeral,
    )

    fmt = format.lower().strip()
    if fmt == "json":
        _print_json(report.as_dict())
        return
    if fmt == "table":
        table = Table(title="dce bench")
        table.add_column("Op")
        table.add_column("p50 ms")
        table.add_column("p95 ms")
        table.add_column("SLO p95")
        table.add_column("OK")
        rows = [
            (
                "build_context",
                report.build_context,
                report.slo.build_context_ms,
                report.within_slo.get("build_context"),
            ),
            (
                "search_context",
                report.search_context,
                report.slo.search_context_ms,
                report.within_slo.get("search_context"),
            ),
            (
                "get_document",
                report.get_document,
                report.slo.get_document_ms,
                report.within_slo.get("get_document"),
            ),
        ]
        for name, stats, target, ok in rows:
            table.add_row(
                name,
                f"{stats.p50_ms:.2f}",
                f"{stats.p95_ms:.2f}",
                f"{target:.0f}",
                "yes" if ok else "no",
            )
        console.print(table)
        console.print(f"docs={report.document_count} iterations={report.iterations}")
        return

    err_console.print("[red]error:[/red] --format must be json or table")
    raise typer.Exit(code=1)


@app.command("backup")
def backup_cmd(
    path: Annotated[
        Path,
        typer.Option("--path", "-p", help="Workspace directory."),
    ] = Path("."),
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Destination .sqlite backup file."),
    ] = Path("dce-backup.sqlite"),
    manifest: Annotated[
        bool,
        typer.Option("--manifest/--no-manifest", help="Write JSON manifest sidecar."),
    ] = True,
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: json|text."),
    ] = "json",
) -> None:
    """Create a WAL-safe snapshot of the workspace SQLite database."""
    try:
        _root, _config, database_path = load_workspace(path)
        result = backup_database(
            database_path,
            output,
            write_manifest=manifest,
        )
    except (WorkspaceError, StorageError) as exc:
        err_console.print(f"[red]error:[/red] {exc.message}")
        raise typer.Exit(code=1) from exc

    fmt = format.lower().strip()
    if fmt == "json":
        _print_json(result.as_dict())
        return
    if fmt == "text":
        console.print(f"backup: {result.backup_path}")
        console.print(f"bytes:  {result.bytes_written}")
        console.print(f"schema: v{result.schema_version}")
        if result.manifest_path:
            console.print(f"manifest: {result.manifest_path}")
        return

    err_console.print("[red]error:[/red] --format must be json or text")
    raise typer.Exit(code=1)


@app.command("restore")
def restore_cmd(
    input: Annotated[
        Path,
        typer.Option("--input", "-i", help="Backup .sqlite file to restore."),
    ],
    path: Annotated[
        Path,
        typer.Option("--path", "-p", help="Workspace directory."),
    ] = Path("."),
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite existing database."),
    ] = False,
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: json|text."),
    ] = "json",
) -> None:
    """Restore a SQLite backup into the workspace database path."""
    from dce.infrastructure.storage.workspace import (
        DEFAULT_CONFIG_NAME,
        load_config,
        resolve_database_path,
    )

    root = path.resolve()
    try:
        config = load_config(root / DEFAULT_CONFIG_NAME)
        database_path = resolve_database_path(root, config)
    except WorkspaceError as exc:
        err_console.print(f"[red]error:[/red] {exc.message}")
        raise typer.Exit(code=1) from exc

    try:
        result = restore_database(input, database_path, force=force)
    except (WorkspaceError, StorageError) as exc:
        err_console.print(f"[red]error:[/red] {exc.message}")
        raise typer.Exit(code=1) from exc

    fmt = format.lower().strip()
    if fmt == "json":
        _print_json(result.as_dict())
        return
    if fmt == "text":
        console.print(f"restored: {result.destination_path}")
        console.print(f"bytes:    {result.bytes_restored}")
        console.print(f"schema:   v{result.schema_version}")
        return

    err_console.print("[red]error:[/red] --format must be json or text")
    raise typer.Exit(code=1)


@app.command("mcp")
def mcp_cmd(
    path: Annotated[
        Path,
        typer.Option("--path", "-p", help="Workspace directory containing dce.yaml."),
    ] = Path("."),
) -> None:
    """Start MCP stdio server for Kiro (do not print to stdout)."""
    # Re-assert stderr-only logging for MCP transport safety.
    configure_logging(verbose=False, log_format=resolve_log_format(), force=True)
    try:
        load_workspace(path)
    except WorkspaceError as exc:
        err_console.print(f"[red]error:[/red] {exc.message}")
        raise typer.Exit(code=1) from exc

    from dce.interfaces.mcp.server import run_mcp_stdio

    run_mcp_stdio(path)


if __name__ == "__main__":
    app()
