# Product Backlog — Dev Context Engine (DCE)

**Método:** backlog priorizado por valor ao Kiro / redução de risco  
**Prioridade:** MoSCoW dentro de cada horizonte  
**Última atualização:** 2026-07-29

IDs estáveis: `PB-XXX`. Sprint planning referencia estes IDs.

---

## Legenda

| Campo | Valores |
|-------|---------|
| Prioridade | `P0` crítico MVP · `P1` alto · `P2` médio · `P3` baixo |
| MoSCoW | Must / Should / Could / Won't (neste horizonte) |
| Tamanho | XS / S / M / L (relativo) |
| Épico | E1–E10 (ver Roadmap) |

---

## Agora — Foundation & MVP engine (→ 0.1.0)

| ID | Item | P | MoSCoW | Tam | Épico | Notas |
|----|------|---|--------|-----|-------|-------|
| PB-001 | Definir modelos de domínio (`Document`, `ContextQuery`, `ContextPackage`, `ContextBudget`) | P0 | Must | S | E1/E3 | ✅ |
| PB-002 | Portas `DocumentRepository` e `Indexer` | P0 | Must | S | E1 | ✅ |
| PB-003 | Schema SQLite + migrations + FTS5 | P0 | Must | M | E1 | ✅ |
| PB-004 | Implementar `SqliteDocumentRepository` | P0 | Must | M | E1 | ✅ |
| PB-005 | `dce init` cria workspace config + DB | P0 | Must | S | E1 | ✅ |
| PB-006 | Markdown Indexer (glob + frontmatter) | P0 | Must | M | E2 | ✅ |
| PB-007 | `dce index` orquestra indexers habilitados | P0 | Must | S | E2 | ✅ |
| PB-008 | Context Builder v1 (plano simples + assemble + budget) | P0 | Must | M | E3 | ✅ |
| PB-009 | `dce build` / `dce search` / `dce show` CLI | P0 | Must | S | E3 | ✅ |
| PB-010 | Suite pytest domain/application/storage ≥ 80% | P0 | Must | M | — | ✅ |
| PB-011 | Wiring ruff + mypy + CI básico | P1 | Should | S | E10 | ✅ (CI + quality gates) |
| PB-012 | Logging estruturado mínimo | P1 | Should | S | — | ✅ Sprint 23 |

---

## Em seguida — MCP Kiro (→ 0.2.0)

| ID | Item | P | MoSCoW | Tam | Épico | Notas |
|----|------|---|--------|-----|-------|-------|
| PB-020 | Servidor MCP stdio (`dce mcp`) | P0 | Must | M | E4 | ✅ Sprint 04 |
| PB-021 | Tool `build_context` | P0 | Must | S | E4 | ✅ Sprint 04 |
| PB-022 | Tool `search_context` | P0 | Must | S | E4 | ✅ Sprint 04 |
| PB-023 | Tool `get_document` | P0 | Must | XS | E4 | ✅ Sprint 04 |
| PB-024 | Tool `recent_documents` | P0 | Must | XS | E4 | ✅ Sprint 04 |
| PB-025 | Contract tests MCP (golden JSON) | P0 | Must | S | E4 | ✅ Sprint 10 |
| PB-026 | `schema_version` em respostas | P1 | Should | XS | E4 | ✅ Sprint 10 |
| PB-027 | Doc de integração Kiro (README seção) | P1 | Should | S | E4 | ✅ Sprint 10 |

---

## Fontes e qualidade (→ 0.3–0.6)

| ID | Item | P | MoSCoW | Tam | Épico | Notas |
|----|------|---|--------|-----|-------|-------|
| PB-030 | ADR Indexer | P1 | Must | S | E5 | ✅ Sprint 05 |
| PB-031 | Memory Indexer + notas locais | P1 | Should | S | E5 | ✅ Sprint 05 |
| PB-032 | Tool opcional `search_memory` | P2 | Could | XS | E5 | ✅ Sprint 17 |
| PB-033 | Diagnostics ricos no `ContextPackage` | P1 | Should | S | E3/E8 | ✅ Sprint 09 |
| PB-034 | Dicionário de âncoras (ORA-*, etc.) configurável | P1 | Should | S | E8 | ✅ Sprint 12 |
| PB-040 | Jira Import JSON | P1 | Must | M | E6 | ✅ Sprint 06 |
| PB-041 | Jira Import CSV | P1 | Should | M | E6 | ✅ Sprint 06 |
| PB-042 | Mapeamento “solução / lições” (campos custom) | P1 | Should | S | E6 | ✅ Sprint 06 |
| PB-050 | Git Indexer (log + paths) | P1 | Should | L | E7 | ✅ Sprint 07 |
| PB-051 | `related_uris` issue↔PR↔commit | P2 | Could | M | E7 | ✅ Sprint 18 |
| PB-060 | RetrievalPlanner por tipo de query | P1 | Should | M | E8 | ✅ Sprint 08 |
| PB-061 | Boosts title/anchor/freshness | P1 | Should | S | E8 | ✅ Sprint 08 |
| PB-062 | Sinônimos técnicos FTS | P2 | Could | S | E8 | ✅ Sprint 09 |

