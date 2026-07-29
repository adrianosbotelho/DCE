# Diagrams — Dev Context Engine (DCE)

Diagramas Mermaid de referência rápida. Fontes canônicas também estão embutidas nos docs principais.

## Contexto do sistema

```mermaid
flowchart TB
  subgraph Sources["Fontes de conhecimento"]
    Jira
    Git
    MD[Markdown]
    ADR[ADRs]
    Proc[Procedimentos]
    Inc[Incidentes]
    Snip[Snippets]
    Mem[Memory]
  end

  Sources --> Indexers
  Indexers --> FTS[(SQLite FTS5)]
  FTS --> CB[Context Builder]
  CB --> MCP[MCP Server]
  MCP --> Kiro
  CB --> CLI[CLI Typer]
```

## Clean Architecture (dependências)

```mermaid
flowchart TB
  I[interfaces: CLI / MCP] --> A[application: use cases]
  A --> D[domain: models + ports]
  INF[infrastructure: sqlite / indexers] --> D
  I --> INF
```

## Fluxo build_context

```mermaid
sequenceDiagram
  participant Kiro
  participant MCP
  participant UC as BuildContext
  participant Plan as RetrievalPlanner
  participant Repo as DocumentRepository
  participant Asm as PackageAssembler

  Kiro->>MCP: build_context
  MCP->>UC: ContextQuery
  UC->>Plan: plan
  Plan-->>UC: RetrievalPlan
  UC->>Repo: search loops
  Repo-->>UC: ScoredDocuments
  UC->>Asm: assemble + budget
  Asm-->>UC: ContextPackage
  UC-->>MCP: ContextPackage
  MCP-->>Kiro: structured JSON
```

## Roadmap simplificado

```mermaid
flowchart LR
  D[Docs 0.0] --> C[Core 0.1]
  C --> M[MCP 0.2]
  M --> S[ADR/Memory 0.3]
  S --> J[Jira import 0.4]
  J --> G[Git 0.5]
  G --> Q[Retrieval 0.6]
  Q --> R1[1.0 stable contracts]
```
