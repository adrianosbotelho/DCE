"""Git indexer — commit messages and touched paths (no diffs/blobs)."""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dce.application.related_uris import (
    commit_uri,
    extract_pr_uris,
    issue_uri,
    merge_unique,
    normalize_related_uris,
)
from dce.domain.models import Document, SourceType
from dce.infrastructure.indexers.common import content_hash, stable_document_id

logger = logging.getLogger(__name__)

_ISSUE_KEY_RE = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")
_DEFAULT_MAX_COMMITS = 200
_RECORD_SEP = "\x1e"
_FIELD_SEP = "\x1f"
_BODY_SEP = "\x1d"


@dataclass(frozen=True)
class GitCommitItem:
    """One commit discovered from git log."""

    sha: str
    short_sha: str
    author_name: str
    author_email: str
    committed_at: str
    subject: str
    body: str
    paths: tuple[str, ...]


def extract_issue_keys(*texts: str) -> list[str]:
    """Extract Jira-like issue keys from commit text."""
    found: list[str] = []
    seen: set[str] = set()
    for text in texts:
        for match in _ISSUE_KEY_RE.findall(text):
            key = match.upper()
            if key not in seen:
                seen.add(key)
                found.append(key)
    return found


def resolve_repo_path(workspace_root: Path, repo_path: str | Path) -> Path:
    """Resolve configured repo path under the workspace when relative."""
    path = Path(repo_path)
    if path.is_absolute():
        return path.resolve()
    return (workspace_root / path).resolve()


