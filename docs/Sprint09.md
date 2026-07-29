# Sprint 09 — Planejamento e entrega

**Sprint:** 09  
**Release alvo:** 0.7.0a1  
**Status:** 🟢 Concluída  
**Última atualização:** 2026-07-29

---

## Objetivo

Fechar o épico de retrieval quality: **sinônimos técnicos** (PB-062) + **diagnostics ricos** (PB-033) no `ContextPackage`.

## Resultado

| ID | Item | Status |
|----|------|--------|
| PB-062 | Sinônimos técnicos | ✅ |
| PB-033 | Diagnostics ricos | ✅ |

### Revisão arquitetural

- [x] Sinônimos como passos FTS extras (não OR FTS)
- [x] Built-in + `retrieval.synonyms` merge via YAML
- [x] Diagnostics aditivos (`schema_version` permanece `1`)
- [x] CLI + MCP compartilham o mesmo `build_context`

---

## Escopo

| ID | Item | Critérios de aceite |
|----|------|---------------------|
| PB-062 | Sinônimos técnicos | Built-in + override via `dce.yaml`; passos FTS extras |
| PB-033 | Diagnostics ricos | `query_kind`, `preferred_sources`, `steps`, `synonym_expansions` |

### Fora de escopo

- MCP tool aliases `search_by_*`
- Jira REST
- Breaking `schema_version` (campos novos são aditivos)

## Design

```mermaid
flowchart LR
  Q[Query] --> S[SynonymDictionary]
  S --> P[Planner steps]
  P --> B[build_context]
  B --> D[RetrievalDiagnostics rico]
```

### Trade-offs

| Escolha | Motivo | Custo |
|---------|--------|-------|
| Sinônimos como passos extras (não OR FTS) | Compatível com escape FTS atual (AND tokens) | Mais searches |
| Built-in + YAML merge | Valor imediato + customização | Dict global simples |
| Diagnostics aditivos | Sem breaking change MCP | schema_version permanece `1` |

## Definition of Done

1. [x] Aceite PB-062 / PB-033  
2. [x] Testes + cobertura ≥ 80%  
3. [x] ruff + mypy  
4. [x] README + CHANGELOG  
5. [x] Maintainer aprova encerramento / Sprint 10  

## Sprint 10

Entregue em `0.8.0a1` — ver [`Sprint10.md`](Sprint10.md).
