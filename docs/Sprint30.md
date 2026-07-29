# Sprint 30 — Planejamento e entrega

**Sprint:** 30  
**Release alvo:** 1.14.0  
**Status:** ✅ Concluída (aguardando aprovação para Sprint 31)  
**Última atualização:** 2026-07-29

---

## Objetivo

Entregar **PB-072**: tool MCP aditiva `search_by_component`.

## Escopo

| ID | Item | Critérios de aceite | Status |
|----|------|---------------------|--------|
| PB-072 | `search_by_component` | Tool estável; contract test; docs MCP; `schema_version` `"1"` | ✅ |

### Fora de escopo

- PB-073–074 · push remoto · PyPI · Authenticode

## Entrega

| Artefato | Caminho |
|----------|---------|
| Tool | `src/dce/interfaces/mcp/server.py` |
| Contract | `STABLE_TOOLS` + contract tests |
| Version | `1.14.0` |

## Definition of Done

1. [x] Tool + STABLE_TOOLS  
2. [x] Contract/unit tests  
3. [x] Docs + version 1.14.0  
4. [x] Tag local; Maintainer aprova Sprint 31  

## Sprint 31 (preview)

- PB-073 `search_by_technology`
- Push `origin` + tag (Release Windows)
- Publish PyPI
