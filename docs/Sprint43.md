# Sprint 43 — Planejamento e entrega

**Sprint:** 43  
**Release:** 1.27.0  
**Status:** ✅ Concluída  

## Objetivo

**PB-107** — interface web **local** (`dce ui`) para configurar workspace, indexar, validar e gerar JSON MCP do Kiro sem CLI avançada.

## Escopo

| Item | Status |
|------|--------|
| `dce ui` localhost-only | ✅ |
| Wizard: init / sample / index / status / MCP JSON / build smoke | ✅ |
| ADR-006 | ✅ |
| Bundle static HTML no wheel + PyInstaller | ✅ |

## Como usar (Windows portable)

```powershell
cd C:\Tools\dce
.\dce.exe ui --path C:\work\meu-projeto
# abre http://127.0.0.1:8765/
```
