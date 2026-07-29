# Sprint 25 — Planejamento e entrega

**Sprint:** 25  
**Release alvo:** 1.9.0  
**Status:** ✅ Concluída (aguardando aprovação para Sprint 26)  
**Última atualização:** 2026-07-29

---

## Objetivo

Entregar **PB-070 `search_by_issue`**: alias MCP tipado para chaves de issue (evidência: QueryKind.ISSUE, Jira, `issue:` related_uris).

## Escopo

| ID | Item | Critérios de aceite | Status |
|----|------|---------------------|--------|
| PB-070 | `search_by_issue` | Tool MCP; normaliza KEY; FTS; contract test | ✅ |

### Fora de escopo

- Demais `search_by_*` (project/component/…)
- Publish PyPI / tags

## Design

```mermaid
flowchart LR
  SBI[search_by_issue KEY] --> Norm[normalize KEY]
  Norm --> SC[search_context text=KEY]
  SC --> Docs[jira/git/docs hits]
```

### Trade-offs

| Escolha | Motivo | Custo |
|---------|--------|-------|
| Só issue (não project/tag) | Evidência forte; thin slice | Outros aliases depois |
| schema_version 1 | Aditivo (ADR-004) | 6ª tool estável |
| Sem forçar `tags=` | FTS no body/title também | Menos precisão vs tag-only |

## Entregas

| Item | Detalhe |
|------|---------|
| Version `1.9.0` | pyproject + `__version__` + CHANGELOG |
| MCP `search_by_issue` | `normalize_issue_key` + FTS |
| Contract | seed Jira + assert PAY-125 |

## Definition of Done

1. [x] Aceite PB-070  
2. [x] Testes + qualidade  
3. [x] Docs + CHANGELOG  
4. [x] Maintainer aprova encerramento / Sprint 26  

## Sprint 26

Entregue em `1.10.0` — ver [`Sprint26.md`](Sprint26.md).
