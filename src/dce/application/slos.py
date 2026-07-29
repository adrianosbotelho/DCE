"""SLO targets and latency statistics for local benchmarks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Documented targets for a representative local SSD index (~thousands of docs).
# Synthetic benches use a smaller corpus; treat results as directional.
SLO_BUILD_CONTEXT_P95_MS = 500.0
SLO_SEARCH_CONTEXT_P95_MS = 200.0
SLO_GET_DOCUMENT_P95_MS = 50.0


@dataclass(frozen=True)
class SloTargets:
    """p95 latency budgets in milliseconds."""

    build_context_ms: float = SLO_BUILD_CONTEXT_P95_MS
    search_context_ms: float = SLO_SEARCH_CONTEXT_P95_MS
    get_document_ms: float = SLO_GET_DOCUMENT_P95_MS

    def as_dict(self) -> dict[str, float]:
        return {
            "build_context_p95_ms": self.build_context_ms,
            "search_context_p95_ms": self.search_context_ms,
            "get_document_p95_ms": self.get_document_ms,
        }


@dataclass(frozen=True)
class LatencyStats:
    """Summary of repeated latency samples (milliseconds)."""

    samples_ms: tuple[float, ...]
    p50_ms: float
    p95_ms: float
    p99_ms: float
    max_ms: float
    mean_ms: float

    @property
    def n(self) -> int:
        return len(self.samples_ms)

    def as_dict(self) -> dict[str, Any]:
        return {
            "n": self.n,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
            "max_ms": self.max_ms,
            "mean_ms": self.mean_ms,
        }


def percentile(samples: list[float], pct: float) -> float:
    """Nearest-rank percentile for ``pct`` in 0..100."""
    if not samples:
        return 0.0
    if pct <= 0:
        return min(samples)
    if pct >= 100:
        return max(samples)
    ordered = sorted(samples)
    rank = max(1, round((pct / 100.0) * len(ordered)))
    return ordered[min(rank, len(ordered)) - 1]


def summarize_latencies(samples_ms: list[float]) -> LatencyStats:
    """Compute common latency percentiles from millisecond samples."""
    cleaned = [max(0.0, float(value)) for value in samples_ms]
    if not cleaned:
        return LatencyStats(
            samples_ms=(),
            p50_ms=0.0,
            p95_ms=0.0,
            p99_ms=0.0,
            max_ms=0.0,
            mean_ms=0.0,
        )
    return LatencyStats(
        samples_ms=tuple(cleaned),
        p50_ms=percentile(cleaned, 50),
        p95_ms=percentile(cleaned, 95),
        p99_ms=percentile(cleaned, 99),
        max_ms=max(cleaned),
        mean_ms=sum(cleaned) / len(cleaned),
    )


@dataclass
class BenchReport:
    """Structured benchmark result (CLI/MCP-friendly JSON)."""

    schema_version: str = "1"
    document_count: int = 0
    iterations: int = 0
    query_text: str = "ORA-12541"
    build_context: LatencyStats = field(default_factory=lambda: summarize_latencies([]))
    search_context: LatencyStats = field(default_factory=lambda: summarize_latencies([]))
    get_document: LatencyStats = field(default_factory=lambda: summarize_latencies([]))
    slo: SloTargets = field(default_factory=SloTargets)
    within_slo: dict[str, bool] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "document_count": self.document_count,
            "iterations": self.iterations,
            "query_text": self.query_text,
            "build_context": self.build_context.as_dict(),
            "search_context": self.search_context.as_dict(),
            "get_document": self.get_document.as_dict(),
            "slo": self.slo.as_dict(),
            "within_slo": dict(self.within_slo),
            "notes": list(self.notes),
        }
