# impl — fix-montos-f1-f2 + quitar-f4-gapps

## fix-montos-f1-f2

- `logica/dwh/integracion.py`: rename `MULTA_UIT`→`MONTO_UIT`, `MULTA_S`→`MONTO_S` en GS1/GS2.
- `logica/dwh/catalogos.py` + DDL: UIT 2026 = 5500.
- Smoke: ACTA CMIN → FACT `MONTO_UIT=64`, `MONTO_S=352000`, `MONTO_S_CALC=352000`, `ID_UIT≠-1`.

## quitar-f4-gapps

- Quitado staging MySQL: `inputs.yaml`, `pl_stage_mysql.hpl`, hops en `wf_main`/`wf_main_win`, `init.sh`/`init.bat`, `metadata/rdbms/mysql.json`, `DB_MYSQL_*` en environments.
- Python: sin lectura/integración MYSQL; puente `CUM_SISUD_vs_GAPP` eliminado; `VW_MC_GAPPS` no se recrea (sí se dropea si existía).
- Semilla `ID_FUENTE=3 GAPPS` conservada como histórico.
- Docs canónicos alineados a F1+F2+F5.

## Limpieza total MySQL (no vuelve)

- Eliminados `python/io/escribir_mysql.py`, `python/introspect/mysql.py`.
- `create_stg.py` / `requirements.txt` sin mysql-connector.
- Docs/skills/ESTRUCTURA/platform sin conexión MySQL operativa.
- Semilla `ID_FUENTE=3 GAPPS` solo como histórico en dim (sin ingestión).
