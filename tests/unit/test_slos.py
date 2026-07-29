"""Unit tests for SLO stats helpers."""

from __future__ import annotations

from dce.application.slos import (
    SLO_BUILD_CONTEXT_P95_MS,
    SloTargets,
    percentile,
    summarize_latencies,
)


def test_percentile_empty_and_edges() -> None:
    assert percentile([], 95) == 0.0
    assert percentile([10.0], 50) == 10.0
    assert percentile([1.0, 2.0, 3.0, 4.0], 0) == 1.0
    assert percentile([1.0, 2.0, 3.0, 4.0], 100) == 4.0


def test_summarize_latencies() -> None:
    stats = summarize_latencies([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    assert stats.p50_ms == 50.0
    assert stats.p95_ms >= stats.p50_ms
    assert stats.max_ms == 100.0
    assert stats.mean_ms == 55.0


def test_slo_targets_defaults() -> None:
    targets = SloTargets()
    assert targets.build_context_ms == SLO_BUILD_CONTEXT_P95_MS
    payload = targets.as_dict()
    assert payload["build_context_p95_ms"] == 500.0
