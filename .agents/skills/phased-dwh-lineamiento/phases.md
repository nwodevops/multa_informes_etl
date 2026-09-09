# Fases 2–7 — criterios de avance

Referencia canónica: `docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md`.  
Estado del modelo: `docs/modelo-kimball.md`.  
Manual enrich: `docs/lineamientos/extra/manual-como-se-arma-el-fact.md`.

Fuentes activas: **F1 + F2 (+etapas) + F5**. F3 OUT. F4 fuera de ingestión (semilla `GAPPS`).

## Fase 2 — Perfilamiento y diccionario

**Salida:** `PROF_RESUMEN`, `PROF_HALLAZGO`, `DICCIONARIO`.

**Avance:** campos de F1/F2/F5 documentados; hallazgos H1–H9 con evidencia.

## Fase 3 — Homologación e integración

**Salida:** intermedios tipificados `df_csep` / `df_od` / `df_sisud` + `DF_ETAPAS` (**sin** merge a un solo fact; F4 no entra).

**Avance:** cero errores de tipo; catálogo de estados acordado.

## Fase 4 — Calidad

**Salida:** `FG_CONFORME`; `MI_DQ_HALLAZGO`; `MI_QA_AMARRE` + `MI_QA_AMARRE_DETALLE` (H9).

**Reglas:** R01 completitud (Sheets `COD_MA`, SISUD `CUM`/`CAM` — sin GAPPS), R02 CUM/CAM, R03 temporal, R04 UIT≥0, R05 UIT↔soles.

**Puente H9:** `RES_MONTO_Sheets_vs_SISUD`.

**Principio:** no eliminar filas; marcar y registrar en `MI_DQ_HALLAZGO`.

## Fase 5 — Modelo dimensional (evidencia)

**Salida:** 8× `MI_DIM_*`, tres facts `MI_FACT_MC_CSEP` / `_OD` / `_SISUD`, `MI_DET_ETAPA_MC`.

**Avance:** ningún hecho sin dimensión (`ID_* = -1` si falta lookup); órgano solo CSEP+ND.

## Fase 6 — Carga Oracle + enrich

**Salida:** TRUNCATE+INSERT de evidencia/dims/QA/KPIs; SQL `07_enrich_sheets_sisud.sql` → `MI_FACT_MULTA_COERCITIVA`; vistas `VW_MC_CSEP` / `_OD` / `_SISUD` / `VW_MC_ENRIQUECIDA`.

**Avance:** `COUNT(*)` Oracle = filas DataFrame (evidencia); enriquecido ≈ CSEP+OD (~1271 ref.).

## Fase 7 — Indicadores

**Salida:** `MI_INDICADOR_RESULTADO` con K1–K5.

| Código | Métrica |
|---|---|
| K1 | `N_MULTAS` por año×órgano |
| K2 | `PROM_DIAS_NOTIF_FIRMA` |
| K3 | `RATIO_COBRANZA_SOLES`, `RATIO_COBRANZA_UIT` |
| K4 | `TASA_VERIF_POST_MC` |
| K5 | `PCT_CONFORME` (por regla), `PCT_AMARRE` (puentes; detalle en `MI_QA_AMARRE_DETALLE`) |

**Avance:** reproducible; presencia de K1–K5; DDL `04_indicadores.sql`.

## Fase 8 (fuera de alcance)

Power BI contra tablas actualizadas — **no se realizará** en esta implementación.
