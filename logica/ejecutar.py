# =============================================================================
# Unico .py en logica/ (main.py lo auto-descubre). El negocio vive en fase1/.
# No filtra filas. No homologa. No marca FG_VALIDO (eso es fase 2).
# =============================================================================

from fase1.pipeline import ejecutar

_out = ejecutar(GS1, GS2, ETAPAS, ORA, MYSQL, INFORMES)
INT_MC_EXCEL = _out["INT_MC_EXCEL"]
INT_MC_ETAPAS = _out["INT_MC_ETAPAS"]
INT_MC_SISUD = _out["INT_MC_SISUD"]
INT_MC_GAPP = _out["INT_MC_GAPP"]
INT_INFORMES = _out["INT_INFORMES"]
QA_CORRIDA = _out["QA_CORRIDA"]
QA_EXCEPCION = _out["QA_EXCEPCION"]
RESULTADO = _out["RESULTADO"]
