"""Technical synonym expansion for retrieval (offline, rules-only)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

# Lowercase keys. Values are alternate search phrases.
BUILTIN_SYNONYMS: dict[str, tuple[str, ...]] = {
    "ora-12541": ("tns", "listener", "no listener", "tns listener"),
    "ora-12154": ("tns", "could not resolve", "tnsnames"),
    "ora-12514": ("listener does not know", "service name"),
    "ora-00942": ("table or view does not exist", "missing table"),
    "nullpointerexception": ("npe", "null pointer"),
    "sqlite": ("fts5", "fts"),
    "kubernetes": ("k8s", "kubectl"),
    "postgresql": ("postgres", "psql"),
}


def normalize_synonym_key(term: str) -> str:
    """Normalize a term for dictionary lookup."""
    return term.strip().lower()


def merge_synonym_dictionaries(
    *dictionaries: Mapping[str, Sequence[str]],
) -> dict[str, tuple[str, ...]]:
    """Merge synonym maps; later dictionaries override earlier keys."""
    merged: dict[str, tuple[str, ...]] = {}
    for dictionary in dictionaries:
        for key, values in dictionary.items():
            normalized = normalize_synonym_key(str(key))
            if not normalized:
                continue
            cleaned = tuple(
                str(value).strip()
                for value in values
                if str(value).strip() and normalize_synonym_key(str(value)) != normalized
            )
            if cleaned:
                merged[normalized] = cleaned
    return merged


def default_synonym_dictionary(
    overrides: Mapping[str, Sequence[str]] | None = None,
) -> dict[str, tuple[str, ...]]:
    """Return builtin synonyms merged with optional workspace overrides."""
    if not overrides:
        return dict(BUILTIN_SYNONYMS)
    return merge_synonym_dictionaries(BUILTIN_SYNONYMS, overrides)


def expand_synonyms(
    terms: Sequence[str],
    dictionary: Mapping[str, Sequence[str]],
    *,
    max_per_term: int = 3,
) -> dict[str, list[str]]:
    """Map matched terms to synonym lists (capped per term)."""
    expansions: dict[str, list[str]] = {}
    for term in terms:
        key = normalize_synonym_key(term)
        if not key or key not in dictionary:
            continue
        syns = [s for s in dictionary[key] if s][: max(0, max_per_term)]
        if syns:
            expansions[term] = syns
    return expansions


def collect_expansion_terms(text: str, anchors: Sequence[str]) -> list[str]:
    """Collect candidate terms from anchors and raw query tokens."""
    terms: list[str] = []
    seen: set[str] = set()
    for anchor in anchors:
        key = normalize_synonym_key(anchor)
        if key and key not in seen:
            seen.add(key)
            terms.append(anchor)
    for token in text.replace(",", " ").split():
        cleaned = token.strip()
        key = normalize_synonym_key(cleaned)
        if key and key not in seen:
            seen.add(key)
            terms.append(cleaned)
    return terms
