# CONTRATO — dos capas Python (no mezclar)

Ver [`LEEME.md`](LEEME.md) y [`../docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md`](../docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md).

```
CAPA STG / DDL
  python/create_stg.py      inputs.yaml → introspect/ → CREATE TABLE STG_*
  python/introspect/        schema vivo. No extrae filas.

CAPA POST-STAGING (lineamientos Fases 2–7)
  python/main.py            orquesta: io/leer_h2 → logica/ejecutar.py → io/cargar_dw.py
  python/io/leer_h2.py      ENTRADA: H2 STG_* → DataFrames
  logica/ejecutar.py        delega a logica/dwh/
  logica/dwh/               perfilamiento, diccionario, homologación, integración, calidad, dimensional, indicadores
  python/io/cargar_dw.py    SALIDA: TRUNCATE+INSERT MI_DIM_*/FACT_*/DET_*/DQ_*/QA_*/INDICADOR + vistas VW_MC_*
```

## Entrada (`python/io/leer_h2.py`)

| Nombre | STG H2 | Fuente lineamiento |
|---|---|---|
| `GS1` | `STG_GS1_CSEP_MULTAS` | F2 CSEP Google Sheets multas (`COD_UNIDAD`) |
| `GS2` | `STG_GS2_OD_MULTAS` | F1 31 ODs Google Sheets (`COD_OD` por fila) |
| `ETAPAS` | `STG_GS1_ETAPAS` | F2-ET (Sheets CSEP) |
| `ORA` | `STG_ORA_VW_MULTA_COERCITIVA` | F5 |
| `MYSQL` | `STG_MYSQL_T_MVC_MULTACOERCITIVA` | F4 |
| `DIC_TABLAS` | `STG_GS1_DIC_TABLAS` | F2 diccionario |
| `DIC_VARIABLES` | `STG_GS1_DIC_VARIABLES` | F2 diccionario |

## Salida (lineamientos Fases 2–7)

| Nombre | Fase | Qué es |
|---|---|---|
| `PROF_RESUMEN` / `PROF_HALLAZGO` | 2 | Perfilamiento |
| `DICCIONARIO` | 2 | Campos documentados |
| `DF_MULTAS` / `DF_ETAPAS` | 3–4 | Integración + `FG_CONFORME` |
| `MI_DQ_HALLAZGO` / `MI_QA_AMARRE` / `MI_QA_AMARRE_DETALLE` | 4 | Calidad + amarre H9 (resumen y claves sin match) |
| `MI_DIM_*` / `MI_FACT_*` / `MI_DET_ETAPA_MC` | 5 | Dimensiones (órgano CSEP limpia, OD, fuente, …), hecho con `ID_FUENTE` + `ID_TIEMPO_FIRMA` |
| `MI_INDICADOR_RESULTADO` | 7 | KPIs K1–K5 |
| `RESULTADO` | 2–7 | Resumen de corrida |

Carga Oracle: `python/io/cargar_dw.py` aplica DDL formal (01–04) si falta, elimina vistas `VW_FCT_*` legacy, recrea `VW_MC_*`, y hace TRUNCATE+INSERT (incluye `MI_QA_*`).

## Reglas

- En `logica/` no hay conexiones ni drivers.
- Hop resetea H2 y carga `STG_*`; Python no filtra el landing.
