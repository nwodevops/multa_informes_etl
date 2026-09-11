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
  logica/dwh/               perfil … dimensional (3 facts memoria) … enrich.py … KPIs
  python/io/cargar_dw.py    SALIDA: wipe canónico DW_M_*/VW_* + DDL 01+02+DQ(+05)
                            + INSERT dims/enriquecida/DET/DW_M_DQ_HALLAZGO
  python/audit/cargar_aud.py  DW_M_AUD_* 1:1 desde STG (fuera de estrella)
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

### Publicada en Oracle (canónico)

| Nombre | Qué es |
|---|---|
| `DW_M_DIM_*` / `DW_M_DET_ETAPA_MC` | Estrella (DET FK al enriquecido) |
| `DW_M_FACT_MULTA_COERCITIVA` | Negocio: F1∪F2 + lookup SISUD (`logica/dwh/enrich.py`) |
| `DW_M_DQ_HALLAZGO` | Bitácora R01–R05 (cuarentena blanda; no elimina filas) |
| `DW_M_AUD_F1_OD_MULTAS` / `DW_M_AUD_F2_CSEP_MULTAS` / `DW_M_AUD_F2_CSEP_ETAPAS` / `DW_M_AUD_F5_SISUD_VW` | Foto cruda STG 1:1 |

### Solo memoria de corrida (no Oracle)

| Nombre | Fase | Qué es |
|---|---|---|
| `PROF_*` / `DICCIONARIO` / `DF_*` | 2–4 | Intermedios |
| `DW_M_FACT_MC_CSEP` / `_OD` / `_SISUD` | 5 | Evidencia por fuente (no se publica) |
| `DW_M_QA_AMARRE*` | 4 | Amarre H9 (resumen/detalle) |
| `DW_M_INDICADOR_RESULTADO` | 7 | KPIs K1–K5 |
| `RESULTADO` | 2–7 | Resumen de corrida |

Carga Oracle: wipe **todas** `DW_M_*` y `VW_MC_*`/`VW_FCT_*` → DDL `01`+`02` + `DW_M_DQ_HALLAZGO` (03 filtrado) (+ comentarios `05`) → INSERT dims/enriquecida/DET/DQ → `python/audit` recrea `DW_M_AUD_*`.  
**No** se aplican `04`/`06`/`07` ni tablas `DW_M_QA_*` / `DW_M_FACT_MC_*` en runtime.

Windows/REPOCSEP: cleanup manual de vistas/`DW_M_*` viejos una vez; luego el wipe canónico mantiene el esquema flaco. Linux/Docker: wipe total cada corrida.

## Reglas

- En `logica/` no hay conexiones ni drivers.
- Hop resetea H2 y carga `STG_*`; Python no filtra el landing.
- Consultar hechos en `DW_M_FACT_*` (no hay vistas `VW_MC_*` en destino).
