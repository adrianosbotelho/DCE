# Kiro steering — uso no dia a dia

**Status:** Sprint 44 (`1.28.0`)

Com o MCP do DCE conectado, o agente **não** precisa ser lembrado em todo prompt.
Cole uma regra / steering no Kiro para ele chamar `build_context` sozinho quando fizer sentido.

## Texto pronto (copiar)

Gere o texto canônico:

```bash
dce steering
# ou na UI: dce ui → passo “Steering do Kiro” → Copiar
```

Também disponível em: `dce steering --format json`

## Onde colar no Kiro

Cole nas **regras / steering / project instructions** do Kiro (nome exato depende da versão do produto).
Reinicie o chat se a regra não for aplicada imediatamente.

## Comportamento esperado

| Situação | DCE? |
|----------|------|
| Bug / ORA-* / procedimento / ADR / incidente / ticket | Sim → `build_context` |
| Refatorar código já aberto / dúvida genérica de linguagem | Não |

Detalhes MCP: [`MCP.md`](MCP.md) · Setup: [`SetupUI.md`](SetupUI.md)
