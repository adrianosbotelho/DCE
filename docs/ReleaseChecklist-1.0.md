# Release Checklist — 1.0.0

**Release:** `1.0.0` (Sprint 16)  
**RC anterior:** `1.0.0rc1` (Sprint 15)

---

## Feito no RC (`1.0.0rc1`)

- [x] Contrato MCP `schema_version: "1"` documentado ([`MCP.md`](MCP.md), ADR-004)
- [x] Tools congeladas: `build_context`, `search_context`, `get_document`, `recent_documents`
- [x] Packaging hatch/wheel/sdist + `twine check` (PB-090)
- [x] Nome dist `dev-context-engine` (ADR-005)
- [x] Operação: init/index/doctor/build/mcp/bench/backup/restore
- [x] SLOs registrados + `dce bench` (PB-091)
- [x] Testes automatizados + cobertura ≥ 80%

---

## Gates `1.0.0` final

### Qualidade

- [x] `ruff check` + `ruff format --check` verdes
- [x] `mypy` verde
- [x] `pytest` verde (incl. contract MCP + packaging smoke)
- [x] `python -m build && twine check dist/*` verdes
- [x] Wheel smoke: packaging integration test

### Evidência operacional

- [x] `dce bench --docs 500 --iterations 30` — ver [`bench-results/1.0.0-SUMMARY.md`](bench-results/1.0.0-SUMMARY.md)
- [x] `dce doctor` smoke em workspace temporário
- [x] Backup/restore smoke (`dce backup` → wipe → `dce restore`)

### Documentação

- [x] CHANGELOG seção `[1.0.0]`
- [x] README status = `1.0.0`
- [x] Packaging / Operations revisados
- [x] Classifier Production/Stable

### Publicação (maintainer)

- [ ] Tag Git `v1.0.0`
- [ ] (Opcional) TestPyPI upload
- [ ] PyPI: `twine upload dist/*` com token
- [ ] GitHub Release notes = CHANGELOG `[1.0.0]`

> Upload e tag permanecem **gated** ao maintainer (credenciais / remoto git).

---

## Explicitamente fora de 1.0.0

- Jira REST live (PB-080)
- Aliases MCP `search_by_*` (PB-070+)
- Vector search / APIs pagas
- UI web

---

## Comandos rápidos

```bash
pip install -e ".[dev]"
ruff check src tests && ruff format --check src tests
mypy
pytest
rm -rf dist && python -m build && twine check dist/*
dce bench --docs 500 --iterations 30 --format table
# maintainer:
# twine upload dist/*
```
