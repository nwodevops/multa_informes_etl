# Sesión activa — rama `linux` (harness / desarrollo local)

## Feature activa

| Campo | Valor |
|---|---|
| ID | `fase-remote-deploy` |
| Status | `in_progress` |
| Criterio Win | `wf_main_win` / `init.bat` → Success + POST-CARGA + `DW_M_AUD_*` + `DW_M_DQ_HALLAZGO`; sin VW/QA/K |

## Hecho reciente

- Harness alineado al DW canónico: `init.sh` / `init.bat` / `CHECKPOINTS.md` / `docs/verification.md`.
- Oracle: estrella + `DW_M_DQ_HALLAZGO` + `DW_M_AUD_*`. QA/K solo memoria.

## Plan

1. Local (`linux`): `./switch-env.sh local` → `./init.sh` o Hop `wf_main.hwf` → `HARNESS OK`.
2. Remoto Win: `git pull` en `windows` → `.\switch-env.ps1 remote` → `init.bat` / `wf_main_win`.
3. Si Win OK → `fase-remote-deploy` = done; merge/homologar ramas.

## Comandos Linux

```bash
git checkout linux
./switch-env.sh local
./init.sh
# o Hop: wf_main.hwf
.venv/bin/python python/verify_dw.py
```
