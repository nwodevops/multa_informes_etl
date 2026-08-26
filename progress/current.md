# Sesión activa — rama `windows` (exclusiva Win)

## Feature activa

| Campo | Valor |
|---|---|
| ID | `fase-remote-deploy` |
| Status | `in_progress` |
| Criterio | `init.bat` o `wf_main_win.hwf` → Success + DW (OK) K1–K5 |

## Plan

1. Working tree limpio: cleanup `python/io`, AGENTS Win-only, docs.
2. En PC Win: `git pull` → `.\switch-env.ps1 remote` → `wf_main_win` / `init.bat`.
3. Si OK → `fase-remote-deploy` = done.

## Comandos Win

```powershell
cd D:\Eder\workspace_etl_oefa\multa_informes_etl
git checkout windows
git pull
.\switch-env.ps1 remote
init.bat
# o Hop: wf_main_win.hwf
```
