# Implementación lineamientos — Fase 4

Referencia: [`PROPUESTA_ADAPTADA_ETL.md`](PROPUESTA_ADAPTADA_ETL.md) secciones 4 y 6.

## Código

| Módulo | Fase | Entregable lineamiento |
|---|---|---|
| `logica/dwh/calidad.py` | 4 | R01–R05, `DW_M_DQ_HALLAZGO`, `DW_M_QA_AMARRE`, `DW_M_QA_AMARRE_DETALLE` (H9) |
| `logica/dwh/pipeline.py` | 2–7 | Orquestación |

## Reglas implementadas

| Regla | Descripción |
|---|---|
| R01 | Completitud: `COD_MA` (Sheets F1/F2), `CUM`/`CAM` (SISUD F5) — **sin GAPPS/F4** |
| R02 | Formato CUM (11 dígitos) y CAM (11 o 13) |
| R03 | Coherencia temporal: vencimiento ≥ notificación |
| R04 | `MONTO_UIT` ≥ 0 |
| R05 | `MONTO_S` vs `MONTO_UIT × UIT(año)` con tolerancia 1% |

Las filas no conformes se marcan con `FG_CONFORME = N` pero **no se eliminan**.

## Amarre H9

| Tabla Oracle | Contenido |
|---|---|
| `DW_M_QA_AMARRE` | Resumen por puente (`N_IZQ`, `N_DER`, `N_MATCH`, `PCT_MATCH_IZQ`) |
| `DW_M_QA_AMARRE_DETALLE` | Claves sin match (`LADO` = `SOLO_IZQ` / `SOLO_DER`, `CLAVE`, `MOTIVO`) |

Puente vigente: **`RES_MONTO_Sheets_vs_SISUD`** (resolución normalizada + `MONTO_UIT`).  
K5 sigue siendo el agregado; el detalle es lo que pide auditoría/CSEP en la práctica.

## Criterio de avance

- Las 5 reglas se ejecutan sin error en cada corrida.
- `DW_M_DQ_HALLAZGO`, `DW_M_QA_AMARRE` y `DW_M_QA_AMARRE_DETALLE` se cargan a BD_CURSOR vía `cargar_dw.py`.
- `./init.sh` / `init.bat` exigen filas en ambas tablas QA.

## Verificación

```bash
./init.sh
```

Revisar log: `FG_CONFORME`, `DW_M_DQ_HALLAZGO`, `DW_M_QA_AMARRE`, `DW_M_QA_AMARRE_DETALLE`.
