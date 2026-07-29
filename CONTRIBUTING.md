# Contributing to Dev Context Engine (DCE)

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Quality gate (required)

```bash
ruff check src tests
ruff format --check src tests
mypy
pytest -m "not slow"
```

Coverage floor: **80%** (configured in `pyproject.toml`).

## Sprint / release process

1. Thin vertical slice (one backlog ID).
2. Tests + docs (`CHANGELOG`, sprint note).
3. Bump `pyproject.toml` + `src/dce/__init__.py` together.
4. `./scripts/cut_release.sh` then push tag (`v*`).
5. Wait for maintainer approval before the next sprint.

PyPI first upload: [`docs/PublishPyPI.md`](docs/PublishPyPI.md).  
Windows portable: tag push → GitHub Release assets.

## Architecture guardrails

- Offline-first; no vector DBs / paid AI APIs.
- MCP `schema_version: "1"` is additive-only (new optional fields/tools).
- Prefer `build_context` as the primary agent tool.
- Layout: `src/dce/{domain,application,infrastructure,interfaces}`.

## Useful commands

```bash
dce init .
dce index . --json
dce doctor . --json
dce facets . --json
dce tools --json
dce recent --path . --format json
dce mcp --path /absolute/workspace
```
