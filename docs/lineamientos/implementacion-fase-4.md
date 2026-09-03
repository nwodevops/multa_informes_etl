# Implementación lineamientos — Fase 4

Referencia: [`PROPUESTA_ADAPTADA_ETL.md`](PROPUESTA_ADAPTADA_ETL.md) secciones 4 y 6.

## Código

| Módulo | Fase | Entregable lineamiento |
|---|---|---|
| `logica/dwh/calidad.py` | 4 | Reglas R01–R05, `MI_DQ_HALLAZGO`, `QA_AMARRE` (H9) |
| `logica/dwh/pipeline.py` | 2–4 | Orquestación extendida |

## Reglas implementadas

| Regla | Descripción |
|---|---|
| R01 | Completitud: `COD_MA` (Excel), `CUM`/`CAM` (GAPPS/SISUD) |
| R02 | Formato CUM (11 dígitos) y CAM (11 o 13) |
| R03 | Coherencia temporal: vencimiento ≥ notificación |
| R04 | `MONTO_UIT` ≥ 0 |
| R05 | `MONTO_S` vs `MONTO_UIT × UIT(año)` con tolerancia 1% |

Las filas no conformes se marcan con `FG_CONFORME = N` pero **no se eliminan**.

## Criterio de avance

- Las 5 reglas se ejecutan sin error en cada corrida.
- `MI_DQ_HALLAZGO` listo para insertar (append a BD_CURSOR vía `python/io/escribir_dw.py` si hay credenciales).
- `QA_AMARRE` reporta % de amarre entre puentes de fuentes (H9).

## Verificación

```bash
./switch-env.sh local
./h2/scripts/reset_and_create.sh
.venv/bin/python python/create_stg.py
# Cargar STG con wf_main.hwf (Excel + Oracle + MySQL)
.venv/bin/python python/main.py
```

Revisar log: `FG_CONFORME`, conteos de `MI_DQ_HALLAZGO`, filas de `QA_AMARRE`.

## Pendiente (Fases 5–7)

- `FACT_*` / `DIM_*` en memoria y carga Oracle (Fases 5–6)
- `MI_INDICADOR_RESULTADO` K1–K5 (Fase 7)
