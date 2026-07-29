#!/usr/bin/env bash
# Build + optional Twine upload for dev-context-engine.
# Usage:
#   ./scripts/publish.sh              # build + twine check only
#   ./scripts/publish.sh --upload     # also twine upload (needs PYPI token)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

UPLOAD=0
REPO="pypi"
for arg in "$@"; do
  case "$arg" in
    --upload) UPLOAD=1 ;;
    --testpypi) REPO="testpypi"; UPLOAD=1 ;;
    -h|--help)
      echo "Usage: $0 [--upload|--testpypi]"
      exit 0
      ;;
    *)
      echo "Unknown arg: $arg" >&2
      exit 2
      ;;
  esac
done

python -m pip install -q build twine
rm -rf dist
python -m build
python -m twine check dist/*

if [[ "$UPLOAD" -eq 1 ]]; then
  if [[ -z "${TWINE_USERNAME:-}" && -z "${TWINE_PASSWORD:-}" && -z "${PYPI_TOKEN:-}" ]]; then
    echo "Set PYPI_TOKEN or TWINE_USERNAME/TWINE_PASSWORD before --upload" >&2
    exit 1
  fi
  if [[ -n "${PYPI_TOKEN:-}" ]]; then
    export TWINE_USERNAME="__token__"
    export TWINE_PASSWORD="$PYPI_TOKEN"
  fi
  if [[ "$REPO" == "testpypi" ]]; then
    python -m twine upload --repository testpypi --non-interactive dist/*
  else
    python -m twine upload --non-interactive dist/*
  fi
  echo "Upload finished."
else
  echo "Build OK. Re-run with --upload (and PYPI_TOKEN) to publish."
fi
