# Implementación lineamientos — Fases 5 y 6

Referencia: [`PROPUESTA_ADAPTADA_ETL.md`](PROPUESTA_ADAPTADA_ETL.md) secciones 3 y 6.

## Código

| Módulo | Fase | Entregable |
|---|---|---|
| `logica/dwh/dimensional.py` | 5 | `DIM_*`, `FACT_*`, `MI_DET_ETAPA_MC` en memoria |
| `python/io/cargar_dw.py` | 6 | TRUNCATE+INSERT a Oracle BD_CURSOR |
| `logica/dwh/pipeline.py` | 2–6 | Orquestación extendida |

## Fase 5 — criterio de avance

- Ningún hecho sin dimensión resuelta (fallback `ID_* = -1`).
- `MI_DET_ETAPA_MC.ID_MC` por `COD_PROY_MC` cuando existe hecho padre.

## Fase 6 — criterio de avance

- DDL formal en `ddl/01`, `02`, `03` aplicado si no existía.
- Vistas legacy `VW_FCT_*_VALIDADA` eliminadas.
- `COUNT(*)` en Oracle = filas del DataFrame por tabla.

## Verificación

```bash
# Tras wf_main.hwf (H2 poblado)
.venv/bin/python python/main.py
```

Esperado (datos actuales F1/F2/F4/F5): ~571 multas, 55 etapas en hechos.

## Pendiente (Fase 7+)

- Ver [`implementacion-fase-7.md`](implementacion-fase-7.md) — Fase 7 implementada. Fase 8 Power BI: **fuera de alcance**.
