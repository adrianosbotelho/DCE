# Guia prático — DCE no Windows corporativo + Kiro

**Versão alvo:** `1.28.0`  
**Modo recomendado:** portable (`dce.exe`) + **interface web local** (`dce ui`)

Não precisa de Python, PyPI nem internet na máquina Windows.

---

## O que copiar (Mac → Windows)

Da Release: https://github.com/adrianosbotelho/DCE/releases/tag/v1.28.0  
(ou a tag mais nova)

| Arquivo | Para quê |
|---------|----------|
| `dce-*-windows-x64.zip` | App (`dce.exe`) |
| `*.sha256` | Opcional |

---

## Na Windows — instalar e configurar (sem CLI avançada)

### 1. Extrair

```powershell
Expand-Archive .\dce-1.28.0-windows-x64.zip -DestinationPath C:\Tools\dce -Force
cd C:\Tools\dce
.\dce.exe --version
```

Se o SmartScreen bloquear: *More info* → *Run anyway*.

### 2. Abrir a interface de configuração

```powershell
.\dce.exe ui --path C:\work\meu-projeto
```

O navegador abre em **http://127.0.0.1:8765/**.

Na tela, siga os passos:

1. **Criar / inicializar** o workspace  
2. **Criar doc de exemplo** (ou já tenha markdown em `docs\`)  
3. **Indexar agora**  
4. Confira se o status fica **healthy**  
5. Em “Comando DCE no Kiro”, use `C:\Tools\dce\dce.exe`  
6. **Gerar JSON** → **Copiar**  
7. **Copiar steering** (passo 5) e colar nas regras do Kiro — [`KiroSteering.md`](KiroSteering.md)  
8. **Testar build_context** com `ORA-12541`

Detalhes da UI: [`SetupUI.md`](SetupUI.md)

### 3. Colar no Kiro

Cole o JSON copiado nas configurações MCP do Kiro e reinicie o servidor MCP.

Exemplo esperado:

```json
{
  "mcpServers": {
    "dce": {
      "command": "C:\\Tools\\dce\\dce.exe",
      "args": ["mcp", "--path", "C:\\work\\meu-projeto"]
    }
  }
}
```

### 4. Testar no chat do Kiro

- *“Use workspace_status do DCE”*  
- *“Use build_context com texto ORA-12541 e resuma os títulos”*

---

## Alternativa (só se a pessoa souber CLI)

```powershell
.\dce.exe init C:\work\meu-projeto
.\dce.exe index C:\work\meu-projeto
.\dce.exe doctor C:\work\meu-projeto
```

Prefira a UI para o time.

---

## Offline

O DCE em uso normal **não acessa** internet/PyPI. A UI escuta só `127.0.0.1`.

---

## Referências

- UI: [`SetupUI.md`](SetupUI.md)  
- Portable: [`Windows.md`](Windows.md)  
- MCP: [`MCP.md`](MCP.md)  
- Releases: https://github.com/adrianosbotelho/DCE/releases  
