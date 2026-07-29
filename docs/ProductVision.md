# Product Vision — Dev Context Engine (DCE)

**Status:** Produto estável (`1.26.0+`) · Context Builder + MCP Kiro  
**Última atualização:** 2026-07-29

---

## 1. Declaração de visão

O **Dev Context Engine (DCE)** é um motor offline que **constrói pacotes de contexto estruturados** a partir do conhecimento técnico corporativo disperso, e os entrega a agentes de IA — em especial o **Kiro** — via MCP, durante tarefas reais de desenvolvimento de software.

A memória (notas curadas) é **uma fonte**. O produto é o **Context Builder**.

---

## 2. Problema

Em organizações de software, o conhecimento relevante para desenvolver e operar sistemas vive fragmentado:

| Fonte | O que se perde com o tempo |
|-------|----------------------------|
| Jira | Soluções, comentários úteis, padrões de falha |
| Git / PRs / commits | Motivo da mudança, riscos, arquivos tocados |
| ADRs | Decisões e trade-offs esquecidos |
| Markdown / wikis | Procedimentos e runbooks desatualizados ou invisíveis |
| Incidentes | Postmortems que não reaparecem na próxima crise |
| Snippets / conversas | Truques locais que nunca viram documentação |

Consequências: onboarding lento, reinvestigação, reincidência de incidentes, decisões arquiteturais contraditórias.

**Dor do agente (Kiro):** sem contexto corporativo, o agente inventa, alucina política interna ou ignora lições já pagas pela equipe.

---

## 3. Solução proposta

1. **Indexar** fontes heterogêneas em documentos canônicos locais (SQLite + FTS5).
2. **Construir contexto** automaticamente a partir de uma pergunta ou âncora (issue, erro, componente).
3. **Entregar** pacotes estruturados ao Kiro via MCP (não prosa livre).

```mermaid
flowchart LR
  Q["Pergunta / âncora<br/>ex: ORA-12541"] --> CB[Context Builder]
  CB --> R[Retrieve multi-fonte]
  R --> Rank[Rank + dedupe + budget]
  Rank --> Pkg[ContextPackage estruturado]
  Pkg --> Kiro
```

---

## 4. Para quem

| Persona | Necessidade |
|---------|-------------|
| **Agente Kiro** (consumidor primário) | Contexto rápido, consistente, estruturado, com orçamento de tamanho |
| Engenheiro sênior | Reduzir “já resolvemos isso” e recuperar ADRs/incidentes |
| Tech lead / arquiteto | Preservar decisões e padrões por componente/tecnologia |
| Novo na equipe | Atalho para histórico real (issues + soluções), não só wiki |
| Maintainer DCE | Operar offline, CLI simples, um DB por workspace |

**Não-persona (agora):** time de compliance buscando GRC enterprise; produto SaaS multi-tenant.

---

## 5. Escopo do produto

### Em escopo

- Indexadores independentes (Markdown, Jira, Git, ADR, Snippet, Procedure, Incident, …)
- Store local SQLite com FTS5 + metadados filtráveis
- Context Builder com ranking heurístico e orçamento de tokens/caracteres
- Servidor MCP (stdio) otimizado para Kiro
- CLI Typer para indexação, inspeção e diagnóstico
- Importação Jira via API **ou** JSON/CSV (ambientes restritos)
- 100% offline em runtime de consulta

### Fora de escopo (anti-escopo explícito)

| Item | Motivo |
|------|--------|
| Base de conhecimento wiki completa / CMS | Não é o produto |
| Clone de ai-memory | Memória é fonte, não o núcleo |
| Banco vetorial / embeddings / OpenAI | Viola offline + custo + complexidade |
| Busca semântica “mágica” como promessa | FTS + metadados + âncoras estruturadas |
| UI web rica no MVP | Kiro + CLI bastam |
| Orquestração multi-agente | Fora do núcleo |
| Sync cloud / multi-tenant SaaS | Contradiz offline-first |

---

## 6. Fase 1 — Discovery (análise crítica)

### 6.1 O que está certo no briefing

- Separar **indexação** de **construção de contexto**.
- Indexers desacoplados.
- MCP estruturado para o consumidor real (Kiro).
- SQLite FTS5 alinhado a offline, footprint baixo e zero vendor lock-in de IA.
- Jira como fonte rica, com fallback JSON/CSV.

### 6.2 Melhorias propostas (questionamento de requisitos)

