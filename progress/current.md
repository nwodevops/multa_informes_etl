# Sesión activa — rama `windows` (exclusiva Win)

## Feature activa

| Campo | Valor |
|---|---|
| ID | `fase-remote-deploy` |
| Status | `in_progress` |
| Criterio | `wf_main_win` / `init.bat` → Success + POST-CARGA ≈ 990/281/534/1271 + `MI_AUD_*` = STG + `MI_DQ_HALLAZGO`; sin VW/QA/K en Oracle |

## Hecho reciente

- `dw-wipe-canonico-aud` = **done**: wipe `MI_*`/`VW_*`, DDL `01`+`02`+`MI_DQ_HALLAZGO`(+`05`), enrich `07`, audit `MI_AUD_*`.
- `MI_DQ_HALLAZGO` restaurado en Oracle (R01–R05). QA/K siguen solo en memoria.

## Homologación

- Código canónico en `linux` y `windows` (merge + push).
- Trabajo de lógica/DW preferir rama `linux`; `windows` para corrida remota.

## Plan

1. En PC Win: `git pull` → `.\switch-env.ps1 remote` → `wf_main_win` / `init.bat` (`client_secret.json`).
2. Confirmar POST-CARGA: CSEP/OD/SISUD/enriquecida + AUD + `MI_DQ_HALLAZGO`.
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
