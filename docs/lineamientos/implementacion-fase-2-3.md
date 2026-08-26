# Implementación lineamientos — Fases 2 y 3

Referencia: [`PROPUESTA_ADAPTADA_ETL.md`](PROPUESTA_ADAPTADA_ETL.md) sección 6.

## Código

| Módulo | Fase | Entregable lineamiento |
|---|---|---|
| `logica/dwh/perfilamiento.py` | 2 | Reporte de perfilamiento |
| `logica/dwh/diccionario.py` | 2 | Diccionario de datos |
| `logica/dwh/homologacion.py` | 3 | Normalización CUM/CAM, fechas, texto, estados |
| `logica/dwh/integracion.py` | 3 | Dataframes integrados tipificados |
| `logica/dwh/pipeline.py` | 2–3 | Orquestación |

## Criterios de avance

**Fase 2:** todo campo F1–F5 en `DICCIONARIO`; `PROF_HALLAZGO` documenta H1–H9.

**Fase 3:** `DF_MULTAS`, `DF_INFORMES`, `DF_ETAPAS` sin errores de tipo; estados mapeados a catálogo `MI_DIM_ESTADO` (semillas ddl/01).

## Verificación

```bash
./h2/scripts/reset_and_create.sh
.venv/bin/python python/create_stg.py
# Cargar STG con Hop wf_main o datos de prueba
.venv/bin/python python/main.py
```

Revisar log: conteos de `PROF_*`, `DICCIONARIO`, `DF_*`.

## Pendiente (Fase 4+)

- ~~Reglas R01–R05 → `MI_DQ_HALLAZGO`~~ → ver [`implementacion-fase-4.md`](implementacion-fase-4.md)
- `FACT_*` / `DIM_*` en memoria y carga Oracle (Fases 5–6)
- `MI_INDICADOR_RESULTADO` K1–K5 (Fase 7)
