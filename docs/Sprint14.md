# Sprint 14 — Planejamento e entrega

**Sprint:** 14  
**Release alvo:** 0.12.0a1  
**Status:** 🟢 Concluída  
**Última atualização:** 2026-07-29

---

## Objetivo

Entregar **PB-093**: backup/restore seguro do índice SQLite (API online backup), com CLI e atualização do runbook — último gap operacional antes de `1.0.0rc1`.

## Resultado

| ID | Item | Status |
|----|------|--------|
| PB-093 | Export/import DB backup | ✅ |

### Revisão arquitetural

- [x] `sqlite3.Connection.backup()` (WAL-safe)
- [x] Manifest JSON opcional
- [x] Restore exige `--force` se destino existe
- [x] Operations.md atualizado

---

## Escopo

| ID | Item | Critérios de aceite |
|----|------|---------------------|
| PB-093 | Export/import DB backup | `dce backup` / `dce restore`; snapshot consistente (WAL-safe) |

### Fora de escopo

- Claim `1.0.0` / `1.0.0rc1`
- Upload PyPI
- Backup completo de `imports/` / git objects / memory tree

## Design

```mermaid
flowchart LR
  Live[(dce.sqlite WAL)] --> API[sqlite3 backup]
  API --> File[backup.sqlite]
  File --> Restore[dce restore --force]
  Restore --> Live
```

### Trade-offs

| Escolha | Motivo | Custo |
|---------|--------|-------|
| `Connection.backup()` | Snapshot consistente com WAL | Só DB (não memory files) |
| Manifest JSON opcional | Auditoria / schema_version | Arquivo extra |
| Restore exige `--force` | Evita overwrite acidental | UX um pouco mais verbosa |

## Definition of Done

1. [x] Aceite PB-093  
2. [x] Testes + cobertura ≥ 80%  
3. [x] ruff + mypy  
4. [x] README + CHANGELOG + Operations  
5. [x] Maintainer aprova encerramento / Sprint 15  

## Sprint 15

Entregue em `1.0.0rc1` — ver [`Sprint15.md`](Sprint15.md).
