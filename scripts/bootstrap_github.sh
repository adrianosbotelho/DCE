#!/usr/bin/env bash
# Create GitHub remote (if missing) and push main + latest SemVer tag.
# Usage:
#   ./scripts/bootstrap_github.sh              # uses adrianosbotelho/DCE
#   ./scripts/bootstrap_github.sh OWNER/REPO   # custom
#   ./scripts/bootstrap_github.sh --public OWNER/REPO
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VISIBILITY="--public"
REPO_SLUG="adrianosbotelho/DCE"

for arg in "$@"; do
  case "$arg" in
    --public) VISIBILITY="--public" ;;
    --private) VISIBILITY="--private" ;;
    -h|--help)
      echo "Usage: $0 [--public|--private] [OWNER/REPO]"
      exit 0
      ;;
    *)
      REPO_SLUG="$arg"
      ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI required" >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository" >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree dirty — commit first" >&2
  exit 1
fi

VERSION="$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")"
TAG="v${VERSION}"
if ! git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Missing tag ${TAG}. Run ./scripts/cut_release.sh first." >&2
  exit 1
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  if gh repo view "$REPO_SLUG" >/dev/null 2>&1; then
    git remote add origin "https://github.com/${REPO_SLUG}.git"
    echo "Added origin → ${REPO_SLUG}"
  else
    gh repo create "$REPO_SLUG" $VISIBILITY --source=. --remote=origin --description "Dev Context Engine — offline context builder for AI coding agents"
    echo "Created ${REPO_SLUG}"
  fi
else
  echo "origin already set: $(git remote get-url origin)"
fi

git push -u origin HEAD
git push origin "$TAG"
echo "Pushed HEAD and ${TAG} to origin."
echo "Windows Portable Release (if workflow enabled): Actions → tag ${TAG}"
