# =============================================================================
# Único .py en logica/ (main.py lo auto-descubre).
# Lineamientos PROPUESTA_ADAPTADA_ETL.md — Fases 2–7. DW netamente Multas.
# 3 facts evidencia; enrich Sheets←SISUD en Oracle SQL 07 (cargar_dw). Sin MySQL.
# =============================================================================

from pathlib import Path

from dwh.pipeline import ejecutar

_root = Path(__file__).resolve().parent.parent

_out = ejecutar(
    GS1,
    GS2,
    ETAPAS,
    ORA,
    dic_tablas=DIC_TABLAS,
    dic_variables=DIC_VARIABLES,
    root=_root,
)

PROF_RESUMEN = _out["PROF_RESUMEN"]
PROF_HALLAZGO = _out["PROF_HALLAZGO"]
DICCIONARIO = _out["DICCIONARIO"]
DF_MULTAS = _out["DF_MULTAS"]
DF_CSEP = _out["DF_CSEP"]
DF_OD = _out["DF_OD"]
DF_SISUD = _out["DF_SISUD"]
DF_ETAPAS = _out["DF_ETAPAS"]
MI_DQ_HALLAZGO = _out["MI_DQ_HALLAZGO"]
MI_QA_AMARRE = _out["MI_QA_AMARRE"]
MI_QA_AMARRE_DETALLE = _out["MI_QA_AMARRE_DETALLE"]
MI_DIM_TIEMPO = _out["MI_DIM_TIEMPO"]
MI_DIM_ADMINISTRADO = _out["MI_DIM_ADMINISTRADO"]
MI_DIM_ORGANO_UNIDAD = _out["MI_DIM_ORGANO_UNIDAD"]
MI_DIM_OD = _out["MI_DIM_OD"]
MI_DIM_FUENTE_REGISTRO = _out["MI_DIM_FUENTE_REGISTRO"]
MI_DIM_MATERIA_SUBSECTOR = _out["MI_DIM_MATERIA_SUBSECTOR"]
MI_DIM_ESTADO = _out["MI_DIM_ESTADO"]
MI_DIM_PARAMETRO_UIT = _out["MI_DIM_PARAMETRO_UIT"]
MI_FACT_MC_CSEP = _out["MI_FACT_MC_CSEP"]
MI_FACT_MC_OD = _out["MI_FACT_MC_OD"]
MI_FACT_MC_SISUD = _out["MI_FACT_MC_SISUD"]
MI_DET_ETAPA_MC = _out["MI_DET_ETAPA_MC"]
MI_INDICADOR_RESULTADO = _out["MI_INDICADOR_RESULTADO"]
RESULTADO = _out["RESULTADO"]
