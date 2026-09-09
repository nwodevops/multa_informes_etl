# Sesión activa — rama `windows` (exclusiva Win)

## Feature activa

| Campo | Valor |
|---|---|
| ID | `fase-remote-deploy` |
| Status | `in_progress` |
| Criterio | `init.bat` o `wf_main_win.hwf` → Success + DW POST-CARGA 990/281/534/1271 + K1–K5 |

> Merge `linux` → `windows` (`a960432`): facts evidencia + enrich 07 + carga canónica wipe `MI_*`/`VW_*`. Validado en linux. Attrs operativos Sheet (JEFE/UF/…) incluidos.

## Plan

1. En PC Win: `git pull` → `.\switch-env.ps1 remote` → `wf_main_win` / `init.bat` (requiere `client_secret.json` para Sheets).
2. Confirmar POST-CARGA: CSEP 990, OD 281, SISUD 534, enriquecida 1271.
3. Si OK → `fase-remote-deploy` = done; `fact-attrs-operativos-sheet` = done.

## Comandos Win

```powershell
cd D:\Eder\workspace_etl_oefa\multa_informes_etl
git checkout windows
git pull
.\switch-env.ps1 remote
init.bat
# o Hop: wf_main_win.hwf
```
