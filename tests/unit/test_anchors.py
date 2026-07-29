"""Unit tests for configurable anchor patterns (PB-034)."""

from __future__ import annotations

from dce.application.anchors import (
    AnchorKind,
    builtin_anchor_patterns,
    compile_anchor_pattern,
    default_anchor_patterns,
    detect_anchors_with_patterns,
    merge_anchor_patterns,
)
from dce.application.planner import QueryKind, classify_query, detect_anchors, plan_retrieval
from dce.domain.models import ContextQuery
from dce.infrastructure.storage.workspace import anchor_patterns_from_config


def test_builtin_detects_issue_ora_path() -> None:
    anchors = detect_anchors("See PROJ-4421 and ora-12541 in docs/runbook.md")
    assert "PROJ-4421" in anchors
    assert "ORA-12541" in anchors
    assert "docs/runbook.md" in anchors


def test_extra_pattern_detects_err_codes() -> None:
    extras = [
        compile_anchor_pattern(
            name="err_code",
            regex=r"\b(ERR-\d{4})\b",
            kind="error_code",
            case="upper",
        )
    ]
    patterns = default_anchor_patterns(extras)
    detected = detect_anchors_with_patterns("failure ERR-0042 in batch", patterns)
    assert any(item.value == "ERR-0042" and item.kind is AnchorKind.ERROR_CODE for item in detected)


def test_extra_pattern_replaces_builtin_by_name() -> None:
    replacement = compile_anchor_pattern(
        name="ora",
        regex=r"\b(ORA-\d{5})\b",
        kind="error_code",
        case="upper",
        ignore_case=True,
    )
    patterns = merge_anchor_patterns(builtin_anchor_patterns(), [replacement])
    assert detect_anchors("ORA-1254", patterns=patterns) == []  # 4 digits no longer match
    assert detect_anchors("ORA-12541", patterns=patterns) == ["ORA-12541"]


def test_plan_uses_custom_anchor_as_error_kind() -> None:
    patterns = default_anchor_patterns(
        [
            compile_anchor_pattern(
                name="err_code",
                regex=r"\b(ERR-\d{4})\b",
                kind="error_code",
                case="upper",
            )
        ]
    )
    plan = plan_retrieval(
        ContextQuery(text="investigate ERR-0099 tonight"),
        anchor_patterns=patterns,
    )
    assert plan.query_kind == QueryKind.ERROR_CODE
    assert "ERR-0099" in plan.anchors
    assert any(step.label == "anchor:ERR-0099" for step in plan.steps)
    assert any("custom anchor patterns: err_code" in note for note in plan.notes)


def test_anchor_patterns_from_config() -> None:
    patterns = anchor_patterns_from_config(
        {
            "retrieval": {
                "anchors": {
                    "extra_patterns": [
                        {
                            "name": "http_status",
                            "pattern": r"\bHTTP/?(5\d{2})\b",
                            "kind": "error_code",
                            "case": "upper",
                            "ignore_case": True,
                        },
                        {"name": "bad", "pattern": "(unterminated"},
                    ]
                }
            }
        }
    )
    names = {pattern.name for pattern in patterns}
    assert "http_status" in names
    assert "issue" in names
    detected = detect_anchors_with_patterns("got HTTP/503 from gateway", patterns)
    assert detected[0].value == "503"
    kind = classify_query(ContextQuery(text="got HTTP/503"), patterns=patterns)
    assert kind == QueryKind.ERROR_CODE
