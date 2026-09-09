# impl_fact-attrs-operativos-sheet

## Qué

Atributos operativos del Sheet F2 en el DW para trabajar sin abrir Sheets:

`JEFE`, `UF`, `N_PROY_MC`, `ETA_REG_PROY_MC`, `ETA_REG_MC`, `RESULT_PROY_MC`, `ESTADO_MC_TXT`, `ESTADO_PAGO_TXT`.

## Archivos

- `docs/lineamientos/ddl/02_hechos.sql`, `05_comentarios.sql`, `07_enrich_sheets_sisud.sql`
- `logica/dwh/integracion.py`, `dimensional.py`
- `python/io/cargar_dw.py` (`_ensure_fact_attrs_operativos`)
- `feature_list.json`, `progress/current.md`

## Criterio

- Caso `0153` enriquecida → `JEFE = MEJIA, HOMERO` (UF `FLORENCIA - TUCARI`, etapa cobranza)
- Enrich Maggi intacto (1271 = 990+281; CUM/CAM OK)
- `python/main.py` recarga DW OK (2026-09-08)
- `./init.sh` HARNESS: opcional si Hop no re-corre staging

