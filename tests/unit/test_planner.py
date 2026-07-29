"""Unit tests for retrieval planner."""

from __future__ import annotations

from dce.application.planner import (
    QueryKind,
    classify_query,
    detect_anchors,
    merge_anchors,
    plan_retrieval,
)
from dce.domain.models import ContextBudget, ContextQuery, SearchFilters


def test_detect_anchors_issue_ora_path() -> None:
    text = "See PROJ-4421 and ora-12541 in docs/runbook.md please"
    anchors = detect_anchors(text)
    assert "PROJ-4421" in anchors
    assert "ORA-12541" in anchors
    assert "docs/runbook.md" in anchors


def test_merge_anchors_dedupes_case() -> None:
    query = ContextQuery(text="ORA-12541 again", anchors=["ora-12541", "OTHER-1"])
    merged = merge_anchors(query)
    assert merged.count("ORA-12541") == 1
    assert "OTHER-1" in merged


def test_classify_query_kinds() -> None:
    assert classify_query(ContextQuery(text="fix ORA-12541")) == QueryKind.ERROR_CODE
    assert classify_query(ContextQuery(text="status of PAY-12")) == QueryKind.ISSUE
    assert classify_query(ContextQuery(text="por que usamos SQLite?")) == QueryKind.ARCHITECTURE
    assert classify_query(ContextQuery(text="who touched src/app.py")) == QueryKind.PATH
    assert classify_query(ContextQuery(text="hello world")) == QueryKind.GENERAL


def test_plan_includes_preferred_sources_for_errors() -> None:
    plan = plan_retrieval(ContextQuery(text="fix ORA-12541 listener"))
    assert plan.query_kind == QueryKind.ERROR_CODE
    assert "jira" in plan.preferred_sources
    labels = [step.label for step in plan.steps]
    assert any(label.startswith("anchor:ORA-12541") for label in labels)
    assert any(label.startswith("preferred:jira") for label in labels)
    assert "full_text" in labels


def test_plan_respects_user_source_filter() -> None:
    plan = plan_retrieval(
        ContextQuery(
            text="ORA-12541",
            filters=SearchFilters(source_types=["markdown"]),
        )
    )
    assert plan.preferred_sources == []
    assert all(not step.label.startswith("preferred:") for step in plan.steps)
    assert any("respecting user source_types" in note for note in plan.notes)


def test_plan_architecture_prefers_adr() -> None:
    plan = plan_retrieval(ContextQuery(text="por que usamos SQLite no DCE?"))
    assert plan.query_kind == QueryKind.ARCHITECTURE
    assert plan.preferred_sources[0] == "adr"
    assert any(step.label == "preferred:adr" for step in plan.steps)


def test_plan_empty_query_recent_fallback() -> None:
    plan = plan_retrieval(ContextQuery(text="", budget=ContextBudget(max_documents=5)))
    assert plan.steps[0].label == "recent_fallback"
    assert plan.steps[0].limit == 5


def test_plan_includes_synonym_steps() -> None:
    plan = plan_retrieval(ContextQuery(text="fix ORA-12541"))
    assert "ORA-12541" in plan.synonym_expansions
    labels = [step.label for step in plan.steps]
    assert any(label.startswith("synonym:ORA-12541->") for label in labels)
    assert any("synonym expansions:" in note for note in plan.notes)


def test_plan_custom_synonym_dictionary() -> None:
    plan = plan_retrieval(
        ContextQuery(text="kubernetes rollout"),
        synonym_dictionary={"kubernetes": ["k8s-cluster"]},
    )
    assert plan.synonym_expansions["kubernetes"] == ["k8s-cluster"]
    assert any(step.label == "synonym:kubernetes->k8s-cluster" for step in plan.steps)


def test_plan_notes_custom_anchor_patterns() -> None:
    from dce.application.anchors import compile_anchor_pattern, default_anchor_patterns

    patterns = default_anchor_patterns(
        [
            compile_anchor_pattern(
                name="ticket",
                regex=r"\b(TCK-\d+)\b",
                kind="issue",
                case="upper",
            )
        ]
    )
    plan = plan_retrieval(ContextQuery(text="status of TCK-7"), anchor_patterns=patterns)
    assert plan.query_kind == QueryKind.ISSUE
    assert "TCK-7" in plan.anchors
