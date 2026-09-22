# impl `f4-mysql-aud-fact`

Rama: `linux_v2`.

## Qué cambió

F4 (query [`input_legacy/input_mysql/vw_multas_app.sql`](../input_legacy/input_mysql/vw_multas_app.sql)) vuelve a ingestión:

- Hop `pl_stage_mysql.hpl` → `STG_MYSQL_MULTAS`
- Foto cruda `DW_M_AUD_F4_GAPPS` (1:1 STG)
- Fact de negocio = F1∪F2 (+ lookup SISUD) **∪ GAPPS** (`ID_FUENTE=3`)
- Sin lookup SISUD sobre filas GAPPS
- Grano GAPPS: `NU_IDMC` (queda en AUD; el fact usa el molde `COLS_MULTAS`)

Contrato de conteo: `enriquecida = AUD_F2 + AUD_F1 + AUD_F4`.

## Archivos

- `inputs.yaml`, `python/introspect/mysql.py`, `python/create_stg.py`, `metadata/rdbms/mysql.json`
- `pipelines/pl_stage_mysql.hpl`, `workflows/wf_main.hwf`, `wf_main_win.hwf`, `init.sh`, `init.bat`
- `python/io/leer_h2.py`, `logica/dwh/{constantes,integracion,pipeline,dimensional,enrich}.py`, `logica/ejecutar.py`
- `python/audit/cargar_aud.py`, `python/verify_dw.py`, `python/main.py`
- Docs: `python/CONTRATO.md`, `docs/inputs/README.md`, `docs/lineamientos/ddl/audit/README.md`

## Verificación

Smoke: aliases del SQL → columnas STG; `_integrar_mysql` + `enriquecer_sheets_sisud` concatena GAPPS sin tocar CUM/CAM de planilla.

`./init.sh` HARNESS OK pendiente de Hop + MySQL vivo (`DB_MYSQL_*`).
