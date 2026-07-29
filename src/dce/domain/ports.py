"""Ports (Protocols) between application and infrastructure."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from dce.domain.models import Document, ScoredDocument, SearchFilters, SearchSpec


@runtime_checkable
class Clock(Protocol):
    """Time source for testability."""

    def now(self) -> datetime:
        """Return the current timezone-aware UTC datetime."""


@runtime_checkable
class DocumentRepository(Protocol):
    """Persistence and retrieval of canonical documents."""

    def upsert_many(self, documents: Sequence[Document]) -> int:
        """Insert or replace documents. Returns number of upserted rows."""

    def get(self, document_id: str) -> Document | None:
        """Fetch a document by id."""

    def search(self, spec: SearchSpec) -> list[ScoredDocument]:
        """Full-text search with optional metadata filters."""

    def list_recent(
        self,
        limit: int = 20,
        filters: SearchFilters | None = None,
    ) -> list[Document]:
        """List newest documents by updated_at/indexed_at."""


@runtime_checkable
class Indexer(Protocol):
    """Independent source indexer. Must not import other indexers."""

    @property
    def name(self) -> str:
        """Stable indexer name for logs and config keys."""

    @property
    def source_type(self) -> str:
        """Canonical source_type written on produced documents."""

    def discover(self, config: Mapping[str, Any]) -> Iterable[Any]:
        """Yield raw items from the configured source."""

    def transform(self, item: Any) -> Document:
        """Map a raw item into a canonical Document."""
