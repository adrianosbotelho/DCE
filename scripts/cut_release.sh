#!/usr/bin/env bash
# Create an annotated git tag matching pyproject.toml / dce.__version__.
# Usage:
#   ./scripts/cut_release.sh           # tag only (local)
#   ./scripts/cut_release.sh --push    # tag + push tag to origin
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PUSH=0
for arg in "$@"; do
  case "$arg" in
    --push) PUSH=1 ;;
    -h|--help)
      echo "Usage: $0 [--push]"
      exit 0
      ;;
    *)
      echo "Unknown arg: $arg" >&2
      exit 2
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository. Run git init first." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree is dirty. Commit or stash before cutting a release." >&2
  git status --short >&2
  exit 1
fi

VERSION="$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")"
IMPORT_VERSION="$(python -c "from dce import __version__; print(__version__)")"
if [[ "$VERSION" != "$IMPORT_VERSION" ]]; then
  echo "Version mismatch: pyproject=$VERSION dce.__version__=$IMPORT_VERSION" >&2
  exit 1
fi

TAG="v${VERSION}"
if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Tag already exists: $TAG" >&2
  exit 1
fi

git tag -a "$TAG" -m "Release ${TAG}"
echo "Created annotated tag ${TAG}"

if [[ "$PUSH" -eq 1 ]]; then
  if ! git remote get-url origin >/dev/null 2>&1; then
    echo "No origin remote configured; tag created locally only." >&2
    exit 1
  fi
  git push origin "$TAG"
  echo "Pushed ${TAG} to origin (triggers Windows Portable Release workflow)."
else
  echo "Local only. Push when ready:"
  echo "  git push -u origin HEAD"
  echo "  git push origin ${TAG}"
  echo "  # or: ./scripts/cut_release.sh --push"
fi
