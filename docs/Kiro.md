# Kiro — adoção rápida do DCE

**Status:** Sprint 33 (`1.17.0`)

Guia curto para conectar o [Kiro](https://kiro.dev) ao Dev Context Engine via MCP stdio.

## 1. Preparar o workspace

```bash
pip install -e ".[dev]"   # ou: pip install dev-context-engine
dce init /path/to/workspace
dce index /path/to/workspace
dce doctor /path/to/workspace
```

`dce doctor` deve listar `mcp` (tools estáveis) e `documents` (> 0 após o index).

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
2. Usar aliases tipados quando o escopo for claro:
   - `search_by_issue` — `PAY-125`
   - `search_by_project` / `search_by_component` / `search_by_technology` / `search_by_tag`
3. `search_memory` só para notas em `.dce/memory`.
4. Respeitar `diagnostics.truncated` e o budget do pacote.

Contrato completo: [`MCP.md`](MCP.md).

## 4. Smoke checklist

- [ ] `dce doctor` healthy  
- [ ] `dce build "ORA-12541"` retorna documentos  
- [ ] Kiro lista tools DCE (`build_context` presente)  
- [ ] Uma pergunta real no Kiro monta `ContextPackage` com `schema_version: "1"`  

## 5. Windows portable

Se o ambiente for Windows sem Python: baixe o ZIP da Release (`dce.exe`) — [`Windows.md`](Windows.md).
