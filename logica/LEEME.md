# Zona de pegado de logica (capa post-staging). Fuera de python/.

- En la raiz de `logica/` hay **un solo** `.py`: `ejecutar.py`. `python/main.py` lo auto-descubre.
- Negocio: paquete `dwh/` segun [`docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md`](../docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md) Fases 2–7.
  - `perfilamiento.py` — Fase 2: PROF_RESUMEN, PROF_HALLAZGO (H1–H9)
  - `diccionario.py` — Fase 2: DICCIONARIO (STG DIC_* + catálogo estático)
  - `homologacion.py` — Fase 3: CUM/CAM, fechas, texto, estados
  - `integracion.py` — Fase 3: intermedios F1/F2/F5 + DF_ETAPAS (sin merge a un fact)
  - `calidad.py` — Fase 4: R01–R05 (sin GAPPS), MI_DQ_HALLAZGO, MI_QA_AMARRE* (`RES_MONTO_Sheets_vs_SISUD`) sobre UNION auxiliar `DF_MULTAS`
  - `dimensional.py` — Fase 5: MI_DIM_*, MI_FACT_MC_CSEP/_OD/_SISUD, MI_DET_ETAPA_MC (evidencia; **sin** fact enriquecido)
  - `indicadores.py` — Fase 7: MI_INDICADOR_RESULTADO (K1–K5)
  - `pipeline.py` — orquesta Fases 2–7 en memoria
- Enrich Sheets←SISUD (`MI_FACT_MULTA_COERCITIVA`) **no** corre aquí: lo hace `python/io/cargar_dw.py` con SQL `07` tras cargar evidencia.
- Entrada: DataFrames de `LECTURAS`. Salida: en memoria (ver `python/CONTRATO.md`).
- No abrir conexiones aqui.
- Manual: [`docs/lineamientos/extra/manual-como-se-arma-el-fact.md`](../docs/lineamientos/extra/manual-como-se-arma-el-fact.md).
