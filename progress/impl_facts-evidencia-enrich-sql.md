# impl_facts-evidencia-enrich-sql

## Qué

- 3 facts evidencia en Oracle + enrich post-SQL (`07_enrich_sheets_sisud.sql`).
- Clave enrich: `norm(N_RES_MC) + MONTO_UIT` → CUM/CAM.
- Puente H9: `RES_MONTO_Sheets_vs_SISUD`.
- Sin MySQL.

## Archivos

- `logica/dwh/integracion.py`, `dimensional.py`, `pipeline.py`, `calidad.py`, `homologacion.py`
- `logica/ejecutar.py`
- `python/io/cargar_dw.py`
- `docs/lineamientos/ddl/02_hechos.sql`, `06_vistas.sql`, `07_enrich_sheets_sisud.sql`
- `init.sh`, docs manual/correo/guía, `feature_list.json`

## Criterio / evidencia

- Corrida Hop `wf_main` 2026-09-08 19:02: CSEP 990, OD 281, SISUD 534, enriquecida 1271.
- Caso Maggi `0153-2026-OEFA/DSEM` + 64 UIT: 2 filas Sheet con CUM `00046882612` / CAM `20260800087`.
- Backup SISUD local `VW_MULTA_COERCITIVA_202609081830.sql` (534 filas) cargado en `localhost:1525`.

## Status

`done` (2026-09-08).
