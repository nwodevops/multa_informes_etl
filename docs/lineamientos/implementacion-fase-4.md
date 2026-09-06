# Implementación lineamientos — Fase 4

Referencia: [`PROPUESTA_ADAPTADA_ETL.md`](PROPUESTA_ADAPTADA_ETL.md) secciones 4 y 6.

## Código

| Módulo | Fase | Entregable lineamiento |
|---|---|---|
| `logica/dwh/calidad.py` | 4 | R01–R05, `MI_DQ_HALLAZGO`, `MI_QA_AMARRE`, `MI_QA_AMARRE_DETALLE` (H9) |
| `logica/dwh/pipeline.py` | 2–7 | Orquestación |

## Reglas implementadas

| Regla | Descripción |
|---|---|
| R01 | Completitud: `COD_MA` (Sheets), `CUM`/`CAM` (GAPPS/SISUD) |
| R02 | Formato CUM (11 dígitos) y CAM (11 o 13) |
| R03 | Coherencia temporal: vencimiento ≥ notificación |
| R04 | `MONTO_UIT` ≥ 0 |
| R05 | `MONTO_S` vs `MONTO_UIT × UIT(año)` con tolerancia 1% |

Las filas no conformes se marcan con `FG_CONFORME = N` pero **no se eliminan**.

## Amarre H9

| Tabla Oracle | Contenido |
|---|---|
| `MI_QA_AMARRE` | Resumen por puente (`N_IZQ`, `N_DER`, `N_MATCH`, `PCT_MATCH_IZQ`) |
| `MI_QA_AMARRE_DETALLE` | Claves sin match (`LADO` = `SOLO_IZQ` / `SOLO_DER`, `CLAVE`, `MOTIVO`) |

Puentes típicos: `COD_MA_vs_EXPEDIENTE_excel`, `COD_MA_vs_CUM_SISUD`, `CUM_SISUD_vs_GAPP`.  
K5 sigue siendo el agregado; el detalle es lo que pide auditoría/CSEP en la práctica.

## Criterio de avance

- Las 5 reglas se ejecutan sin error en cada corrida.
- `MI_DQ_HALLAZGO`, `MI_QA_AMARRE` y `MI_QA_AMARRE_DETALLE` se cargan a BD_CURSOR vía `cargar_dw.py`.
- `./init.sh` exige filas en ambas tablas QA.

## Verificación

```bash
./init.sh
```

Revisar log: `FG_CONFORME`, `MI_DQ_HALLAZGO`, `MI_QA_AMARRE`, `MI_QA_AMARRE_DETALLE`.
