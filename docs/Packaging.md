# Packaging — Dev Context Engine (DCE)

**Status:** Ready to publish (upload gated by Trusted Publisher / token)  
**Release:** `1.18.0`  
**Backlog:** PB-090 (wheel) · PB-094 (Windows ZIP) · PB-098 (publish OIDC)

---

## Nomes

| Superfície | Valor | Motivo |
|------------|--------|--------|
| Distribuição PyPI | `dev-context-engine` | Nome `dce` já ocupado no PyPI |
| Pacote importável | `dce` | Identidade do produto |
| CLI | `dce` | Entry point estável |

```bash
pip install dev-context-engine
dce --version
python -c "import dce; print(dce.__version__)"
```

---

## Build local

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

./scripts/publish.sh              # build + twine check (sem upload)
```

Artefatos esperados em `dist/`:

- `dev_context_engine-<version>.tar.gz` (sdist)
- `dev_context_engine-<version>-py3-none-any.whl` (wheel)

---

## Publicar (recomendado — Trusted Publisher)

1. Em [pypi.org](https://pypi.org) → projeto `dev-context-engine` → **Publishing** → adicionar Trusted Publisher:
   - Owner: `adrianosbotelho`
   - Repository: `DCE`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
2. No GitHub: criar environment `pypi` (Settings → Environments).
3. Actions → **Publish** → Run workflow → target `pypi` ou `testpypi`.

Ver também [`ReleaseVerify.md`](ReleaseVerify.md).

### Fallback com token local

```bash
export PYPI_TOKEN=pypi-...
./scripts/publish.sh --upload     # PyPI
./scripts/publish.sh --testpypi   # TestPyPI
```

---

## Smoke de instalação (wheel)

```bash
python -m venv /tmp/dce-smoke
/tmp/dce-smoke/bin/pip install dist/*.whl
/tmp/dce-smoke/bin/dce --version
/tmp/dce-smoke/bin/python -c "import dce; assert dce.__version__"
```

---

## Windows portable ZIP

Ver [`Windows.md`](Windows.md) · [`ReleaseWindows.md`](ReleaseWindows.md).

Tags `v*` publicam ZIP + `.sha256` no GitHub Release.

---

## Hatch / layout

- Código em `src/dce/`
- Wheel inclui apenas o pacote `dce`
- `py.typed` presente → typed package

---

## CI

`.github/workflows/ci.yml` executa ruff (check + format), mypy, pytest, build, twine check e smoke do wheel.
