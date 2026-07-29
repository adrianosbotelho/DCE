# SLOs — Dev Context Engine (DCE)

**Status:** Registrados e mensuráveis via `dce bench`  
**Release:** a partir de `0.11.0a1`  
**Backlog:** PB-091

---

## Alvos (p95, índice local SSD)

| Operação | Alvo p95 | Notas |
|----------|----------|-------|
| `build_context` | **&lt; 500 ms** | Pacote completo com budget padrão |
| `search_context` | **&lt; 200 ms** | FTS rankeado, limit 20 |
| `get_document` | **&lt; 50 ms** | Lookup por id |
| `dce index` (Markdown ~1k) | **&lt; 30 s** cold | Medido operacionalmente, não no `bench` |

Fonte arquitetural: [`Architecture.md`](Architecture.md) §14.

---

## Como medir

```bash
dce bench --docs 500 --iterations 30 --format table
```

- Por padrão usa DB **ephemeral** (`.dce/bench.sqlite`) com corpus sintético.
- `--ephemeral/--no-ephemeral` (default ephemeral) — workspace real com `--no-ephemeral`.
- Saída JSON inclui `within_slo` e os alvos em `slo`.

### Interpretação

1. Corpus sintético é **direcional** — o alvo de Architecture cita ~10k docs reais.
2. **Não** use `within_slo` como hard-fail de CI (variância de host/CI shared).
3. Antes de release 1.0, rode o bench em máquina representativa e anexe o JSON às notas.

---

## Registro de evidência (template)

```text
Date:
Host:
dce version:
Command: dce bench --docs N --iterations M
build_context p95:
search_context p95:
get_document p95:
within_slo:
Notes:
```

Guardar sob `docs/bench-results/` (opcional, local) ou na release note.
