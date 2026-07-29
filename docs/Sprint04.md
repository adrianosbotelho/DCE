# Sprint 04 — Planejamento e entrega

**Sprint:** 04  
**Release alvo:** 0.2.0a1  
**Status:** 🟢 Concluída (aguardando aprovação de encerramento / Sprint 05)  
**Última atualização:** 2026-07-29

---

## Objetivo

Expor o motor ao **Kiro** via **MCP stdio**, com tools mínimas e respostas estruturadas.

## Resultado

| ID | Item | Status |
|----|------|--------|
| PB-020 | `dce mcp` stdio | ✅ |
| PB-021 | `build_context` | ✅ |
| PB-022 | `search_context` | ✅ |
| PB-023 | `get_document` | ✅ |
| PB-024 | `recent_documents` | ✅ |
| PB-025 | Contract tests | ✅ |

**Qualidade:** 63 testes; cobertura ≈ **88%**; ruff + mypy limpos.

### Revisão arquitetural

- [x] Tools MCP delegam aos use cases / repositório (sem lógica de retrieval duplicada)
- [x] Respostas tipadas com `schema_version`
- [x] Superfície mínima (sem `search_by_*`)
- [x] stdio only; stdout limpo no comando `mcp`

---

## Escopo

| ID | Item | Critérios de aceite |
|----|------|---------------------|
| PB-020 | `dce mcp` stdio | Sobe servidor MCP apontando a um workspace |
| PB-021 | `build_context` | Retorna `ContextPackage` estruturado |
| PB-022 | `search_context` | Lista `ScoredDocument` + `schema_version` |
| PB-023 | `get_document` | Documento ou `found=false` |
| PB-024 | `recent_documents` | Lista recente com filtros |
| PB-025 | Contract tests | `call_tool` cobre shapes estáveis |

### Fora de escopo

- Aliases `search_by_*` / `search_memory`
- HTTP / SSE transport
- Auth OAuth

## Decisão de dependência

Usar **`mcp` (SDK oficial) ≥ 2.0** com `MCPServer`, não o pacote standalone FastMCP 2.x.

| Alternativa | Por que não |
|-------------|-------------|
| `fastmcp` 2.x (Prefect) | Mais features e deps extras além do necessário para stdio |
| MCP SDK 1.x FastMCP | API legada; SDK 2.0 é o caminho atual |

Trade-off: o SDK 2 puxa Starlette/Uvicorn mesmo para stdio. Aceitável por estabilidade de protocolo; HTTP não é usado nesta sprint.

## Design

```mermaid
flowchart LR
  Kiro -->|stdio| CLI["dce mcp --path"]
  CLI --> S[MCPServer]
  S --> UC[build_context / search / get / recent]
  UC --> Repo[(SQLite)]
```

## Definition of Done

1. [x] Aceite PB-020…025  
2. [x] Testes + cobertura ≥ 80%  
3. [x] ruff + mypy  
4. [x] README + CHANGELOG  
5. [x] Maintainer aprova encerramento / Sprint 05  

## Sprint 05 (preview — não iniciar sem aprovação)

Candidata natural: **PB-030 ADR Indexer + PB-031 Memory notes** (épico E5).
