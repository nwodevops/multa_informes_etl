# Zona de pegado de logica (capa post-staging). Fuera de python/.

- En la raiz de `logica/` hay **un solo** `.py`: `ejecutar.py`. `python/main.py` lo auto-descubre.
- Negocio: paquete `dwh/` segun [`docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md`](../docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md) Fases 2–4.
  - `perfilamiento.py` — Fase 2: PROF_RESUMEN, PROF_HALLAZGO (H1–H9)
  - `diccionario.py` — Fase 2: DICCIONARIO
  - `homologacion.py` — Fase 3: CUM/CAM, fechas, texto, estados
  - `integracion.py` — Fase 3: DF_MULTAS, DF_INFORMES, DF_ETAPAS
  - `calidad.py` — Fase 4: R01–R05, DQ_HALLAZGO, QA_AMARRE (H9)
  - `dimensional.py` — Fase 5: DIM_*, FACT_*, DET_ETAPA_MC
  - `indicadores.py` — Fase 7: INDICADOR_RESULTADO (K1–K5)
  - `pipeline.py` — orquesta Fase 2 + 3 + 4 + 5 + 6 + 7 (carga vía main.py)
- Entrada: DataFrames de `LECTURAS`. Salida: en memoria (ver `python/CONTRATO.md`).
- No abrir conexiones aqui.
