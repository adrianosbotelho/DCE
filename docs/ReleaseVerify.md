# Release verification

**Status:** Sprint 34 (`1.18.0`)

Checklist after cutting a SemVer tag (`./scripts/cut_release.sh` + push).

## Automated

| Check | Where |
|-------|--------|
| CI (ruff/mypy/pytest/build) | Actions → **CI** on `main` |
| Windows ZIP + SHA-256 | Actions → **Windows Portable** on `v*` |
| GitHub Release assets | https://github.com/adrianosbotelho/DCE/releases |

Example (verified for `v1.17.0`):

- Release: https://github.com/adrianosbotelho/DCE/releases/tag/v1.17.0
- Assets: `dce-1.17.0-windows-x64.zip` + `.sha256`

## PyPI publish (maintainer)

1. One-time: on [pypi.org](https://pypi.org) → project `dev-context-engine` → **Publishing** → Trusted Publisher:
   - Owner: `adrianosbotelho`
   - Repository: `DCE`
   - Workflow: `publish.yml`
   - Environment: `pypi`
2. Actions → **Publish** → `workflow_dispatch` → target `pypi` (or `testpypi`).
3. Smoke: `pip install dev-context-engine==X.Y.Z && dce --version`

Local dry-run (no upload):

```bash
./scripts/publish.sh
```

Token fallback (optional): set GitHub environment secret `PYPI_TOKEN` / `TEST_PYPI_TOKEN`.

## Manual smoke

```bash
dce doctor /path/to/workspace
# Kiro: docs/Kiro.md
```
