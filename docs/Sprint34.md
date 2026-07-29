# Sprint 34 — Planejamento e entrega

**Sprint:** 34  
**Release alvo:** 1.18.0  
**Status:** ✅ Concluída  
**Última atualização:** 2026-07-29

---

## Objetivo

**PB-098** — estabilizar release path: corrigir CI (ruff format), Trusted Publisher no workflow Publish, docs de verificação (Windows Release `v1.17.0` já ok).

## Escopo

| ID | Item | Status |
|----|------|--------|
| PB-098a | Fix CI `ruff format` | ✅ |
| PB-098b | Publish workflow OIDC (`pypa/gh-action-pypi-publish`) | ✅ |
| PB-098c | Docs Packaging + ReleaseVerify | ✅ |

### Fora de escopo

- Upload PyPI real (precisa Trusted Publisher configurado no pypi.org pelo maintainer)
- Authenticode / MSI

## Evidence

- Windows Release `v1.17.0`: https://github.com/adrianosbotelho/DCE/releases/tag/v1.17.0

## Sprint 35 (preview)

- Configurar Trusted Publisher + primeiro upload PyPI
- Authenticode (se certificado)
- Feedback real de uso no Kiro
