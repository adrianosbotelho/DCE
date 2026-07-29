"""Optional git hooks for DCE workspaces (post-commit index)."""

from __future__ import annotations

import stat
from dataclasses import dataclass
from pathlib import Path

from dce.domain.errors import WorkspaceError

HOOK_MARKER = "# dce-managed-hook: post-commit"
HOOK_NAME = "post-commit"

_HOOK_SCRIPT = f"""#!/bin/sh
{HOOK_MARKER}
# Keep the DCE git indexer fresh after each commit.
# Soft-fail: never block the commit if indexing fails.
set -e
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "$ROOT" || exit 0
if command -v dce >/dev/null 2>&1; then
  dce index . --source git >/dev/null 2>&1 || true
elif command -v python3 >/dev/null 2>&1; then
  python3 -m dce index . --source git >/dev/null 2>&1 || true
fi
exit 0
"""


@dataclass(frozen=True)
class HookStatus:
    """Status of the managed post-commit hook."""

    repo_root: Path | None
    hook_path: Path | None
    installed: bool
    managed: bool
    detail: str


def find_git_dir(workspace_root: Path) -> Path | None:
    """Return ``.git`` directory for workspace, if present."""
    root = workspace_root.resolve()
    git_path = root / ".git"
    if git_path.is_dir():
        return git_path
    if git_path.is_file():
        # worktree / submodule pointer — unsupported for install in this thin slice
        return None
    return None


def hook_path_for(workspace_root: Path) -> Path | None:
    """Return path to ``.git/hooks/post-commit`` when a repo exists."""
    git_dir = find_git_dir(workspace_root)
    if git_dir is None:
        return None
    return git_dir / "hooks" / HOOK_NAME


def get_hook_status(workspace_root: Path) -> HookStatus:
    """Inspect whether a managed post-commit hook is installed."""
    root = workspace_root.resolve()
    path = hook_path_for(root)
    if path is None:
        return HookStatus(
            repo_root=None,
            hook_path=None,
            installed=False,
            managed=False,
            detail="not a git repository (no .git directory)",
        )
    if not path.is_file():
        return HookStatus(
            repo_root=root,
            hook_path=path,
            installed=False,
            managed=False,
            detail="post-commit not installed",
        )
    text = path.read_text(encoding="utf-8", errors="replace")
    managed = HOOK_MARKER in text
    return HookStatus(
        repo_root=root,
        hook_path=path,
        installed=True,
        managed=managed,
        detail="managed by dce" if managed else "foreign post-commit present",
    )


def install_post_commit_hook(workspace_root: Path, *, force: bool = False) -> Path:
    """Install the managed post-commit hook. Returns hook path."""
    path = hook_path_for(workspace_root)
    if path is None:
        msg = "Not a git repository (expected .git directory under workspace)"
        raise WorkspaceError(msg)

    if path.is_file():
        existing = path.read_text(encoding="utf-8", errors="replace")
        if HOOK_MARKER not in existing and not force:
            msg = (
                f"Refusing to overwrite foreign hook at {path}. "
                "Re-run with --force to replace."
            )
            raise WorkspaceError(msg)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_HOOK_SCRIPT, encoding="utf-8")
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def uninstall_post_commit_hook(workspace_root: Path, *, force: bool = False) -> Path | None:
    """Remove the managed post-commit hook. Returns removed path or None."""
    status = get_hook_status(workspace_root)
    if status.hook_path is None or not status.installed:
        return None
    if not status.managed and not force:
        msg = (
            f"Refusing to remove foreign hook at {status.hook_path}. "
            "Re-run with --force to delete."
        )
        raise WorkspaceError(msg)
    status.hook_path.unlink(missing_ok=True)
    return status.hook_path
