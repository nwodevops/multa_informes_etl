# Sesión activa

> El líder (humano o agente principal) mantiene este archivo. Al cerrar sesión, resumir en [`history.md`](history.md).

## Feature activa

| Campo | Valor |
|---|---|
| ID | `fase-remote-deploy` |
| Status | `in_progress` |
| Criterio | Win: `git pull` + `.\switch-env.ps1 remote` + `wf_main_win` → Success + DW (OK) K1–K5 |

## Plan

1. Docs reorg + `vista-general` / kimball + `cargar_dw` schema USER: **done** (rama `windows`).
2. Re-correr Hop Win tras `git pull` — confirmar sin `ORA-00942`.
3. Si OK → marcar `fase-remote-deploy` done + entrada en `history.md`.

## Comandos

```powershell
cd D:\Eder\workspace_etl_oefa\multa_informes_etl
git pull
.\switch-env.ps1 remote
# Hop GUI → wf_main_win.hwf  |  init.bat
```
