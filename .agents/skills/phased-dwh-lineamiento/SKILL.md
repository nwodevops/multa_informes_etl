---
name: phased-dwh-lineamiento
description: >-
  Implementa ETLs de consultoría por fases secuenciales (perfilamiento →
  dimensional → indicadores) según documento lineamiento. Módulos en logica/dwh/,
  pipeline.py, DDL en docs/lineamientos/ddl/, una rama git por fase de servicio.
  Usar al abrir una fase nueva, cablear Fase 2–7, o clonar el patrón en proyectos
  OEFA/similares con PROPUESTA_ADAPTADA_ETL.
---

# ETL por fases (lineamiento)

Patrón validado: documento `PROPUESTA_ADAPTADA_ETL.md` + implementación incremental en `logica/dwh/`. **No avanzar de fase sin cumplir criterio de salida.**

Detalle por fase: [phases.md](phases.md).

## Mapa de fases → código

| Fase | Entregable | Módulo |
|:---:|---|---|
| 2 | `PROF_*`, `DICCIONARIO` | `perfilamiento.py`, `diccionario.py` |
| 3 | Intermedios F1/F2/F5 + `DF_ETAPAS` (sin merge) | `homologacion.py`, `integracion.py` |
| 4 | `FG_CONFORME`, `DW_M_DQ_HALLAZGO`, `DW_M_QA_AMARRE`(+`_DETALLE`) | `calidad.py` |
| 5 | `DW_M_DIM_*`, `DW_M_FACT_MC_CSEP`/`_OD`/`_SISUD`, `DET_*` | `dimensional.py` |
| 6 | Carga Oracle (enriquecida ya en pandas) | `python/io/cargar_dw.py` |
| 7 | `DW_M_INDICADOR_RESULTADO` K1–K5 | `indicadores.py` |

Orquestación: `logica/dwh/pipeline.py` → `logica/ejecutar.py` → `python/main.py`.

## Estructura de paquete `logica/dwh/`

```
logica/dwh/
  constantes.py      # ID_CARGA, FUENTE_REGISTRO (mapa staging → CODIGO)
  catalogos.py       # semillas DIM_*
  homologacion.py    # vacio(), CUM/CAM, SI/NO, estados
  integracion.py     # intermedios por fuente F1/F2/F5 (sin merge a un fact)
  calidad.py         # R01–R05 (sin GAPPS), DW_M_QA_AMARRE* (RES_MONTO), no elimina filas
  dimensional.py     # dims + 3 facts evidencia, miembro -1, ID_FUENTE / ID_TIEMPO_FIRMA
  indicadores.py     # K1–K5 sobre hechos en memoria
  pipeline.py        # ejecutar() devuelve dict[str, DataFrame]
```

**Regla:** en `logica/` cero conexiones. I/O solo en `python/io/`.

## Cablear una fase nueva

1. Implementar módulo en `logica/dwh/`.
2. Llamar desde `pipeline.py`; exportar en `ejecutar.py`.
3. Si persiste en Oracle: DDL en `docs/lineamientos/ddl/NN_*.sql` + extender `cargar_dw.py` (`DROP_ORDEN`, `INSERT_ORDEN`, `REQUIRED_CORE`); enrich Sheet←SISUD vive en `07_enrich_sheets_sisud.sql`.
4. Prefijo en `python/main.py` → `_es_salida` y `tablas_dw`.
5. Documentar en `docs/lineamientos/implementacion-fase-N.md` y `python/CONTRATO.md`.
6. Smoke: `.venv/bin/python python/main.py` → conteos `N filas -> N en BD (OK)`.

## Git: una rama por fase de servicio

- `fase-1` (actividades a–c), `fase-2` (d–f) sale de `fase-1`, `fase-3` (g–h) sale de `fase-2`.
- **No** carpetas `fase-N/` en el código; la fase vive en la rama.
- Lineamiento interno (Fases 2–7) puede ir en la misma rama hasta el hito acordado con CSEP.

## Modelo dimensional (Fase 5–6)

- H2 = solo staging; modelo final **solo** en Oracle (o memoria previa a carga).
- Evidencia: `DW_M_FACT_MC_CSEP` / `_OD` / `_SISUD`; negocio: `DW_M_FACT_MULTA_COERCITIVA` vía SQL 07.
- Claves surrogate en Python (`ID_* = -1` para ND).
- Amarres opcionales → `NULL` + métrica en K5 (`DW_M_QA_AMARRE`), no bloqueante.

## Indicadores (Fase 7)

- Una tabla `DW_M_INDICADOR_RESULTADO` (filas largas: `COD_INDICADOR`, `METRICA`, `NUMERADOR`, `DENOMINADOR`, `VALOR`).
- Calcular **en memoria** tras construir hechos; no re-leer Oracle.
- Grano común K1–K4: `(ANIO, ID_ORGANO)` + fila `SUBGRANO=TOTAL`.
- Reproducibilidad: misma corrida H2 → mismos valores (criterio de aceptación).

## Gotchas pandas aprendidos

- No usar `or` / `if val` con `pandas.NA` → helper `vacio()` de `homologacion.py`.
- Flags `== "S"`: usar helper que no evalúe NA como bool.
- Homologar `REQUIERE_VERIF_*` con `homologar_si_no` (CHAR(1) en Oracle).

## Skills relacionadas

- Infra Hop/H2: [`../hop-python-etl/SKILL.md`](../hop-python-etl/SKILL.md)
- Calidad: [`../auditable-soft-quarantine/SKILL.md`](../auditable-soft-quarantine/SKILL.md)
- Oracle: [`../oracle-cargar-dw/SKILL.md`](../oracle-cargar-dw/SKILL.md)
