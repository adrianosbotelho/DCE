# Release Windows portable — checklist

**Release alvo:** tag SemVer `vX.Y.Z` (ex.: `v1.11.0`)  
**Artefatos:** `dce-X.Y.Z-windows-x64.zip` + `.sha256`

---

## Pré-requisitos

1. Código na versão desejada (`pyproject.toml` / `dce.__version__` alinhados)
2. Repositório GitHub com Actions habilitadas
3. Tag empurrada: `git tag vX.Y.Z && git push origin vX.Y.Z`

---

## O que o CI faz

Workflow **Windows Portable** (`.github/workflows/windows-portable.yml`):

1. Build PyInstaller → ZIP  
2. Gera `*.zip.sha256`  
3. Upload artifact (sempre)  
4. Se o ref for `refs/tags/v*`, cria/atualiza **GitHub Release** e anexa ZIP + checksum  

`workflow_dispatch` gera só o artifact (sem Release), útil para smoke.

---

## Verificar após a tag

1. Actions → run verde  
2. Releases → assets presentes  
3. Conferir checksum no Windows:

```powershell
Get-FileHash .\dce-1.11.0-windows-x64.zip -Algorithm SHA256
Get-Content .\dce-1.11.0-windows-x64.zip.sha256
```

---

## Ainda fora deste checklist

- Assinatura Authenticode  
- Instalador MSI/Inno  
- Upload PyPI (`scripts/publish.sh` / workflow **Publish**)
