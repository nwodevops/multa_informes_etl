# Sesión activa — rama `windows` (exclusiva Win)

## Feature activa

| Campo | Valor |
|---|---|
| ID | `fase-remote-deploy` |
| Status | `in_progress` |
| Criterio | `init.bat` o `wf_main_win.hwf` → Success + DW (OK) K1–K5 |

> Merge `linux` → `windows`: F1/F2 Google Sheets, `MI_DIM_OD`/`MI_DIM_ORGANO_UNIDAD`, vistas `VW_MC_*`, amarre H9 detalle, linaje solo `ID_FUENTE`. Lote puntos 2–7 cerrado en linux (`progress/impl_mejoras-kimball-2-7.md`).

## Plan

1. En PC Win: `git pull` → `.\switch-env.ps1 remote` → `wf_main_win` / `init.bat` (requiere `client_secret.json` para Sheets).
2. Si OK → `fase-remote-deploy` = done.

## Comandos Win

```powershell
cd D:\Eder\workspace_etl_oefa\multa_informes_etl
git checkout windows
git pull
.\switch-env.ps1 remote
init.bat
# o Hop: wf_main_win.hwf
```
