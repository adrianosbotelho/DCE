# Sprint 26 — Planejamento e entrega

**Sprint:** 26  
**Release alvo:** 1.10.0  
**Status:** ✅ Concluída (aguardando aprovação para Sprint 27)  
**Última atualização:** 2026-07-29

---

## Objetivo

Entregar **`dce.exe` portátil em ZIP** para Windows (sem instalador MSI/Setup) — build via PyInstaller + artefato CI.

## Escopo

| ID | Item | Critérios de aceite | Status |
|----|------|---------------------|--------|
| PB-094 | Windows portable zip | Spec + PowerShell + GHA + docs Kiro | ✅ |

### Fora de escopo

- Inno Setup / MSI / assinatura SmartScreen
- Cross-compile a partir de macOS
- Scoop/Chocolatey

## Design

```mermaid
flowchart LR
  Win[windows-latest CI] --> PyI[PyInstaller onefile]
  PyI --> Exe[dce.exe]
  Exe --> Zip[dce-VERSION-windows-x64.zip]
  Zip --> User[extrair + Kiro MCP]
```

### Trade-offs

| Escolha | Motivo | Custo |
|---------|--------|-------|
| onefile `.exe` | Portátil simples | Startup mais lento; zip maior |
| Build só no Windows/CI | PyInstaller não cross-compila | Precisa GHA ou máquina Win |
| Sem assinatura | Thin slice | SmartScreen pode alertar |

## Entregas

| Item | Detalhe |
|------|---------|
| Version `1.10.0` | pyproject + `__version__` + CHANGELOG |
| `packaging/pyinstaller/` | `dce.spec` + `run_dce.py` |
| `scripts/build_windows_portable.ps1` | Build + ZIP |
| Workflow | `.github/workflows/windows-portable.yml` |
| Docs | [`Windows.md`](Windows.md) |

## Definition of Done

1. [x] Spec + scripts + workflow  
2. [x] Docs Windows/Kiro  
3. [x] Version 1.10.0 + CHANGELOG + testes de presença  
4. [x] Maintainer aprova encerramento / Sprint 27  

## Sprint 27

Entregue em `1.11.0` — ver [`Sprint27.md`](Sprint27.md).
