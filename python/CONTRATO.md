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
  python/io/cargar_dw.py    SALIDA: TRUNCATE+INSERT MI_DIM_*/MI_FACT_*/MI_DET_*/MI_DQ_*/MI_INDICADOR_RESULTADO → Oracle DW
```

## Entrada (`python/io/leer_h2.py`)

| Nombre | STG H2 | Fuente lineamiento |
|---|---|---|
| `GS1` | `STG_GS1_MULTAS_COERCITIVAS` | F2 CAGR multas |
| `GS2` | `STG_GS2_MULTAS_COERCITIVAS` | F1 Lambayeque |
| `ETAPAS` | `STG_GS1_ETAPAS` | F2-ET |
| `ORA` | `STG_ORA_VW_MULTA_COERCITIVA` | F5 |
| `MYSQL` | `STG_MYSQL_T_MVC_MULTACOERCITIVA` | F4 |
| `INFORMES` | `STG_ORA_CSEP_INFORMES` | F3 |
| `DIC_TABLAS` | `STG_GS1_DIC_TABLAS` | F2 diccionario |
| `DIC_VARIABLES` | `STG_GS1_DIC_VARIABLES` | F2 diccionario |

## Salida (lineamientos Fases 2–7)

| Nombre | Fase | Qué es |
|---|---|---|
| `PROF_RESUMEN` / `PROF_HALLAZGO` | 2 | Perfilamiento |
| `DICCIONARIO` | 2 | Campos documentados |
| `DF_MULTAS` / `DF_INFORMES` / `DF_ETAPAS` | 3–4 | Integración + `FG_CONFORME` |
| `MI_DQ_HALLAZGO` / `QA_AMARRE` | 4 | Calidad + amarre H9 |
| `DIM_*` / `MI_DIM_*` | 5 | Dimensiones con miembro `-1` |
| `FACT_*` / `MI_FACT_*` / `MI_DET_ETAPA_MC` | 5 | Hechos y detalle |
| `MI_INDICADOR_RESULTADO` | 7 | KPIs K1–K5 |
| `RESULTADO` | 2–7 | Resumen de corrida |

Carga Oracle: `python/io/cargar_dw.py` aplica DDL formal (01–04) si falta, elimina vistas `VW_FCT_*` legacy, y hace TRUNCATE+INSERT. Esquema = USER de la sesión Oracle.

## Reglas

- En `logica/` no hay conexiones ni drivers.
- Hop resetea H2 y carga `STG_*`; Python no filtra el landing.
