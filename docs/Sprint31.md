# Sprint 31 — Planejamento e entrega

**Sprint:** 31  
**Release alvo:** 1.15.0  
**Status:** ✅ Concluída  
**Última atualização:** 2026-07-29

---

## Objetivo

Entregar **PB-073**: tool MCP aditiva `search_by_technology`.

## Escopo

| ID | Item | Critérios de aceite | Status |
|----|------|---------------------|--------|
| PB-073 | `search_by_technology` | Tool estável; contract test; docs MCP; `schema_version` `"1"` | ✅ |

### Fora de escopo

- PB-074 · push remoto · PyPI · Authenticode

## Entrega

| Artefato | Caminho |
|----------|---------|
| Tool | `src/dce/interfaces/mcp/server.py` |
| Contract | `STABLE_TOOLS` + contract tests |
| Version | `1.15.0` |

## Definition of Done

1. [x] Tool + STABLE_TOOLS  
2. [x] Contract/unit tests  
3. [x] Docs + version 1.15.0  
4. [x] Tag local; Maintainer aprova Sprint 32  

## Sprint 32 (preview)

- PB-074 `search_by_tag`
- Push `origin` + tag (Release Windows)
- Publish PyPI
