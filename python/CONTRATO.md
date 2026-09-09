# CONTRATO — dos capas Python (no mezclar)

Ver [`LEEME.md`](LEEME.md) y [`../docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md`](../docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md).  
Manual enrich: [`../docs/lineamientos/extra/manual-como-se-arma-el-fact.md`](../docs/lineamientos/extra/manual-como-se-arma-el-fact.md).

```
CAPA STG / DDL
  python/create_stg.py      inputs.yaml → introspect/ → CREATE TABLE STG_*
  python/introspect/        schema vivo. No extrae filas.

CAPA POST-STAGING (lineamientos Fases 2–7)
  python/main.py            orquesta: leer_h2 → logica/ → cargar_dw → audit/cargar_aud
  python/io/leer_h2.py      ENTRADA: H2 STG_* → DataFrames
  logica/ejecutar.py        delega a logica/dwh/
  logica/dwh/               perfil … dimensional (3 facts) … calidad/indicadores (memoria)
  python/io/cargar_dw.py    SALIDA estrella: wipe canónico MI_*/VW_* + DDL 01+02(+05)
                            + INSERT dims/facts/DET + SQL 07 enrich
  python/audit/cargar_aud.py  MI_AUD_* 1:1 desde STG (fuera de estrella)
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

## Salida

### Publicada en Oracle (canónico flaco)

| Nombre | Qué es |
|---|---|
| `MI_DIM_*` / `MI_FACT_MC_CSEP` / `_OD` / `_SISUD` / `MI_DET_ETAPA_MC` | Estrella evidencia |
| `MI_FACT_MULTA_COERCITIVA` | Negocio enrich SQL 07 (solo Oracle) |
| `MI_AUD_F1_OD_MULTAS` / `MI_AUD_F2_CSEP_MULTAS` / `MI_AUD_F2_CSEP_ETAPAS` / `MI_AUD_F5_SISUD_VW` | Foto cruda STG 1:1 |

### Solo memoria de corrida (no Oracle)

| Nombre | Fase | Qué es |
|---|---|---|
| `PROF_*` / `DICCIONARIO` / `DF_*` | 2–4 | Intermedios |
| `MI_DQ_HALLAZGO` / `MI_QA_AMARRE*` | 4 | Calidad + amarre H9 |
| `MI_INDICADOR_RESULTADO` | 7 | KPIs K1–K5 |
| `RESULTADO` | 2–7 | Resumen de corrida |

Carga Oracle: wipe **todas** `MI_*` y `VW_MC_*`/`VW_FCT_*` → DDL **solo** `01`+`02` (+ comentarios `05`) → INSERT estrella → enrich `07` → `python/audit` recrea `MI_AUD_*`.  
**No** se aplican `03`/`04`/`06` en runtime (históricos TDR en `docs/lineamientos/ddl/`).

Windows/REPOCSEP: cleanup manual de vistas/`MI_*` viejos una vez; luego el wipe canónico mantiene el esquema flaco. Linux/Docker: wipe total cada corrida.

## Reglas

- En `logica/` no hay conexiones ni drivers.
- Hop resetea H2 y carga `STG_*`; Python no filtra el landing.
- Consultar hechos en `MI_FACT_*` (no hay vistas `VW_MC_*` en destino).
