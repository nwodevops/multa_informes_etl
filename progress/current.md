# Sesión activa — rama `windows` (exclusiva Win)

## Feature activa

| Campo | Valor |
|---|---|
| ID | `fase-remote-deploy` |
| Status | `in_progress` |
| Criterio | `wf_main_win` / `init.bat` → Success + POST-CARGA ≈ 990/281/534/1271 + `MI_AUD_*` = STG; sin VW/DQ/QA/K en Oracle |

## Hecho reciente (ambas ramas)

- `dw-wipe-canonico-aud` = **done** (validado en linux): wipe `MI_*`/`VW_*`, DDL solo `01`+`02`(+`05`), enrich `07`, audit `MI_AUD_*`; DQ/QA/K no se publican.

## Plan

1. En PC Win: `git pull` → `.\switch-env.ps1 remote` → `wf_main_win` / `init.bat` (`client_secret.json`).
2. Confirmar POST-CARGA: CSEP 990, OD 281, SISUD 534, enriquecida 1271; AUD = STG.
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
