"""Indexer registry for composition roots (CLI / future workers)."""

from __future__ import annotations

from pathlib import Path

from dce.domain.ports import Indexer
from dce.infrastructure.indexers.adr import AdrIndexer
from dce.infrastructure.indexers.git import GitIndexer
from dce.infrastructure.indexers.incident import IncidentIndexer
from dce.infrastructure.indexers.jira_import import JiraImportIndexer
from dce.infrastructure.indexers.jira_rest import JiraRestIndexer
from dce.infrastructure.indexers.markdown import MarkdownIndexer
from dce.infrastructure.indexers.memory import MemoryIndexer
from dce.infrastructure.indexers.procedure import ProcedureIndexer
from dce.infrastructure.indexers.snippet import SnippetIndexer


def build_default_indexers(workspace_root: Path) -> list[Indexer]:
    """Return the built-in indexer set for a workspace."""
    root = workspace_root.resolve()
    return [
        MarkdownIndexer(root),
        AdrIndexer(root),
        MemoryIndexer(root),
        ProcedureIndexer(root),
        IncidentIndexer(root),
        SnippetIndexer(root),
        JiraImportIndexer(root),
        JiraRestIndexer(root),
        GitIndexer(root),
    ]
