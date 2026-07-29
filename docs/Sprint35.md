# Sprint 35 — Planejamento e entrega

**Sprint:** 35  
**Release alvo:** 1.19.0  
**Status:** ✅ Concluída (aguardando aprovação para Sprint 36)  
**Última atualização:** 2026-07-29

---

## Objetivo

**PB-099** — destravar first-publish PyPI (runbook + environment) e polish operacional (`doctor --json`, Actions Node 24).

## Escopo

| ID | Item | Status |
|----|------|--------|
| PB-099a | GitHub environment `pypi` | ✅ |
| PB-099b | `docs/PublishPyPI.md` (pending Trusted Publisher) | ✅ |
| PB-099c | `dce doctor --json` | ✅ |
| PB-099d | Bump Actions `checkout@v5` / `setup-python@v6` | ✅ |

### Fora de escopo

- Upload PyPI real (exige pending publisher no pypi.org — ação humana)
- Authenticode / MSI

## Evidence

- Windows Release `v1.18.0` com ZIP + SHA-256 ok
- Environment: https://github.com/adrianosbotelho/DCE/settings/environments

## Sprint 36 (preview)

- Maintainer: pending publisher + `gh workflow run publish.yml`
- Authenticode (se certificado)
- Feedback Kiro em workspace real
