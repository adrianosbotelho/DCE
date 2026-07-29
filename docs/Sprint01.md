# Sprint 01 — Planejamento

**Sprint:** 01  
**Release alvo:** 0.1.0a1  
**Status:** 🟢 Concluída (aguardando aprovação de encerramento / Sprint 02)  
**Duração:** Fatia foundation store  
**Última atualização:** 2026-07-29

---

## Objetivo da sprint

Entregar a **primeira fatia vertical testável do motor**: modelos de domínio + SQLite/FTS5 + repositório + `dce init`/`doctor` mínimo — **sem** Context Builder completo ainda, **sem** MCP, **sem** Jira.

> Princípio do processo: *“Cada Sprint deverá implementar apenas uma pequena funcionalidade.”*  
> Por isso Sprint 01 **não** tenta fechar o MVP inteiro.

---

## Resultado

| ID | Item | Status |
|----|------|--------|
| PB-001 | Modelos de domínio | ✅ |
| PB-002 | Ports `DocumentRepository` / `Indexer` / `Clock` | ✅ |
| PB-003 | Schema + FTS5 + migrations (v1) | ✅ |
| PB-004 | `SqliteDocumentRepository` | ✅ |
| PB-005 | `dce init` + `dce doctor` | ✅ |

**Qualidade:** 31 testes passando; cobertura total ≈ **90%** (gate ≥ 80%); ruff + mypy limpos; CI workflow adicionado.

### Decisão local de tokenizer

FTS5 usa **`unicode61`**, não `porter`. Trade-off: menos stemming em inglês; melhor preservação de códigos técnicos (`ORA-12541`). Documentado no CHANGELOG e README.

### Revisão arquitetural

- [x] `domain` sem imports de infra / Typer / SQLite  
- [x] Uma implementação de repositório; Protocol no domain  
- [x] Workspace bootstrap em `infrastructure/storage` (evita application→infra)  
- [x] Sem indexer cruzado / sem MCP / sem Builder (escopo respeitado)  

---

## Escopo original

### Inclui (committed)

| ID | Item | Critérios de aceite |
|----|------|---------------------|
| PB-001 | Modelos de domínio | `Document`, `ContextQuery`, `ContextPackage`, `ContextBudget`, `ScoredDocument` definidos em Pydantic; validação básica; testes unitários |
| PB-002 | Ports | `DocumentRepository` e `Indexer` como `Protocol`; sem dependência de infra |
| PB-003 | Schema + FTS5 + migrations | DB criado do zero; FTS populável; migração versionada; teste de schema |
| PB-004 | `SqliteDocumentRepository` | `upsert_many`, `get`, `search` (FTS), `list_recent`; testes com `tmp_path` |
| PB-005 | `dce init` + `dce doctor` (mínimo) | Cria `dce.yaml` esqueleto + DB; `doctor` reporta schema ok / FTS disponível |

### Explicitamente fora

- Markdown indexer (Sprint 02 candidata)
- Context Builder (Sprint 02/03)
- MCP (após Builder CLI)
- Qualquer chamada de rede
- Tools `search_by_*`

---

## Tarefas técnicas (checklist)

- [x] Packaging mínimo (`pyproject.toml`) — Python 3.12+, pacote `dce`
- [x] Pacotes `domain`, `application`, `infrastructure/storage`, `interfaces/cli`
- [x] Implementar modelos + testes
- [x] Implementar migrations + FTS
- [x] Implementar repositório + testes
- [x] CLI `init` / `doctor`
- [x] ruff + mypy passando
- [x] Atualizar README (como init/doctor)
- [x] Atualizar CHANGELOG
- [x] Revisão arquitetural: domain sem imports de infra

---

## Definition of Done — Sprint 01

1. [x] Todos os itens committed com aceite marcado  
2. [x] `pytest` verde; cobertura ≥ 80% em core  
3. [x] `ruff check` + `mypy` limpos no pacote  
4. [x] README e CHANGELOG atualizados  
5. [x] Nenhum arquivo de código morto intencional  
6. [x] Dependências justificadas (Pydantic, Typer, Rich, PyYAML + dev tools)  
7. [x] Maintainer revisa e **aprova encerramento** antes da Sprint 02  

---

## Sprint 02

Entregue — ver [`Sprint02.md`](Sprint02.md).
