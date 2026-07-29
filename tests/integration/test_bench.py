"""Benchmark harness tests (PB-091)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from dce.application.benchmarks import prepare_bench_database, run_benchmark
from dce.interfaces.cli.main import app

runner = CliRunner()


def test_run_benchmark_synthetic(tmp_path: Path) -> None:
    db = prepare_bench_database(tmp_path / "bench.sqlite")
    report = run_benchmark(
        db,
        document_count=40,
        iterations=5,
        query_text="ORA-12541",
        force_seed=True,
    )
    assert report.schema_version == "1"
    assert report.iterations == 5
    assert report.document_count == 40
    assert report.build_context.p95_ms >= 0.0
    assert report.search_context.n == 5
    assert report.get_document.n == 5
    assert set(report.within_slo) == {
        "build_context",
        "search_context",
        "get_document",
    }
    assert "slo" in report.as_dict()


def test_cli_bench_json(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "bench",
            "--path",
            str(tmp_path),
            "--docs",
            "30",
            "--iterations",
            "3",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0, result.output
    assert '"schema_version": "1"' in result.output
    assert "build_context" in result.output
