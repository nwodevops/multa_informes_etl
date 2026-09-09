# CONTRATO — dos capas Python (no mezclar)

Ver [`LEEME.md`](LEEME.md) y [`../docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md`](../docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md).  
Manual enrich: [`../docs/lineamientos/extra/manual-como-se-arma-el-fact.md`](../docs/lineamientos/extra/manual-como-se-arma-el-fact.md).

```
CAPA STG / DDL
  python/create_stg.py      inputs.yaml → introspect/ → CREATE TABLE STG_*
  python/introspect/        schema vivo. No extrae filas.

CAPA POST-STAGING (lineamientos Fases 2–7)
  python/main.py            orquesta: io/leer_h2 → logica/ejecutar.py → io/cargar_dw.py
  python/io/leer_h2.py      ENTRADA: H2 STG_* → DataFrames
  logica/ejecutar.py        delega a logica/dwh/
  logica/dwh/               perfilamiento … dimensional (3 facts evidencia) … indicadores
  python/io/cargar_dw.py    SALIDA: wipe MI_*/VW_* + DDL 01–06 + INSERT + SQL 07 enrich
```

Fuentes activas: F1 Sheets OD, F2 Sheets CSEP (+etapas), F5 SISUD. **Sin MySQL.**

## Entrada (`python/io/leer_h2.py`)

| Nombre | STG H2 | Fuente lineamiento |
|---|---|---|
| `GS1` | `STG_GS1_CSEP_MULTAS` | F2 CSEP Google Sheets multas (`COD_UNIDAD`) |
| `GS2` | `STG_GS2_OD_MULTAS` | F1 ODs Google Sheets (`COD_OD` por fila) |
| `ETAPAS` | `STG_GS1_ETAPAS` | F2-ET (Sheets CSEP) |
| `ORA` | `STG_ORA_VW_MULTA_COERCITIVA` | F5 |
| `DIC_TABLAS` | `STG_GS1_DIC_TABLAS` | F2 diccionario |
| `DIC_VARIABLES` | `STG_GS1_DIC_VARIABLES` | F2 diccionario |

## Salida (lineamientos Fases 2–7)

| Nombre | Fase | Qué es |
|---|---|---|
| `PROF_RESUMEN` / `PROF_HALLAZGO` | 2 | Perfilamiento |
| `DICCIONARIO` | 2 | Campos documentados |
| Intermedios F1/F2/F5 / `DF_ETAPAS` / `DF_MULTAS` | 3–4 | Tipificados; `FG_CONFORME` solo en `DF_MULTAS` (UNION auxiliar) |
| `MI_DQ_HALLAZGO` / `MI_QA_AMARRE` / `MI_QA_AMARRE_DETALLE` | 4 | Calidad + amarre H9 (`RES_MONTO_Sheets_vs_SISUD`) |
| `MI_DIM_*` / `MI_FACT_MC_CSEP` / `_OD` / `_SISUD` / `MI_DET_ETAPA_MC` | 5 | Evidencia + dims (export Python) |
| `MI_FACT_MULTA_COERCITIVA` | 6 (SQL 07) | Negocio enriquecido Sheet←SISUD (**solo Oracle**, no lo exporta `logica/`) |
| `MI_INDICADOR_RESULTADO` | 7 | KPIs K1–K5 |
| `RESULTADO` | 2–7 | Resumen de corrida |

Carga Oracle: cada corrida `cargar_dw.py` hace wipe de `MI_*` / `VW_MC_*` (y `VW_FCT_*` si quedaran), aplica DDL `01`–`04` + vistas `06`, INSERT de evidencia/dims/QA/KPIs, ejecuta `07_enrich_sheets_sisud.sql` → `MI_FACT_MULTA_COERCITIVA` + `VW_MC_*`.

## Reglas

- En `logica/` no hay conexiones ni drivers.
- Hop resetea H2 y carga `STG_*`; Python no filtra el landing.
