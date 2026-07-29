"""Unit tests for synonym expansion helpers."""

from __future__ import annotations

from dce.application.synonyms import (
    BUILTIN_SYNONYMS,
    collect_expansion_terms,
    default_synonym_dictionary,
    expand_synonyms,
    merge_synonym_dictionaries,
    normalize_synonym_key,
)
from dce.infrastructure.storage.workspace import synonyms_from_config


def test_normalize_and_merge_overrides() -> None:
    assert normalize_synonym_key(" ORA-12541 ") == "ora-12541"
    merged = merge_synonym_dictionaries(
        BUILTIN_SYNONYMS,
        {"ORA-12541": ["custom-listener"]},
    )
    assert merged["ora-12541"] == ("custom-listener",)


def test_default_dictionary_merges_overrides() -> None:
    dictionary = default_synonym_dictionary({"sqlite": ["wal"]})
    assert "wal" in dictionary["sqlite"]
    assert "fts5" not in dictionary["sqlite"]  # override replaces key


def test_expand_synonyms_caps_and_matches_anchors() -> None:
    terms = collect_expansion_terms("fix ORA-12541 listener", ["ORA-12541"])
    expansions = expand_synonyms(terms, default_synonym_dictionary(), max_per_term=2)
    assert "ORA-12541" in expansions
    assert expansions["ORA-12541"] == ["tns", "listener"]


def test_synonyms_from_config() -> None:
    assert synonyms_from_config({}) == {}
    assert synonyms_from_config({"retrieval": {"synonyms": "bad"}}) == {}
    loaded = synonyms_from_config(
        {
            "retrieval": {
                "synonyms": {
                    "ORA-00942": ["missing table", ""],
                    "blank": [],
                    "": ["x"],
                }
            }
        }
    )
    assert loaded == {"ORA-00942": ["missing table"]}
