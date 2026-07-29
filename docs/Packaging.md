# Packaging — Dev Context Engine (DCE)

**Status:** Ready to publish (upload gated by maintainer)  
**Release:** `1.10.0` (stable); packaging desde `0.9.0a1`  
**Backlog:** PB-090 (wheel) · PB-094 (Windows portable ZIP)

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

rm -rf dist/
python -m build
twine check dist/*
```

Artefatos esperados em `dist/`:

- `dev_context_engine-<version>.tar.gz` (sdist)
- `dev_context_engine-<version>-py3-none-any.whl` (wheel)

---

## Smoke de instalação (wheel)

```bash
python -m venv /tmp/dce-smoke
/tmp/dce-smoke/bin/pip install dist/*.whl
/tmp/dce-smoke/bin/dce --version
/tmp/dce-smoke/bin/python -c "import dce; assert dce.__version__"
```

---

## Publicar RC / 1.x (manual — maintainer)

```bash
./scripts/publish.sh              # build + twine check
export PYPI_TOKEN=pypi-...
./scripts/publish.sh --upload     # PyPI
./scripts/publish.sh --testpypi   # TestPyPI
```

Ou GitHub Actions → workflow **Publish** (`workflow_dispatch`) com secret `PYPI_TOKEN` / `TEST_PYPI_TOKEN`.

Gates 1.0: [`ReleaseChecklist-1.0.md`](ReleaseChecklist-1.0.md).

---

## Windows portable ZIP (PB-094)

Ver guia completo: [`Windows.md`](Windows.md).

```powershell
# Em máquina Windows / CI windows-latest
.\scripts\build_windows_portable.ps1
# → dist\dce-<version>-windows-x64.zip
```

GitHub Actions → workflow **Windows Portable** (`workflow_dispatch` ou tag `v*`).  
Em tags, o ZIP + `.sha256` vão para **GitHub Release** — ver [`ReleaseWindows.md`](ReleaseWindows.md).

---

## Hatch / layout

- Código em `src/dce/`
- Wheel inclui apenas o pacote `dce` (sem `force-include` duplicado)
- `py.typed` presente → typed package

---

## CI

Workflow `.github/workflows/ci.yml` executa build + `twine check` + smoke do wheel além de ruff/mypy/pytest.