---

## MCP aliases (somente com evidência)

| ID | Item | P | MoSCoW | Tam | Épico | Notas |
|----|------|---|--------|-----|-------|-------|
| PB-070 | `search_by_issue` | P2 | Could | XS | E4 | ✅ Sprint 25 |
| PB-071 | `search_by_project` | P2 | Could | XS | E4 | ✅ Sprint 29 |
| PB-072 | `search_by_component` | P2 | Could | XS | E4 | ✅ Sprint 30 |
| PB-073 | `search_by_technology` | P2 | Could | XS | E4 | ✅ Sprint 31 |
| PB-074 | `search_by_tag` | P2 | Could | XS | E4 | ✅ Sprint 32 |

**Decisão de backlog:** Won't no horizonte 0.1–0.2; reavaliar após uso real no Kiro.

---

## Jira live & operação (→ 0.6–1.0)

| ID | Item | P | MoSCoW | Tam | Épico | Notas |
|----|------|---|--------|-----|-------|-------|
| PB-080 | Jira REST indexer (opcional) | P2 | Could | L | E9 | ✅ Sprint 22 (thin: JQL search) |
| PB-081 | Procedure Indexer (especialização) | P2 | Could | S | E5 | ✅ Sprint 19 |
| PB-082 | Incident Indexer | P2 | Could | S | E5 | ✅ Sprint 20 |
| PB-083 | Snippet Indexer | P2 | Could | S | E5 | ✅ Sprint 21 |
| PB-090 | Empacotamento PyPI `dce` | P1 | Should | M | E10 | ✅ Sprint 11 (`dev-context-engine`) |
| PB-091 | Benchmarks + registro de SLOs | P2 | Could | M | E10 | ✅ Sprint 13 |
| PB-092 | Hook Git opcional `post-commit` index | P3 | Could | S | E10 | ✅ Sprint 24 |
| PB-093 | Export/import DB backup | P2 | Could | S | E10 | ✅ Sprint 14 |
| PB-094 | Windows portable `dce.exe` (ZIP) | P2 | Could | M | E10 | ✅ Sprint 26 |
| PB-095 | GitHub Release assets (ZIP + SHA-256) | P2 | Could | S | E10 | ✅ Sprint 27 |
| PB-096 | Git bootstrap + cut-release script | P1 | Should | S | E10 | ✅ Sprint 28 |

---

## Won't (explícito — evita overengineering)

| ID | Item | Motivo |
|----|------|--------|
| PB-900 | Banco vetorial / embeddings | Viola requisitos + complexidade |
| PB-901 | Dependência OpenAI / APIs pagas | Fora da missão |
| PB-902 | UI web no MVP | Kiro + CLI |
| PB-903 | Microsserviços / fila | Desnecessário offline |
| PB-904 | Plugin marketplace | Prematuro |
| PB-905 | Multi-tenant cloud | Anti offline-first |

---

## Ordenação sugerida de entrega

```mermaid
flowchart LR
  PB001[PB-001..005] --> PB006[PB-006..007]
  PB006 --> PB008[PB-008..009]
  PB008 --> PB010[PB-010]
  PB010 --> PB020[PB-020..025]
  PB020 --> PB030[PB-030..]
```

---

## Critérios de pronto (Definition of Done) — item de backlog

1. Código tipado (mypy) + ruff limpo nas áreas tocadas  
2. Testes automatizados do comportamento  
3. Docstrings em APIs públicas  
4. CHANGELOG `[Unreleased]` atualizado  
5. Sem código morto / abstração sem uso  
6. Revisão arquitetural breve (ports intactas)  

---

## Sprint atual

Sprint 32 concluída tecnicamente (`1.16.0`).  
PB-074 (`search_by_tag`) — série `search_by_*` completa.  
Próxima: Sprint 33 — **aguardando aprovação do maintainer**.  
Detalhes: [`Sprint32.md`](Sprint32.md) · [`MCP.md`](MCP.md).
