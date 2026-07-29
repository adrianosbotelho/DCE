# Sprint 33 — Planejamento e entrega

**Sprint:** 33  
**Release alvo:** 1.17.0  
**Status:** ✅ Concluída (aguardando aprovação para Sprint 34)  
**Última atualização:** 2026-07-29

---

## Objetivo

**PB-097** — readiness de adoção: `dce doctor` reporta índice + MCP; guia Kiro; bootstrap GitHub (`origin` + push da tag).

## Escopo

| ID | Item | Status |
|----|------|--------|
| PB-097a | Doctor: checks `documents` + `mcp` | ✅ |
| PB-097b | Docs `Kiro.md` | ✅ |
| PB-097c | `scripts/bootstrap_github.sh` + push remoto | ✅ |

### Fora de escopo

- Upload PyPI (precisa `PYPI_TOKEN`)
- Authenticode / MSI

## Definition of Done

1. [x] Doctor + testes  
2. [x] Docs Kiro  
3. [x] Version 1.17.0 + tag  
4. [x] Repo GitHub + push (se `gh` autenticado)  

## Sprint 34 (preview)

- Publish PyPI  
- Monitorar Release Windows da tag  
- Authenticode (se certificado)
