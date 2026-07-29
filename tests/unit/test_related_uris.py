"""Unit tests for related_uris helpers and linker."""

from __future__ import annotations

from collections.abc import Sequence

from dce.application.related_uris import (
    commit_uri,
    extract_pr_uris,
    issue_uri,
    link_related_uris,
    merge_unique,
    normalize_related_uris,
    pr_uri,
)
from dce.domain.models import Document, ScoredDocument, SearchFilters, SearchSpec


class MemoryRepo:
    def __init__(self, docs: list[Document] | None = None) -> None:
        self.by_id: dict[str, Document] = {d.id: d for d in (docs or [])}

    def upsert_many(self, documents: Sequence[Document]) -> int:
        for doc in documents:
            self.by_id[doc.id] = doc
        return len(documents)

    def get(self, document_id: str) -> Document | None:
        return self.by_id.get(document_id)

    def search(self, spec: SearchSpec) -> list[ScoredDocument]:
        docs = list(self.by_id.values())
        types = spec.filters.source_types
        if types:
            docs = [d for d in docs if d.source_type in types]
        return [ScoredDocument(document=d, score=0.0) for d in docs[: spec.limit]]

    def list_recent(
        self,
        limit: int = 20,
        filters: SearchFilters | None = None,
    ) -> list[Document]:
        return list(self.by_id.values())[:limit]


def test_uri_helpers_and_pr_extract() -> None:
    assert issue_uri("pay-1") == "issue:PAY-1"
    assert commit_uri("ABC1234") == "commit:abc1234"
    assert pr_uri(42) == "pr:42"
    assert merge_unique(["a", "b"], ["b", "c"]) == ["a", "b", "c"]
    prs = extract_pr_uris(
        "Fixes PAY-1 via PR #7 and https://github.com/org/repo/pull/99",
        "Also merge request !3",
    )
    assert "pr:7" in prs
    assert "https://github.com/org/repo/pull/99" in prs
    assert "pr:3" in prs
    assert normalize_related_uris(["PAY-9", "pay-9", "deadbeef"]) == [
        "issue:PAY-9",
        "commit:deadbeef",
    ]


def test_link_related_uris_bidirectional() -> None:
    git = Document(
        id="git:abc",
        source_type="git",
        uri="abcdef0123456789",
        title="Fix PAY-125 listener PR #12",
        body="See https://github.com/acme/pay/pull/12",
        tags=["commit", "PAY-125"],
        metadata={"sha": "abcdef0123456789", "issue_keys": ["PAY-125"]},
        related_uris=["src/x.py", "issue:PAY-125", "commit:abcdef0123456789"],
    )
    jira = Document(
        id="jira:pay-125",
        source_type="jira",
        uri="PAY-125",
        title="Listener",
        tags=["PAY-125"],
        metadata={"key": "PAY-125"},
        related_uris=["https://git/pr/99"],
    )
    repo = MemoryRepo([git, jira])
    updated = link_related_uris(repo)
    assert updated == 2
    linked_git = repo.get("git:abc")
    linked_jira = repo.get("jira:pay-125")
    assert linked_git is not None
    assert linked_jira is not None
    assert "issue:PAY-125" in linked_git.related_uris
    assert "pr:12" in linked_git.related_uris
    assert "commit:abcdef0123456789" in linked_jira.related_uris
    assert "issue:PAY-125" in linked_jira.related_uris
    assert "https://github.com/acme/pay/pull/12" in linked_jira.related_uris
    assert "https://git/pr/99" in linked_jira.related_uris
