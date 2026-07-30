# Kiro — adoção rápida do DCE

**Status:** Sprint 37 (`1.21.0`)

Guia curto para conectar o [Kiro](https://kiro.dev) ao Dev Context Engine via MCP stdio.

## 1. Preparar o workspace

```bash
pip install -e ".[dev]"   # ou: pip install dev-context-engine
dce init /path/to/workspace
dce index /path/to/workspace
dce doctor /path/to/workspace
```

`dce doctor` deve listar `mcp` (tools estáveis) e `documents` (> 0 após o index).  
Para automação: `dce doctor --json`.

## 2. Configurar MCP no Kiro

```json
{
  "mcpServers": {
    "dce": {
      "command": "dce",
      "args": ["mcp", "--path", "/absolute/path/to/workspace"]
    }
  }
}
```

Use caminho absoluto. O processo MCP **não** escreve prosa em stdout.

## 3. Como o agente deve perguntar

1. Preferir **`build_context`** para perguntas de desenvolvimento.
2. Em dúvida sobre o índice, chamar **`workspace_status`** (espelha `dce doctor --json`).
3. Se não souber slugs, chamar **`list_facets`** (ou `dce facets`).
4. Usar aliases tipados quando o escopo for claro:
   - `search_by_issue` — `PAY-125`
   - `search_by_project` / `search_by_component` / `search_by_technology` / `search_by_tag`
5. `search_memory` só para notas em `.dce/memory`.
6. Respeitar `diagnostics.truncated` e o budget do pacote.

**Dia a dia:** cole o steering pronto (`dce steering` ou passo 5 da UI) nas regras do Kiro —  
veja [`KiroSteering.md`](KiroSteering.md). Assim você **não** precisa pedir o MCP em todo prompt.

Contrato completo: [`MCP.md`](MCP.md).

## 4. Smoke checklist

- [ ] `dce doctor` / MCP `workspace_status` healthy  
- [ ] `dce build "ORA-12541"` retorna documentos  
- [ ] Kiro lista tools DCE (`build_context`, `workspace_status`)  
- [ ] Uma pergunta real no Kiro monta `ContextPackage` com `schema_version: "1"`  

## 5. Windows corporativo + Kiro (guia completo)

**Recomendado:** `dce ui` (interface local) — [`SetupUI.md`](SetupUI.md)

Passo a passo Windows: [`KiroWindows.md`](KiroWindows.md)


