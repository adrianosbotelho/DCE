"""Local synthetic benchmarks for Context Builder latency (PB-091)."""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

from dce.application.build_context import build_context
from dce.application.slos import BenchReport, SloTargets, summarize_latencies
from dce.domain.models import ContextBudget, ContextQuery, Document, SearchSpec
from dce.infrastructure.storage.connection import connect
from dce.infrastructure.storage.migrations import apply_migrations
from dce.infrastructure.storage.repository import SqliteDocumentRepository


def seed_synthetic_documents(
    repository: SqliteDocumentRepository,
    *,
    count: int,
    error_code: str = "ORA-12541",
) -> int:
    """Upsert ``count`` synthetic documents (mix of hits and noise)."""
    total = max(1, count)
    documents: list[Document] = []
    for index in range(total):
        is_hit = index % 7 == 0
        body = (
            f"Runbook for {error_code}: check listener and tnsnames. entry={index}."
            if is_hit
            else f"Unrelated note about payments batch job #{index}."
        )
        documents.append(
            Document(
                id=f"bench-{index}",
                source_type="markdown" if not is_hit else "jira",
                uri=f"bench://doc/{index}",
                title=f"{'Listener' if is_hit else 'Noise'} {index}",
                body=body,
                tags=[error_code] if is_hit else ["noise"],
                project="bench",
            )
        )
    return repository.upsert_many(documents)


def _time_ms(fn: Callable[[], object]) -> float:
    started = time.perf_counter()
    fn()
    return (time.perf_counter() - started) * 1000.0


def run_benchmark(
    database_path: Path,
    *,
    document_count: int = 200,
    iterations: int = 20,
    query_text: str = "ORA-12541",
    force_seed: bool = True,
    slo: SloTargets | None = None,
) -> BenchReport:
    """Seed a synthetic corpus and measure build/search/get latencies."""
    targets = slo or SloTargets()
    iterations = max(1, iterations)
    document_count = max(1, document_count)
    notes: list[str] = [
        "Synthetic corpus — directional only vs Architecture 10k-doc SLO.",
        "CI should not hard-fail on within_slo (host variance).",
    ]

    with connect(database_path) as conn:
        apply_migrations(conn)
        repository = SqliteDocumentRepository(conn)
        if force_seed or not repository.list_recent(limit=1):
            seeded = seed_synthetic_documents(
                repository, count=document_count, error_code="ORA-12541"
            )
            notes.append(f"seeded {seeded} synthetic documents")
        else:
            notes.append("reusing existing database contents")

        build_samples: list[float] = []
        search_samples: list[float] = []
        get_samples: list[float] = []

        query = ContextQuery(
            text=query_text,
            budget=ContextBudget(max_documents=20, max_chars=24_000, max_per_source=5),
        )
        hits = repository.search(SearchSpec(text=query_text, limit=1))
        sample_id = hits[0].document.id if hits else "bench-0"

        for _ in range(iterations):
            build_samples.append(_time_ms(lambda: build_context(repository, query)))
            search_samples.append(
                _time_ms(lambda: repository.search(SearchSpec(text=query_text, limit=20)))
            )
            get_samples.append(_time_ms(lambda: repository.get(sample_id)))

        build_stats = summarize_latencies(build_samples)
        search_stats = summarize_latencies(search_samples)
        get_stats = summarize_latencies(get_samples)

        within = {
            "build_context": build_stats.p95_ms <= targets.build_context_ms,
            "search_context": search_stats.p95_ms <= targets.search_context_ms,
            "get_document": get_stats.p95_ms <= targets.get_document_ms,
        }

        return BenchReport(
            document_count=document_count,
            iterations=iterations,
            query_text=query_text,
            build_context=build_stats,
            search_context=search_stats,
            get_document=get_stats,
            slo=targets,
            within_slo=within,
            notes=notes,
        )


def prepare_bench_database(path: Path) -> Path:
    """Create parent dirs and return sqlite path for an ephemeral bench DB."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
