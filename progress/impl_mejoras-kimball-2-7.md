# Evidencia — mejoras Kimball puntos 2–7

**Fecha:** 2026-09-06  
**Verificación:** `./init.sh` → **HARNESS OK**

## Resumen

| Punto | Estado | Evidencia Oracle / repo |
|---|---|---|
| 1 Órgano CSEP limpia | ya done | `MI_DIM_ORGANO_UNIDAD` = 11 |
| 2 Vistas por fuente | done | `VW_MC_CSEP/OD/SISUD/GAPPS` presentes |
| 3 Amarre H9 detalle | done | `MI_QA_AMARRE`=3, `MI_QA_AMARRE_DETALLE`=3078 |
| 4 Sin VARCHAR `FUENTE_REGISTRO` | done | columna inexistente en hecho |
| 5 `ID_TIEMPO_FIRMA` | done | columna + FK presentes |
| 6 Ops / contrato | done | mínimos CAGR≥200, OD≥50, SISUD≥50; `docs/inputs/README.md` |
| 7 Anti-patrones | done | guía §9 (no F3, no fusionar OD/órgano, no INNER JOIN forzado) |

## Conteos por fuente (corrida)

`OD_SHEETS` 281 · `CAGR` 986 · `GAPPS` 4 · `SISUD_VW` 530 · hecho 1801

## Fix de cableado

`python/main.py` `_es_salida` ahora incluye prefijo `MI_QA_` (sin eso se truncaban las tablas QA pero no se insertaban).

## Archivos clave

- `docs/lineamientos/ddl/06_vistas.sql`, `03_bitacora.sql`, `02_hechos.sql`
- `logica/dwh/calidad.py`, `dimensional.py`, `pipeline.py`
- `python/io/cargar_dw.py`, `python/main.py`
- `init.sh`, guías Kimball / anexo / inputs README
