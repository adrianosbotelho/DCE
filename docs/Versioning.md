# Versioning — Dev Context Engine (DCE)

**Última atualização:** 2026-07-29  
**Esquema:** [Semantic Versioning 2.0.0](https://semver.org/)

---

## 1. Formato

`MAJOR.MINOR.PATCH` — exemplo: `0.2.1`

Pré-releases (PEP 440): `1.0.0rc1`, `1.0.0rc2`, …

---

## 2. O que incrementa o quê

| Mudança | Incremento | Exemplos |
|---------|------------|----------|
| Bug fix sem mudar contrato | PATCH | Correção FTS; crash no `doctor` |
| Funcionalidade compatível | MINOR | Novo indexer; nova tool MCP **aditiva** |
| Breaking change | MAJOR | Remover tool; renomear campo JSON; migration incompatível sem upgrade path |

`1.0.0rcN` foi a fase de validação.  
`1.0.0` marca o contrato MCP `schema_version: "1"` como **estável** (ver [`ReleaseChecklist-1.0.md`](ReleaseChecklist-1.0.md)).  
`1.1.0` adiciona tool MCP `search_memory` (aditivo; `schema_version` permanece `"1"`).

---

## 3. Superfícies versionadas

1. **Pacote Python / CLI** (`dce` command)
2. **Schema SQLite** (`schema_version` interno)
3. **MCP response** (`schema_version` no payload)
4. **Config `dce.yaml`** (campos documentados)

Mudança breaking em qualquer superfície pública → MAJOR (ou nota explícita em 0.x).

---

## 4. Compatibilidade MCP (Kiro)

- Adicionar campo opcional → MINOR  
- Adicionar tool nova → MINOR  
- Remover/renomear tool ou campo required → MAJOR  
- Mudar semântica de `build_context` de forma incompatível → MAJOR  

- Contract tests protegem regressões acidentais.
- Documento normativo: [`MCP.md`](MCP.md) + [ADR-004](adr/ADR-004.md).

---

## 5. Schema SQLite

- Cada migration incrementa inteiro monotônico
- Upgrade automático no startup/`doctor`
- Downgrade não é prometido; backup do arquivo DB antes de majors

---

## 6. Tags Git

- `vMAJOR.MINOR.PATCH` para releases
- Tags `sprint-NN` opcionais (não substituem SemVer)

---

## 7. Changelog

Keep a Changelog — ver raiz [`CHANGELOG.md`](../CHANGELOG.md).

Toda release taggeada **deve** ter seção correspondente.
