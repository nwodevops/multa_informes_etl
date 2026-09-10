# Implementación lineamientos — Fases 2 y 3

Referencia: [`PROPUESTA_ADAPTADA_ETL.md`](PROPUESTA_ADAPTADA_ETL.md) sección 6.

## Código

| Módulo | Fase | Entregable lineamiento |
|---|---|---|
| `logica/dwh/perfilamiento.py` | 2 | Reporte de perfilamiento |
| `logica/dwh/diccionario.py` | 2 | Diccionario de datos |
| `logica/dwh/homologacion.py` | 3 | Normalización CUM/CAM, fechas, texto, estados |
| `logica/dwh/integracion.py` | 3 | Dataframes intermedios tipificados por fuente |
| `logica/dwh/pipeline.py` | 2–3 | Orquestación |

## Criterios de avance

**Fase 2:** campos de fuentes activas **F1+F2+F5** en `DICCIONARIO`; `PROF_HALLAZGO` documenta H1–H9. (F3/F4 no se perfilan en corrida.)

**Fase 3:** intermedios tipificados **sin merge a un solo fact**:
- `df_csep` (F2), `df_od` (F1), `df_sisud` (F5), `DF_ETAPAS` (F2-ET)
- Estados mapeados a catálogo `DW_M_DIM_ESTADO` (semillas ddl/01)
- El enriquecido Sheet←SISUD ocurre **después**, en Oracle (`07_enrich_sheets_sisud.sql`)

## Verificación

```bash
./h2/scripts/reset_and_create.sh
.venv/bin/python python/create_stg.py
# Cargar STG con Hop wf_main o datos de prueba
.venv/bin/python python/main.py
```

Revisar log: conteos de `PROF_*`, `DICCIONARIO`, intermedios F1/F2/F5 / `DF_ETAPAS`.

## Pendiente (Fase 4+)

- ~~Reglas R01–R05 → `DW_M_DQ_HALLAZGO`~~ → ver [`implementacion-fase-4.md`](implementacion-fase-4.md)
- ~~3 facts evidencia + enrich 07~~ → ver [`implementacion-fase-5-6.md`](implementacion-fase-5-6.md)
- `DW_M_INDICADOR_RESULTADO` K1–K5 (Fase 7)
