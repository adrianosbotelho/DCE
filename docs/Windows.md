# Windows portable — DCE

**Status:** Sprint 27 (`1.11.0`)  
**Artefato:** `dce-<version>-windows-x64.zip` (+ `.sha256`) contendo `dce.exe` + `README-WINDOWS.txt`

---

## O que é

Pacote **portátil** (sem instalador MSI/Setup): extrair o ZIP e usar `dce.exe`.

Não substitui o wheel PyPI; é um caminho conveniente para máquinas Windows / Kiro.

---

## Como obter

### GitHub Release (recomendado)

1. Baixar em **Releases** o asset `dce-<version>-windows-x64.zip`  
2. Conferir o arquivo `.sha256`  
3. Detalhes do processo: [`ReleaseWindows.md`](ReleaseWindows.md)

### CI artifact (smoke / sem tag)

1. GitHub Actions → workflow **Windows Portable** → *Run workflow*  
2. Baixar o artifact `dce-windows-x64`

### Build local (só em Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,portable]"
.\scripts\build_windows_portable.ps1
```

Saída:

- `dist\dce-<version>-windows-x64.zip`
- `dist\dce-<version>-windows-x64.zip.sha256`

> PyInstaller **não** gera `.exe` Windows a partir de macOS/Linux.

---

## Uso rápido

**Recomendado (sem CLI avançada):** interface local — ver [`SetupUI.md`](SetupUI.md)

```powershell
Expand-Archive dce-1.27.0-windows-x64.zip -DestinationPath C:\Tools\dce
cd C:\Tools\dce
.\dce.exe --version
.\dce.exe ui --path C:\work\meu-projeto
```

Alternativa CLI:

```powershell
.\dce.exe init C:\work\meu-projeto
.\dce.exe index C:\work\meu-projeto
.\dce.exe doctor C:\work\meu-projeto
```

Guia Kiro: [`KiroWindows.md`](KiroWindows.md)

---

## Kiro MCP

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

Use caminhos **absolutos**. Logs do DCE vão para stderr (stdout fica limpo para MCP).

---

## Limitações

| Item | Nota |
|------|------|
| SmartScreen | Binário não assinado pode alertar |
| Tamanho | Onefile embute runtime Python + deps |
| Startup | Primeira execução do onefile é mais lenta |
| Jira REST | Continua opt-in via env `JIRA_*` |

---

## Arquivos de packaging

- `packaging/pyinstaller/dce.spec`
- `packaging/pyinstaller/run_dce.py`
- `scripts/build_windows_portable.ps1`
- `.github/workflows/windows-portable.yml`
- [`ReleaseWindows.md`](ReleaseWindows.md)
