"""Shared file helpers for markdown-like indexers (not an Indexer itself)."""

from __future__ import annotations

import hashlib
import logging
import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_HEADING_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_ABS_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")


@dataclass(frozen=True)
class TextFileItem:
    """Raw UTF-8 text file discovered under a workspace."""

    relative_path: str
    absolute_path: Path
    text: str
    mtime: datetime


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split optional YAML frontmatter from markdown body."""
    if not text.startswith("---"):
        return {}, text

    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, text

    closing_index: int | None = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break
    if closing_index is None:
        return {}, text

    raw_yaml = "".join(lines[1:closing_index])
    body = "".join(lines[closing_index + 1 :])
    if not raw_yaml.strip():
        return {}, body

    try:
        loaded = yaml.safe_load(raw_yaml)
    except yaml.YAMLError:
        logger.warning("Ignoring invalid YAML frontmatter")
        return {}, text

    if loaded is None:
        return {}, body
    if not isinstance(loaded, dict):
        logger.warning("Ignoring non-mapping YAML frontmatter")
        return {}, text
    return loaded, body


def extract_title(body: str, frontmatter: Mapping[str, Any], relative_path: str) -> str:
    """Resolve title from frontmatter, first H1, or file stem."""
    for key in ("title", "Title"):
        value = frontmatter.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    match = _HEADING_RE.search(body)
    if match:
        return match.group(1).strip()
    return Path(relative_path).stem


def as_str_list(value: Any) -> list[str]:
    """Normalize tags-like values to a list of strings."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def optional_str(value: Any) -> str | None:
    """Coerce a scalar to a stripped string or None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def stable_document_id(source_type: str, relative_path: str) -> str:
    """Stable id from source type + relative path."""
    return hashlib.sha256(f"{source_type}:{relative_path}".encode()).hexdigest()


def is_under_root(path: Path, root: Path) -> bool:
    """Return True when resolved path stays inside workspace root."""
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _match_exclude(relative_posix: str, exclude_patterns: Sequence[str]) -> bool:
    """Return True when relative path matches an exclude glob/prefix."""
    for pattern in exclude_patterns:
        cleaned = pattern.replace("\\", "/").rstrip("/")
        if cleaned.endswith("/**"):
            prefix = cleaned[:-3].rstrip("/")
            if relative_posix == prefix or relative_posix.startswith(prefix + "/"):
                return True
        if Path(relative_posix).match(pattern):
            return True
        # Filename-only patterns like "*.tmp"
        if Path(relative_posix).name == pattern or Path(Path(relative_posix).name).match(pattern):
            return True
    return False


def discover_text_files(
    root: Path,
    patterns: Sequence[str],
    *,
    exclude: Sequence[str] = (),
    suffixes: frozenset[str] = frozenset({".md", ".markdown"}),
) -> Iterator[TextFileItem]:
    """Yield UTF-8 text files under root for the given globs."""
    resolved_root = root.resolve()
    seen: set[Path] = set()
    for pattern in patterns:
        if pattern.startswith("/") or _ABS_PATTERN.match(pattern):
            logger.warning("Skipping absolute glob pattern: %s", pattern)
            continue
        for match in sorted(resolved_root.glob(pattern)):
            if not match.is_file():
                continue
            resolved = match.resolve()
            if resolved in seen:
                continue
            if not is_under_root(resolved, resolved_root):
                logger.warning("Skipping path outside workspace: %s", match)
                continue
            if resolved.suffix.lower() not in suffixes:
                continue
            relative = resolved.relative_to(resolved_root).as_posix()
            if exclude and _match_exclude(relative, exclude):
                continue
            try:
                text = resolved.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                logger.warning("Skipping non-UTF-8 file: %s", match)
                continue
            except OSError as exc:
                logger.warning("Skipping unreadable file %s: %s", match, exc)
                continue

            mtime = datetime.fromtimestamp(resolved.stat().st_mtime, tz=UTC)
            seen.add(resolved)
            yield TextFileItem(
                relative_path=relative,
                absolute_path=resolved,
                text=text,
                mtime=mtime,
            )


def content_hash(text: str) -> str:
    """SHA-256 hex digest of file text."""
    return hashlib.sha256(text.encode()).hexdigest()
