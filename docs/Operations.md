# Operations Runbook — Dev Context Engine (DCE)

**Status:** Operação local / offline  
**Release:** a partir de `0.11.0a1`

---

## Ciclo diário (desenvolvedor)

```bash
# 1. Bootstrap (uma vez)
dce init .
# opcional: editar dce.yaml (indexers, synonyms, anchors, budget)

# 2. Indexar fontes
dce index .
dce index . --source git          # se habilitado / necessário
dce index . --source jira_import  # após dropar JSON/CSV em imports/jira

# 3. Validar saúde / descobrir slugs
dce doctor .
dce doctor . --json
dce facets . --json
dce tools --json
dce index . --json

# 4. Consultar
dce build "ORA-12541"
dce search "listener"
dce recent --path . --format table
dce show <document_id>

# 5. Servir o Kiro (stdio — não misturar prosa no stdout)
dce mcp --path /absolute/path/to/workspace
```

Contrato MCP: [`MCP.md`](MCP.md).

---

## Backup e recovery

```bash
# Snapshot WAL-safe do índice
dce backup --path . --output backups/dce.sqlite

# Restore (exige --force se o DB atual existir)
dce restore --path . --input backups/dce.sqlite --force
dce doctor .
```

| Artefato | Caminho típico | Ação |
|----------|----------------|------|
| Índice | `.dce/dce.sqlite` | `dce backup` / `dce restore` |
| Manifest | `*.sqlite.manifest.json` | Metadados (schema / versão) |
| Config | `dce.yaml` | Versionar no git do workspace (sem segredos) |
| Memória | `.dce/memory/**` | Backup junto do workspace |
| Procedures | `.dce/procedures/**` | Runbooks tipados (`source_type=procedure`) |
| Incidents | `.dce/incidents/**` | Postmortems tipados (`source_type=incident`) |
| Snippets | `.dce/snippets/**` | Código/comandos tipados (`source_type=snippet`) |
| Jira REST | env `JIRA_*` | Opt-in; nunca obrigatório offline |

### Jira REST (opcional)

```bash
export JIRA_BASE_URL=https://your.atlassian.net
export JIRA_EMAIL=you@example.com
export JIRA_API_TOKEN=...   # Cloud API token
# ou: export JIRA_PAT=...   # Bearer / personal access token

# dce.yaml → indexers.jira_rest.enabled: true
dce index . --source jira_rest
```

Sem credenciais ou com falha de rede, o indexer **só registra warning e segue** — o restante do `dce index` e consultas offline continuam ok.

Migrations são **forward-only**. Após upgrade do pacote `dev-context-engine`, `doctor` / abertura do DB aplica schema novo.

---

## Upgrade do pacote

```bash
pip install -U dev-context-engine
dce --version
dce doctor .
dce index .   # se indexers mudaram
```

---

## Diagnóstico rápido

| Sintoma | Checagem |
|---------|----------|
| `Config not found` | `dce init` no path certo |
| `Missing database` | `dce init` ou restore do sqlite |
| Resultados vazios | `dce index`; filtros `source_type`; sinônimos/âncoras |
| MCP “mudo” / quebrado | Garantir que nada escreve em stdout além do protocolo |
| Latência alta | `dce bench`; ver [`SLOs.md`](SLOs.md) |
| Debug indexer | `dce -v --log-format json index .` (logs em stderr) |

### Logging

```bash
dce --verbose index .
dce --log-format json -v doctor .
export DCE_LOG_LEVEL=DEBUG
export DCE_LOG_FORMAT=json
```

Logs vão **sempre para stderr** (MCP stdio permanece limpo).

### Git hook (opcional)

```bash
dce hooks install .     # post-commit → dce index --source git (soft-fail)
dce hooks status .
dce hooks uninstall .
```

O hook nunca falha o `git commit`. `dce doctor` mostra o status quando `.git` existe.

---

## Benchmarks

```bash
dce bench --format table
```

Detalhes e alvos: [`SLOs.md`](SLOs.md).

---

## O que não fazer

- Não apontar o MCP para um workspace sem `dce index` recente esperado
- Não commitar dumps Jira com dados sensíveis em repos públicos
- Não colocar tokens Jira no `dce.yaml` (só env)
- Não prometer SLO de 10k docs com base só no corpus sintético do `bench`
