"""Configurable anchor pattern dictionary for retrieval (offline, rules-only)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from re import Pattern


class AnchorKind(StrEnum):
    """Retrieval bias implied by a matched anchor pattern."""

    ERROR_CODE = "error_code"
    ISSUE = "issue"
    PATH = "path"
    ARCHITECTURE = "architecture"
    GENERAL = "general"


class AnchorCase(StrEnum):
    """How to normalize a matched anchor value."""

    UPPER = "upper"
    LOWER = "lower"
    PRESERVE = "preserve"


@dataclass(frozen=True)
class AnchorPattern:
    """One named regex used to extract strong identifiers."""

    name: str
    pattern: Pattern[str]
    kind: AnchorKind
    case: AnchorCase = AnchorCase.PRESERVE


@dataclass(frozen=True)
class DetectedAnchor:
    """An anchor value with the kind implied by its pattern."""

    value: str
    kind: AnchorKind
    pattern_name: str


_BUILTIN_SPECS: tuple[tuple[str, str, AnchorKind, AnchorCase, int], ...] = (
    # Error codes before issue keys so values like ORA-12541 are not classified as issues.
    ("ora", r"\b(ORA-\d{3,5})\b", AnchorKind.ERROR_CODE, AnchorCase.UPPER, re.IGNORECASE),
    (
        "issue",
        r"\b(?!ORA-)([A-Z][A-Z0-9]+-\d+)\b",
        AnchorKind.ISSUE,
        AnchorCase.UPPER,
        0,
    ),
    (
        "path",
        r"\b([\w./-]+\.(?:md|py|ts|tsx|js|java|go|sql|yml|yaml))\b",
        AnchorKind.PATH,
        AnchorCase.PRESERVE,
        0,
    ),
)


def normalize_anchor_value(value: str, case: AnchorCase) -> str:
    """Apply case normalization to a matched anchor."""
    if case is AnchorCase.UPPER:
        return value.upper()
    if case is AnchorCase.LOWER:
        return value.lower()
    return value


def _normalize_value(value: str, case: AnchorCase) -> str:
    return normalize_anchor_value(value, case)


def _parse_kind(raw: str) -> AnchorKind:
    cleaned = raw.strip().lower()
    try:
        return AnchorKind(cleaned)
    except ValueError:
        return AnchorKind.GENERAL


def _parse_case(raw: str | None) -> AnchorCase:
    if not raw:
        return AnchorCase.PRESERVE
    cleaned = str(raw).strip().lower()
    try:
        return AnchorCase(cleaned)
    except ValueError:
        return AnchorCase.PRESERVE


def compile_anchor_pattern(
    *,
    name: str,
    regex: str,
    kind: AnchorKind | str = AnchorKind.GENERAL,
    case: AnchorCase | str | None = AnchorCase.PRESERVE,
    ignore_case: bool = False,
) -> AnchorPattern:
    """Compile a single anchor pattern; raises ``re.error`` on bad regex."""
    resolved_kind = kind if isinstance(kind, AnchorKind) else _parse_kind(str(kind))
    resolved_case = case if isinstance(case, AnchorCase) else _parse_case(case)
    flags = re.IGNORECASE if ignore_case else 0
    return AnchorPattern(
        name=name.strip() or "custom",
        pattern=re.compile(regex, flags),
        kind=resolved_kind,
        case=resolved_case,
    )


def builtin_anchor_patterns() -> list[AnchorPattern]:
    """Return the built-in issue / ORA / path detectors."""
    return [
        AnchorPattern(
            name=name,
            pattern=re.compile(regex, flags),
            kind=kind,
            case=case,
        )
        for name, regex, kind, case, flags in _BUILTIN_SPECS
    ]


def merge_anchor_patterns(
    builtins: Sequence[AnchorPattern],
    extras: Sequence[AnchorPattern],
) -> list[AnchorPattern]:
    """Merge patterns; extras with the same ``name`` replace builtins."""
    by_name = {pattern.name: pattern for pattern in builtins}
    for pattern in extras:
        by_name[pattern.name] = pattern
    ordered: list[AnchorPattern] = []
    seen: set[str] = set()
    for pattern in builtins:
        current = by_name[pattern.name]
        ordered.append(current)
        seen.add(current.name)
    for pattern in extras:
        if pattern.name not in seen:
            ordered.append(pattern)
            seen.add(pattern.name)
    return ordered


def default_anchor_patterns(
    extras: Sequence[AnchorPattern] | None = None,
) -> list[AnchorPattern]:
    """Built-ins merged with optional workspace extras."""
    return merge_anchor_patterns(builtin_anchor_patterns(), list(extras or ()))


def detect_anchors_with_patterns(
    text: str,
    patterns: Sequence[AnchorPattern],
) -> list[DetectedAnchor]:
    """Extract anchors using the provided pattern dictionary.

    If multiple patterns match the same value, the strongest ``kind`` wins
    (error_code > issue > path > architecture > general).
    """
    rank = {
        AnchorKind.ERROR_CODE: 0,
        AnchorKind.ISSUE: 1,
        AnchorKind.PATH: 2,
        AnchorKind.ARCHITECTURE: 3,
        AnchorKind.GENERAL: 4,
    }
    by_key: dict[str, DetectedAnchor] = {}
    order: list[str] = []
    for pattern in patterns:
        for match in pattern.pattern.finditer(text):
            raw = match.group(1) if match.lastindex else match.group(0)
            value = _normalize_value(str(raw).strip(), pattern.case)
            if not value:
                continue
            key = value.lower()
            candidate = DetectedAnchor(
                value=value,
                kind=pattern.kind,
                pattern_name=pattern.name,
            )
            existing = by_key.get(key)
            if existing is None:
                by_key[key] = candidate
                order.append(key)
                continue
            if rank[candidate.kind] < rank[existing.kind]:
                by_key[key] = candidate
    return [by_key[key] for key in order]


def classify_from_anchors(detected: Sequence[DetectedAnchor]) -> AnchorKind | None:
    """Return the strongest kind implied by detected anchors, if any."""
    priority = (
        AnchorKind.ERROR_CODE,
        AnchorKind.ISSUE,
        AnchorKind.PATH,
        AnchorKind.ARCHITECTURE,
    )
    kinds = {item.kind for item in detected}
    for kind in priority:
        if kind in kinds:
            return kind
    return None
