# =============================================================================
# Único .py en logica/ (main.py lo auto-descubre).
# Lineamientos PROPUESTA_ADAPTADA_ETL.md — Fases 2–7. DW netamente Multas.
#
# Flujo (quién llama a quién):
#   Hop deja STG_* en H2 → Python lee GS1/GS2/ETAPAS/ORA → este módulo
#   → dwh.pipeline.ejecutar(...) → DataFrames DW_M_* en memoria
#   → cargar_dw.py publica a Oracle + SQL 07 arma el fact enriquecido.
#
# Qué NO hace este módulo:
#   - No lee Sheets/Oracle fuente (eso es Hop).
#   - No hace el LEFT JOIN Sheet←SISUD (eso es docs/lineamientos/ddl/07_*.sql).
# Guía: docs/adjuntos/guia-codigo-logica-homologacion-facts.md
# =============================================================================

from pathlib import Path

from dwh.pipeline import ejecutar

_root = Path(__file__).resolve().parent.parent

# DataFrames inyectados por el runtime Hop/Python (staging H2 ya cargado):
#   GS1     = F2 CSEP multas (STG_GS1_CSEP_MULTAS)
#   GS2     = F1 OD multas   (STG_GS2_OD_MULTAS)
#   ETAPAS  = F2 etapas      (STG_GS1_ETAPAS)
#   ORA     = F5 SISUD       (STG_ORA_VW_MULTA_COERCITIVA)
#   DIC_*   = diccionario legacy (perfilamiento)
# STEP 4.1: delegar las fases de negocio al pipeline DWH.
_out = ejecutar(
    GS1,
    GS2,
    ETAPAS,
    ORA,
    dic_tablas=DIC_TABLAS,
    dic_variables=DIC_VARIABLES,
    root=_root,
)

# STEP 4.2: exponer en el namespace los DataFrames que main.py recolectará.
# Las salidas QA/K también se exponen, pero main.py decide después si se publican.
PROF_RESUMEN = _out["PROF_RESUMEN"]
PROF_HALLAZGO = _out["PROF_HALLAZGO"]
DICCIONARIO = _out["DICCIONARIO"]
DF_MULTAS = _out["DF_MULTAS"]          # UNION auxiliar CSEP∪OD∪SISUD (calidad/KPIs)
DF_CSEP = _out["DF_CSEP"]              # bloque canónico F2
DF_OD = _out["DF_OD"]                  # bloque canónico F1
DF_SISUD = _out["DF_SISUD"]            # bloque canónico F5
DF_ETAPAS = _out["DF_ETAPAS"]
DW_M_DQ_HALLAZGO = _out["DW_M_DQ_HALLAZGO"]
DW_M_QA_AMARRE = _out["DW_M_QA_AMARRE"]
DW_M_QA_AMARRE_DETALLE = _out["DW_M_QA_AMARRE_DETALLE"]
DW_M_DIM_TIEMPO = _out["DW_M_DIM_TIEMPO"]
DW_M_DIM_ADMINISTRADO = _out["DW_M_DIM_ADMINISTRADO"]
DW_M_DIM_ORGANO_UNIDAD = _out["DW_M_DIM_ORGANO_UNIDAD"]
DW_M_DIM_OD = _out["DW_M_DIM_OD"]
DW_M_DIM_FUENTE_REGISTRO = _out["DW_M_DIM_FUENTE_REGISTRO"]
DW_M_DIM_MATERIA_SUBSECTOR = _out["DW_M_DIM_MATERIA_SUBSECTOR"]
DW_M_DIM_ESTADO = _out["DW_M_DIM_ESTADO"]
DW_M_DIM_PARAMETRO_UIT = _out["DW_M_DIM_PARAMETRO_UIT"]
# Tres facts de EVIDENCIA (1 fila = 1 multa de UNA fuente). El de NEGOCIO se arma en SQL 07.
DW_M_FACT_MC_CSEP = _out["DW_M_FACT_MC_CSEP"]
DW_M_FACT_MC_OD = _out["DW_M_FACT_MC_OD"]
DW_M_FACT_MC_SISUD = _out["DW_M_FACT_MC_SISUD"]
DW_M_DET_ETAPA_MC = _out["DW_M_DET_ETAPA_MC"]
DW_M_INDICADOR_RESULTADO = _out["DW_M_INDICADOR_RESULTADO"]
RESULTADO = _out["RESULTADO"]
