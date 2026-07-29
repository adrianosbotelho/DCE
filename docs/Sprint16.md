# Sprint 16 — Planejamento e entrega

**Sprint:** 16  
**Release alvo:** 1.0.0  
**Status:** 🟢 Concluída (aguardando aprovação de encerramento / Sprint 17)  
**Última atualização:** 2026-07-29

---

## Objetivo

Promover o RC a **`1.0.0` estável**: gates de qualidade, evidência de `dce bench`, checklist fechado, classifier Production — upload PyPI **somente se** houver token do maintainer.

## Resultado

| Item | Status |
|------|--------|
| Version `1.0.0` | ✅ |
| Bench evidence | ✅ `docs/bench-results/` |
| Doctor + backup/restore smoke | ✅ |
| Classifier Production/Stable | ✅ |
| Upload PyPI | ⏸ gated (sem token) |
| Tag Git | ⏸ gated (sem remoto / ação maintainer) |

### Revisão arquitetural

- [x] Sem breaking change vs `1.0.0rc1`
- [x] Contrato MCP v1 permanece
- [x] Checklist 1.0 atualizado com evidências
- [x] Publish explícito como passo humano

---

## Escopo

| Item | Critérios de aceite |
|------|---------------------|
| Version `1.0.0` | pyproject + `__version__` + CHANGELOG |
| Evidência bench | JSON/resumo em `docs/bench-results/` |
| Checklist 1.0 | Itens locais marcados; publish gated |
| Classifier | Development Status :: 5 - Production/Stable |

### Fora de escopo

- Features novas
- Tag Git / GitHub Release sem remoto
- Upload PyPI sem token

## Trade-offs

| Escolha | Motivo | Custo |
|---------|--------|-------|
| 1.0.0 mesmo sem PyPI live | Contrato estável localmente | Índice público atrasado |
| Bench sintético anexado | Evidência reproduzível | Não é corpus 10k real |

## Definition of Done

1. [x] Aceite `1.0.0` local/stable  
2. [x] Testes + cobertura ≥ 80% + build/twine  
3. [x] Bench + smoke backup/doctor  
4. [x] README + CHANGELOG + checklist  
5. [x] Maintainer aprova encerramento / Sprint 17  

## Sprint 17

Entregue em `1.1.0` — ver [`Sprint17.md`](Sprint17.md).
