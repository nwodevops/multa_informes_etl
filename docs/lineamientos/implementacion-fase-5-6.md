# Implementación lineamientos — Fases 5 y 6

Referencia: [`PROPUESTA_ADAPTADA_ETL.md`](PROPUESTA_ADAPTADA_ETL.md) secciones 3 y 6.  
Mapa mental: [`../adjuntos/guia-leer-modelo-dimensional.md`](../adjuntos/guia-leer-modelo-dimensional.md).

## Código

| Módulo | Fase | Entregable |
|---|---|---|
| `logica/dwh/dimensional.py` | 5 | `MI_DIM_*`, `MI_FACT_MULTA_COERCITIVA`, `MI_DET_ETAPA_MC` |
| `python/io/cargar_dw.py` | 6 | TRUNCATE+INSERT + ensure DDL/vistas |
| `logica/dwh/pipeline.py` | 2–7 | Orquestación |

## Fase 5 — modelo en memoria

- 8 dims (incluye `MI_DIM_OD`, `MI_DIM_FUENTE_REGISTRO`).
- Hecho con `ID_FUENTE` y `ID_TIEMPO_FIRMA` (role-playing); **sin** VARCHAR `FUENTE_REGISTRO`.
- `MI_DIM_ORGANO_UNIDAD`: solo 10 CSEP + ND (catálogo `f2_csep_sheets.json`).
- Ningún hecho sin dimensión resuelta (fallback `ID_* = -1`).
- `MI_DET_ETAPA_MC.ID_MC` por `COD_PROY_MC` cuando existe hecho padre.

## Fase 6 — carga Oracle

- DDL `01`–`04` (+ comentarios `05`, vistas `06`) vía `cargar_dw.py`.
- Carga: dims → hecho → etapas → `MI_DQ_HALLAZGO` → `MI_QA_AMARRE*` → indicadores.
- Vistas legacy `VW_FCT_*` drop; vistas de reporte `VW_MC_*` recreate.
- `COUNT(*)` Oracle = filas del DataFrame por tabla (salvo DQ: `>=`).

## Volúmenes de referencia (local)

~1801 multas · ~2070 etapas · órgano 11 · OD 33 · fuentes: CAGR~986, SISUD~530, OD_SHEETS~281, GAPPS~4.

## Verificación

```bash
./init.sh   # HARNESS OK
```
