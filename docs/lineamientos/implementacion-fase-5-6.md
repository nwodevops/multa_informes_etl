# Implementación lineamientos — Fases 5 y 6

Referencia: [`PROPUESTA_ADAPTADA_ETL.md`](PROPUESTA_ADAPTADA_ETL.md) secciones 3 y 6.  
Mapa mental: [`../modelo-kimball.md`](../modelo-kimball.md).  
Cómo se arma el enriquecido: [`extra/manual-como-se-arma-el-fact.md`](extra/manual-como-se-arma-el-fact.md).

## Código

| Módulo | Fase | Entregable |
|---|---|---|
| `logica/dwh/dimensional.py` | 5 | `MI_DIM_*`, `MI_FACT_MC_CSEP` / `_OD` / `_SISUD`, `MI_DET_ETAPA_MC` |
| `python/io/cargar_dw.py` | 6 | wipe + DDL 01–06 + INSERT + enrich 07 |
| `docs/lineamientos/ddl/07_enrich_sheets_sisud.sql` | 6 | `MI_FACT_MULTA_COERCITIVA` = (CSEP∪OD) LEFT JOIN SISUD |
| `logica/dwh/pipeline.py` | 2–7 | Orquestación |

## Fase 5 — modelo en memoria (evidencia)

- 8 dims (incluye `MI_DIM_OD`, `MI_DIM_FUENTE_REGISTRO`).
- **Tres facts de evidencia** (sin merge): `MI_FACT_MC_CSEP`, `MI_FACT_MC_OD`, `MI_FACT_MC_SISUD`.
- Attrs operativos en hechos: `JEFE`, `UF`, `N_PROY_MC`, `ETA_REG_PROY_MC`, `ETA_REG_MC`, `RESULT_PROY_MC`, `ESTADO_MC_TXT`, `ESTADO_PAGO_TXT`.
- `ID_FUENTE` y `ID_TIEMPO_FIRMA` (role-playing); **sin** VARCHAR `FUENTE_REGISTRO`.
- `MI_DIM_ORGANO_UNIDAD`: solo 10 CSEP + ND (catálogo `f2_csep_sheets.json`).
- Ningún hecho sin dimensión resuelta (fallback `ID_* = -1`).
- `MI_DET_ETAPA_MC.ID_MC` por `COD_PROY_MC` cuando existe hecho padre CSEP.

## Fase 6 — carga Oracle + enrich

- DDL `01`–`04` (+ comentarios `05`, vistas `06`) vía `cargar_dw.py`.
- Carga: dims → 3 facts evidencia → etapas → `MI_DQ_HALLAZGO` → `MI_QA_AMARRE*` → indicadores.
- Tras INSERT: ejecutar `07_enrich_sheets_sisud.sql` → `MI_FACT_MULTA_COERCITIVA`.
- Vistas: `VW_MC_CSEP`, `VW_MC_OD`, `VW_MC_SISUD`, `VW_MC_ENRIQUECIDA` (drop legacy `VW_FCT_*`).
- `COUNT(*)` Oracle = filas del DataFrame por tabla de evidencia (salvo DQ: `>=`).

## Volúmenes de referencia (local)

CSEP~990 · OD~281 · SISUD~534 · enriquecido~1271 · órgano 11 · OD 33 · fuentes activas: CAGR / OD_SHEETS / SISUD_VW (`GAPPS` solo semilla).

## Verificación

```bash
./init.sh   # HARNESS OK
```