| Requisito original | Questionamento | Proposta |
|--------------------|----------------|----------|
| Muitas tools MCP (`search_by_*`) | Superfície ampla demais cedo; duplica filtros | MVP: `build_context`, `search_context`, `get_document`, `recent_documents`; filtros como parâmetros. Demais tools como *aliases* finos só se o Kiro precisar |
| `search_memory` separado | Risco de produto paralelo | Memory = `source_type=memory` + tool opcional fina; não um subsistema |
| “Sempre pesquisar 8+ fontes” | Latência e ruído | Context Builder usa **plano de recuperação** por tipo de pergunta (erro Oracle ≠ ADR) |
| Issue Jira com “lições aprendidas” nativo | Campo raramente existe | Campo opcional + enrichment local (nota/memory ligada à issue) |
| Jira API no MVP | Auth, rede, rate limit vs offline | **MVP: Markdown + ADR + import JSON/CSV**; API Jira depois |
| “Respostas rápidas” sem SLO | Inefável | SLOs explícitos por operação (ver Architecture) |
| Pacote de contexto sem budget | Estoura contexto do Kiro | `ContextBudget` obrigatório (chars/docs/fontes) |

### 6.3 Riscos

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| FTS5 fraco em português / sinônimos | Recall baixo | Dicionário de sinônimos técnico + âncoras (ORA-*, chaves Jira) + campos boost |
| Índice desatualizado | Contexto errado | `dce index` incremental + `indexed_at` + hook Git opcional |
| Over-fetch no Builder | CPU/latência | Limites por fonte, parallelismo controlado, cache de query |
| Escopo “todas as fontes” no dia 1 | Atraso infinito | MVP estreito; roadmap por indexer |
| Schemas MCP instáveis | Quebra Kiro | Versionar tools; contract tests |
| Expectativa de “semântica vetorial” | Frustração | Documentar honestamente: lexical + estrutura + ranking |
| Dados sensíveis no SQLite | Vazamento local | `.gitignore` do DB; docs de hygiene; sem telemetria |

### 6.4 Simplificações deliberadas

1. **Um workspace = um arquivo SQLite** (sem cluster).
2. **Documento canônico único** (`Document`) para todas as fontes.
3. **Sem plugin marketplace** no MVP — indexers in-process registrados via entry points depois.
4. **Sem fila/worker** — indexação CLI síncrona/incremental.
5. **Sem ORM pesado** — SQL explícito + repositórios finos.
6. **Ranking v1 = BM25 + boosts de metadados** (não ML).

### 6.5 Critérios de sucesso do produto (12–18 meses)

- Kiro usa `build_context` como hábito em tarefas de bugfix / onboarding técnico.
- Tempo médio para “achar solução já conhecida” cai mensuravelmente (pesquisa qualitativa com time).
- Índice de um monorepo típico + export Jira cabe em máquina de desenvolvedor sem dor.
- Novos indexers entram sem alterar o Context Builder (OCP).

---

## 7. Diferenciação

| Alternativa | Diferença do DCE |
|-------------|------------------|
| Wiki / Confluence search | Não monta pacote multi-fonte para agente |
| Jira search | Uma fonte; sem ADRs/Git/procedimentos unidos |
| RAG vetorial cloud | Custo, rede, vendor; DCE é lexical offline |
| ai-memory / notes agents | Memória pessoal ≠ motor de contexto corporativo |
| grep / ripgrep | Arquivos, não conhecimento estruturado + ranking |

---

## 8. Princípios de design de produto

1. **Contexto &gt; busca** — a pergunta do usuário termina em `ContextPackage`, não em lista crua.
2. **Estrutura &gt; prosa** — MCP retorna objetos tipados.
3. **Âncoras &gt; similaridade vaga** — chaves de erro, issue keys, componentes.
4. **Honestidade lexical** — não fingir embeddings.
5. **Evolução por indexer** — valor incremental sem reescrever o núcleo.

---

## 9. MVP (definição)

O MVP é bem-sucedido quando:

1. É possível indexar um diretório Markdown/ADR local.
2. `build_context("ORA-12541")` (ou query equivalente) devolve um `ContextPackage` JSON com seções tipadas e documentos ranqueados.
3. O mesmo pacote é exposto via MCP stdio consumível pelo Kiro.
4. Tudo roda offline, com testes ≥ 80% nas partes core, sem dependências de IA externa.

Detalhamento: [`Sprint01.md`](Sprint01.md) e [`Roadmap.md`](Roadmap.md).

---

## 10. Aprovação

Esta visão alimenta Arquitetura, Backlog e Sprint 01.  
**Nenhuma implementação até aprovação explícita do maintainer.**
