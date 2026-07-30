# Sprint 44 — Planejamento e entrega

**Sprint:** 44  
**Release:** 1.28.0  
**Status:** ✅ Concluída  

## Objetivo

**PB-108** — steering / regras prontas para o Kiro usar o DCE no dia a dia sem o usuário invocar MCP em todo prompt.

## Escopo

| Item | Status |
|------|--------|
| Texto canônico `kiro_steering` | ✅ |
| CLI `dce steering` | ✅ |
| UI passo “Copiar steering” + `/api/steering` | ✅ |
| Docs `KiroSteering.md` | ✅ |

## Fora de escopo

- Authenticode / MSI (precisa certificado)
- UI cloud / multi-tenant (PB-902)

## Como usar

```bash
dce steering                 # imprimir regras
dce ui --path /seu/projeto   # copiar pela interface
```
