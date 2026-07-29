# Git bootstrap & cut-release

**Status:** Sprint 28 (`1.12.0`)

This repo may start without a remote. Local bootstrap:

```bash
git init
git add -A
git commit -m "chore: initial import of Dev Context Engine"
```

## Cut a SemVer release

1. Bump `pyproject.toml` and `src/dce/__init__.py` to the same version.
2. Update `CHANGELOG.md` / docs.
3. Commit on a clean tree.
4. Run:

```bash
./scripts/cut_release.sh
# creates annotated tag vX.Y.Z matching package version
```

Optional push (requires `origin`):

```bash
git remote add origin git@github.com:OWNER/DCE.git   # once
git push -u origin HEAD
./scripts/cut_release.sh --push
# or: git push origin vX.Y.Z
```

Pushing a `v*` tag triggers **Windows Portable** → GitHub Release assets.  
See [`ReleaseWindows.md`](ReleaseWindows.md).

## Guardrails

- Dirty working tree → script exits.
- `pyproject` version ≠ `dce.__version__` → exits.
- Tag already exists → exits.
- `--push` without `origin` → exits after local tag (error).
