# impl `canonico-flaco-enrich-py`

Rama: `linux_v2`.

## Qué cambió

- `logica/dwh/enrich.py`: vertical F1∪F2, horizontal lookup SISUD (`clave_join_res_monto`).
- Oracle ya no crea/inserta `DW_M_FACT_MC_CSEP|_OD|_SISUD`.
- `DW_M_DET_ETAPA_MC.ID_MC` FK a `DW_M_FACT_MULTA_COERCITIVA`.
- SQL `07` deprecado (no runtime).

## Smoke `./init.sh` (linux_v2)

**HARNESS OK.** APP@localhost:1524.

- Enriquecida 1271 = AUD_F2 990 + AUD_F1 281. SISUD AUD 534 (no suma filas).
- Sin `DW_M_FACT_MC_*` en Oracle. DET 2080. Caso 0153/64: 2 filas, 2 con CUM+CAM.

## Archivos

- `logica/dwh/enrich.py` (nuevo), `pipeline.py`, `ejecutar.py`
- `python/main.py`, `python/io/cargar_dw.py`, `python/verify_dw.py`
- `docs/lineamientos/ddl/02_hechos.sql`, `07_enrich_sheets_sisud.sql`
- `init.sh`, `init.bat`, `CHECKPOINTS.md`, `python/CONTRATO.md`, `feature_list.json`