def is_git_repository(repo_path: Path) -> bool:
    """Return True when path is inside a git work tree."""
    if not repo_path.exists():
        return False
    result = _run_git(repo_path, ["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip() == "true"


def _run_git(
    repo_path: Path,
    args: list[str],
    *,
    timeout: float = 60.0,
) -> subprocess.CompletedProcess[str]:
    git_bin = shutil.which("git")
    if git_bin is None:
        return subprocess.CompletedProcess(
            args=["git", *args],
            returncode=127,
            stdout="",
            stderr="git executable not found",
        )
    try:
        return subprocess.run(
            [git_bin, "-C", str(repo_path), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.warning("git command failed in %s: %s", repo_path, exc)
        return subprocess.CompletedProcess(
            args=["git", *args],
            returncode=1,
            stdout="",
            stderr=str(exc),
        )


def parse_git_log(output: str) -> list[GitCommitItem]:
    """Parse metadata+paths ``git log`` output (subject only; no multiline body)."""
    commits: list[GitCommitItem] = []
    if not output.strip():
        return commits

    for chunk in output.split(_RECORD_SEP):
        block = chunk.strip("\n")
        if not block.strip() or _FIELD_SEP not in block:
            continue
        header, _, files_part = block.partition("\n")
        fields = header.split(_FIELD_SEP)
        if len(fields) < 6:
            continue
        sha, short_sha, author_name, author_email, committed_at, subject = fields[:6]
        paths = tuple(line.strip() for line in files_part.splitlines() if line.strip())
        if not sha.strip():
            continue
        commits.append(
            GitCommitItem(
                sha=sha.strip(),
                short_sha=short_sha.strip() or sha.strip()[:7],
                author_name=author_name.strip(),
                author_email=author_email.strip(),
                committed_at=committed_at.strip(),
                subject=subject.strip(),
                body="",
                paths=paths,
            )
        )
    return commits


def parse_git_bodies(output: str) -> dict[str, str]:
    """Parse ``sha + body`` records from a second git log call."""
    bodies: dict[str, str] = {}
    if not output.strip():
        return bodies
    for chunk in output.split(_RECORD_SEP):
        block = chunk.strip("\n")
        if not block or _BODY_SEP not in block:
            continue
        sha, _, body = block.partition(_BODY_SEP)
        sha = sha.strip()
        if sha:
            bodies[sha] = body.strip()
    return bodies


def read_commits(
    repo_path: Path,
    *,
    max_commits: int,
    include_body: bool,
) -> list[GitCommitItem]:
    """Run conservative git log calls and parse commits."""
    max_commits = max(1, min(max_commits, 5000))
    pretty = (
        f"{_RECORD_SEP}%H{_FIELD_SEP}%h{_FIELD_SEP}%an{_FIELD_SEP}%ae{_FIELD_SEP}%aI{_FIELD_SEP}%s"
    )
    meta = _run_git(
        repo_path,
        [
            "log",
            f"--max-count={max_commits}",
            f"--pretty=format:{pretty}",
            "--name-only",
            "--no-merges",
        ],
    )
    if meta.returncode != 0:
        logger.warning(
            "git log failed in %s: %s",
            repo_path,
            meta.stderr.strip() or meta.returncode,
        )
        return []

    commits = parse_git_log(meta.stdout)
    if not include_body or not commits:
        return commits

    bodies_result = _run_git(
        repo_path,
        [
            "log",
            f"--max-count={max_commits}",
            f"--pretty=format:{_RECORD_SEP}%H{_BODY_SEP}%b",
            "--no-merges",
        ],
    )
    if bodies_result.returncode != 0:
        logger.warning("git log bodies failed in %s", repo_path)
        return commits

    bodies = parse_git_bodies(bodies_result.stdout)
    return [
        GitCommitItem(
            sha=item.sha,
            short_sha=item.short_sha,
            author_name=item.author_name,
            author_email=item.author_email,
            committed_at=item.committed_at,
            subject=item.subject,
            body=bodies.get(item.sha, ""),
            paths=item.paths,
        )
        for item in commits
    ]


def _parse_committed_at(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def build_commit_body(item: GitCommitItem) -> str:
    """Compose FTS-friendly body without diffs."""
    lines = [
        f"Commit: {item.sha}",
        f"Subject: {item.subject}",
        f"Author: {item.author_name} <{item.author_email}>",
        f"Date: {item.committed_at}",
    ]
    if item.body:
        lines.extend(["", "Message:", item.body])
    if item.paths:
        lines.extend(["", "Files:"])
        lines.extend(f"- {path}" for path in item.paths)
    return "\n".join(lines).strip()


class GitIndexer:
    """Indexer for local git commit history (messages + paths only)."""

    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root.resolve()

    @property
    def name(self) -> str:
        return "git"

    @property
    def source_type(self) -> str:
        return SourceType.GIT.value

    def discover(self, config: Mapping[str, Any]) -> Iterator[GitCommitItem]:
        if shutil.which("git") is None:
            logger.warning("git executable not found — skipping git indexer")
            return

        repo_path = resolve_repo_path(self._root, str(config.get("repo_path") or "."))
        if not is_git_repository(repo_path):
            logger.warning("Not a git repository: %s", repo_path)
            return

        max_commits = int(config.get("max_commits") or _DEFAULT_MAX_COMMITS)
        include_body = bool(config.get("include_body", True))
        yield from read_commits(
            repo_path,
            max_commits=max_commits,
            include_body=include_body,
        )

    def transform(self, item: GitCommitItem) -> Document:
        issue_keys = extract_issue_keys(item.subject, item.body)
        tags = ["commit", *issue_keys]
        body = build_commit_body(item)
        committed_at = _parse_committed_at(item.committed_at)
        related = normalize_related_uris(
            merge_unique(
                item.paths,
                [issue_uri(k) for k in issue_keys],
                [commit_uri(item.sha)],
                extract_pr_uris(item.subject, item.body),
            )
        )
        summary = item.subject[:240] if item.subject else item.short_sha

        metadata: dict[str, Any] = {
            "content_hash": content_hash(f"{item.sha}\n{body}"),
            "sha": item.sha,
            "short_sha": item.short_sha,
            "author_name": item.author_name,
            "author_email": item.author_email,
            "committed_at": item.committed_at,
            "paths": list(item.paths),
            "issue_keys": issue_keys,
        }

        return Document(
            id=stable_document_id(self.source_type, item.sha),
            source_type=self.source_type,
            uri=item.sha,
            title=item.subject or item.short_sha,
            body=body,
            summary=summary,
            metadata=metadata,
            tags=tags,
            project=None,
            component=None,
            technology=None,
            related_uris=related,
            created_at=committed_at,
            updated_at=committed_at,
        )
