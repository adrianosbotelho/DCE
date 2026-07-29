"""Indexing use case — orchestrates enabled indexers into the document store."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from dce.application.related_uris import link_related_uris
from dce.domain.ports import DocumentRepository, Indexer

logger = logging.getLogger(__name__)

# CLI aliases → indexer name / config key
SOURCE_ALIASES: dict[str, str] = {
    "md": "markdown",
    "markdown": "markdown",
    "adr": "adr",
    "memory": "memory",
    "mem": "memory",
    "procedure": "procedure",
    "proc": "procedure",
    "procedures": "procedure",
    "incident": "incident",
    "incidents": "incident",
    "inc": "incident",
    "snippet": "snippet",
    "snippets": "snippet",
    "snip": "snippet",
    "jira": "jira_import",
    "jira_import": "jira_import",
    "jira_rest": "jira_rest",
    "jira_api": "jira_rest",
    "git": "git",
}


@dataclass
class IndexerRunResult:
    """Per-indexer indexing outcome."""

    name: str
    source_type: str
    discovered: int = 0
    upserted: int = 0
    skipped: bool = False
    detail: str = ""


@dataclass
class IndexRunResult:
    """Aggregate outcome of ``dce index``."""

    runs: list[IndexerRunResult] = field(default_factory=list)
    related_uris_linked: int = 0

    @property
    def total_upserted(self) -> int:
        return sum(run.upserted for run in self.runs)


def normalize_source_name(source: str | None) -> str | None:
    """Map CLI source aliases to canonical indexer names."""
    if source is None:
        return None
    key = source.strip().lower()
    if not key:
        return None
    return SOURCE_ALIASES.get(key, key)


def run_indexing(
    repository: DocumentRepository,
    indexers: Sequence[Indexer],
    indexers_config: Mapping[str, Any],
    *,
    only_source: str | None = None,
) -> IndexRunResult:
    """Run selected indexers and upsert produced documents.

    An indexer runs when:
    - ``only_source`` matches its name, or
    - ``only_source`` is None and ``indexers_config[name].enabled`` is true.
    """
    result = IndexRunResult()
    selected = normalize_source_name(only_source)

    for indexer in indexers:
        cfg_raw = indexers_config.get(indexer.name) or {}
        cfg: dict[str, Any] = dict(cfg_raw) if isinstance(cfg_raw, Mapping) else {}
        enabled = bool(cfg.get("enabled", False))

        if selected is not None:
            if indexer.name != selected:
                continue
        elif not enabled:
            result.runs.append(
                IndexerRunResult(
                    name=indexer.name,
                    source_type=indexer.source_type,
                    skipped=True,
                    detail="disabled in config",
                )
            )
            continue

        discovered = 0
        documents = []
        for item in indexer.discover(cfg):
            documents.append(indexer.transform(item))
            discovered += 1

        upserted = repository.upsert_many(documents) if documents else 0
        logger.info(
            "indexer=%s discovered=%s upserted=%s",
            indexer.name,
            discovered,
            upserted,
        )
        result.runs.append(
            IndexerRunResult(
                name=indexer.name,
                source_type=indexer.source_type,
                discovered=discovered,
                upserted=upserted,
                detail="ok",
            )
        )

    if selected is not None and not any(run.name == selected for run in result.runs):
        result.runs.append(
            IndexerRunResult(
                name=selected,
                source_type=selected,
                skipped=True,
                detail="unknown or unavailable indexer",
            )
        )

    if any(not run.skipped and run.upserted > 0 for run in result.runs):
        result.related_uris_linked = link_related_uris(repository)

    return result
