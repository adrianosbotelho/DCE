# Sprint 32 — Planejamento e entrega

**Sprint:** 32  
**Release alvo:** 1.16.0  
**Status:** ✅ Concluída  
**Última atualização:** 2026-07-29

---

## Objetivo

Entregar **PB-074**: tool MCP aditiva `search_by_tag` (fecha a série de aliases `search_by_*`).

## Escopo

| ID | Item | Critérios de aceite | Status |
|----|------|---------------------|--------|
| PB-074 | `search_by_tag` | Tool estável; contract test; docs MCP; `schema_version` `"1"` | ✅ |

### Fora de escopo

- Push remoto · PyPI · Authenticode / MSI

## Entrega

| Artefato | Caminho |
|----------|---------|
| Tool | `src/dce/interfaces/mcp/server.py` |
| Contract | `STABLE_TOOLS` + contract tests |
| Version | `1.16.0` |

## Definition of Done

1. [x] Tool + STABLE_TOOLS  
2. [x] Contract/unit tests  
3. [x] Docs + version 1.16.0  
4. [x] Tag local; Maintainer aprova Sprint 33  

## Sprint 33 (preview)

- Configurar `origin` + push das tags (Release Windows real)
- Publish PyPI (`PYPI_TOKEN`)
- Authenticode / MSI (se houver certificado)
- Ops: polish CLI doctor / docs de adoção Kiro
