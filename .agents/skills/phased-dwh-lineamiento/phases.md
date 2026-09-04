# Fases 2–7 — criterios de avance

Referencia canónica: `docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md`.

## Fase 2 — Perfilamiento y diccionario

**Salida:** `PROF_RESUMEN`, `PROF_HALLAZGO`, `DICCIONARIO`.

**Avance:** todo campo de las fuentes documentado; hallazgos H1–H9 con evidencia.

## Fase 3 — Homologación e integración

**Salida:** `DF_MULTAS` (F1+F2+F4+F5 + `FUENTE_ORIGEN`), `DF_ETAPAS`.

**Avance:** cero errores de tipo; catálogo de estados acordado.

## Fase 4 — Calidad

**Salida:** `FG_CONFORME` en dataframes; `MI_DQ_HALLAZGO`; `QA_AMARRE` (% puente H9).

**Reglas:** R01 completitud, R02 CUM/CAM, R03 temporal, R04 UIT≥0, R05 UIT↔soles.

**Principio:** no eliminar filas; marcar y registrar en `MI_DQ_HALLAZGO`.

## Fase 5 — Modelo dimensional

**Salida:** `DIM_*` (6), `MI_FACT_MULTA_COERCITIVA`, `MI_DET_ETAPA_MC`.

**Avance:** ningún hecho sin dimensión (`ID_* = -1` si falta lookup).

## Fase 6 — Carga Oracle

**Salida:** tablas en BD_CURSOR vía `TRUNCATE + INSERT` tipado.

**Avance:** `COUNT(*)` Oracle = filas DataFrame por tabla; DDL formal (`01`–`03`); DROP vistas legacy.

## Fase 7 — Indicadores

**Salida:** `MI_INDICADOR_RESULTADO` con K1–K5.

| Código | Métrica |
|---|---|
| K1 | `N_MULTAS` por año×órgano |
| K2 | `PROM_DIAS_NOTIF_FIRMA` |
| K3 | `RATIO_COBRANZA_SOLES`, `RATIO_COBRANZA_UIT` |
| K4 | `TASA_VERIF_POST_MC` |
| K5 | `PCT_CONFORME` (por regla), `PCT_AMARRE` (puentes) |

**Avance:** reproducible; presencia de K1–K5; DDL `04_indicadores.sql`.

## Fase 8 (fuera de alcance)

Power BI contra tablas actualizadas — **no se realizará** en esta implementación.
