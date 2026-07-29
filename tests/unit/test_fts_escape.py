"""Unit tests for FTS query escaping."""

from dce.infrastructure.storage.repository import escape_fts5_query


def test_escape_empty() -> None:
    assert escape_fts5_query("   ") == ""


def test_escape_tokens_and_specials() -> None:
    query = escape_fts5_query('ORA-12541 "weird" (x)')
    assert '"ORA-12541"*' in query
    assert '"weird"*' in query
    assert " AND " in query
