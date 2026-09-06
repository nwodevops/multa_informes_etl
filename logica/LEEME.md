# Zona de pegado de logica (capa post-staging). Fuera de python/.

- En la raiz de `logica/` hay **un solo** `.py`: `ejecutar.py`. `python/main.py` lo auto-descubre.
- Negocio: paquete `dwh/` segun [`docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md`](../docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md) Fases 2–7.
  - `perfilamiento.py` — Fase 2: PROF_RESUMEN, PROF_HALLAZGO (H1–H9)
  - `diccionario.py` — Fase 2: DICCIONARIO
  - `homologacion.py` — Fase 3: CUM/CAM, fechas, texto, estados
  - `integracion.py` — Fase 3: DF_MULTAS, DF_ETAPAS (`FUENTE_ORIGEN`)
  - `calidad.py` — Fase 4: R01–R05, MI_DQ_HALLAZGO, MI_QA_AMARRE, MI_QA_AMARRE_DETALLE
  - `dimensional.py` — Fase 5: MI_DIM_*, MI_FACT_* (ID_FUENTE, ID_TIEMPO_FIRMA), MI_DET_ETAPA_MC
  - `indicadores.py` — Fase 7: MI_INDICADOR_RESULTADO (K1–K5)
  - `pipeline.py` — orquesta Fases 2–7 (carga Oracle vía main.py → cargar_dw.py)
- Entrada: DataFrames de `LECTURAS`. Salida: en memoria (ver `python/CONTRATO.md`).
- No abrir conexiones aqui.
