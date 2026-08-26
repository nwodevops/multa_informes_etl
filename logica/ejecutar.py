# =============================================================================
# Único .py en logica/ (main.py lo auto-descubre).
# Lineamientos PROPUESTA_ADAPTADA_ETL.md — Fases 2–7.
# Salidas: PROF_*, DICCIONARIO, DF_*, DQ_*, QA_*, DIM_*, FACT_*, DET_*, MI_INDICADOR_RESULTADO.
# =============================================================================

from pathlib import Path

from dwh.pipeline import ejecutar

_root = Path(__file__).resolve().parent.parent

_out = ejecutar(
    GS1,
    GS2,
    ETAPAS,
    ORA,
    MYSQL,
    INFORMES,
    dic_tablas=DIC_TABLAS,
    dic_variables=DIC_VARIABLES,
    root=_root,
)

PROF_RESUMEN = _out["PROF_RESUMEN"]
PROF_HALLAZGO = _out["PROF_HALLAZGO"]
DICCIONARIO = _out["DICCIONARIO"]
DF_MULTAS = _out["DF_MULTAS"]
DF_INFORMES = _out["DF_INFORMES"]
DF_ETAPAS = _out["DF_ETAPAS"]
MI_DQ_HALLAZGO = _out["MI_DQ_HALLAZGO"]
QA_AMARRE = _out["QA_AMARRE"]
MI_DIM_TIEMPO = _out["MI_DIM_TIEMPO"]
MI_DIM_ADMINISTRADO = _out["MI_DIM_ADMINISTRADO"]
MI_DIM_ORGANO_UNIDAD = _out["MI_DIM_ORGANO_UNIDAD"]
MI_DIM_MATERIA_SUBSECTOR = _out["MI_DIM_MATERIA_SUBSECTOR"]
MI_DIM_ESTADO = _out["MI_DIM_ESTADO"]
MI_DIM_PARAMETRO_UIT = _out["MI_DIM_PARAMETRO_UIT"]
MI_FACT_INFORME_SUPERVISION = _out["MI_FACT_INFORME_SUPERVISION"]
MI_FACT_MULTA_COERCITIVA = _out["MI_FACT_MULTA_COERCITIVA"]
MI_DET_ETAPA_MC = _out["MI_DET_ETAPA_MC"]
MI_INDICADOR_RESULTADO = _out["MI_INDICADOR_RESULTADO"]
RESULTADO = _out["RESULTADO"]
