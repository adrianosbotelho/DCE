# Setup UI — `dce ui`

**Status:** Sprint 44 (`1.28.0`) · ADR: [`adr/ADR-006.md`](adr/ADR-006.md)

Assistente **local** (só `127.0.0.1`) para pessoas que não usam linha de comando.

## Abrir

```bash
# macOS / Linux / pip
dce ui --path /caminho/do/projeto

# Windows portable
.\dce.exe ui --path C:\work\meu-projeto
```

Abre o navegador em `http://127.0.0.1:8765/`.

Opções úteis:

```bash
dce ui --path . --port 8765 --no-open
dce ui --path C:\work\app --command C:\Tools\dce\dce.exe
```

## O que a tela faz

1. Escolher / criar workspace (`dce.yaml` + SQLite)
2. Criar documento de exemplo (opcional)
3. Indexar fontes
4. Mostrar saúde (doctor)
5. Gerar e copiar JSON MCP do Kiro
6. Copiar **steering** (regras de uso no dia a dia) — [`KiroSteering.md`](KiroSteering.md)
7. Testar `build_context`

Tudo offline. Não envia dados para internet.

## Fluxo recomendado no Windows corporativo

1. Extrair `dce-*-windows-x64.zip` em `C:\Tools\dce`
2. `.\dce.exe ui --path C:\work\meu-projeto`
3. Na UI: **Criar / inicializar** → **Criar doc de exemplo** (ou use docs reais) → **Indexar** → **Copiar** JSON → **Copiar steering** → colar no Kiro
4. Perguntar no chat em linguagem natural (sem precisar pedir o MCP a cada vez)

Guia completo: [`KiroWindows.md`](KiroWindows.md)
