# =============================================================================
# Único .py en logica/ (main.py lo auto-descubre).
# Lineamientos PROPUESTA_ADAPTADA_ETL.md — Fases 2–7.
# Salidas: PROF_*, DICCIONARIO, DF_*, DQ_*, QA_*, DIM_*, FACT_*, DET_*, INDICADOR_RESULTADO.
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
DQ_HALLAZGO = _out["DQ_HALLAZGO"]
QA_AMARRE = _out["QA_AMARRE"]
DIM_TIEMPO = _out["DIM_TIEMPO"]
DIM_ADMINISTRADO = _out["DIM_ADMINISTRADO"]
DIM_ORGANO_UNIDAD = _out["DIM_ORGANO_UNIDAD"]
DIM_MATERIA_SUBSECTOR = _out["DIM_MATERIA_SUBSECTOR"]
DIM_ESTADO = _out["DIM_ESTADO"]
DIM_PARAMETRO_UIT = _out["DIM_PARAMETRO_UIT"]
FACT_INFORME_SUPERVISION = _out["FACT_INFORME_SUPERVISION"]
FACT_MULTA_COERCITIVA = _out["FACT_MULTA_COERCITIVA"]
DET_ETAPA_MC = _out["DET_ETAPA_MC"]
INDICADOR_RESULTADO = _out["INDICADOR_RESULTADO"]
RESULTADO = _out["RESULTADO"]
