"""Constantes de corrida y mapa de fuentes F1/F2/F4/F5 (multas).

ID_CARGA / FECHA_CARGA: se fijan al importar el módulo (una corrida = un id).
FUENTE_REGISTRO: alias staging Hop → código de linaje que viaja en FUENTE_ORIGEN / ID_FUENTE.
VACIOS: tokens que homologacion.vacio() trata como null (errores típicos de Sheets).
"""

from __future__ import annotations

from datetime import datetime

ID_CARGA = datetime.now().strftime("%Y%m%d%H%M%S")
FECHA_CARGA = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Tokens de planilla / Excel que NO son dato real
VACIOS = {"", "#N/A", "#NA", "N/A", "NA", "NULL", "NONE", "-", "—", "#REF!", "#VALUE!"}

# Clave Hop/staging → código linaje en DF / DIM_FUENTE_REGISTRO
# F1=OD (GS2), F2=sede central (GS1, código histórico CAGR), F5=ORA
FUENTE_REGISTRO = {
    "GS2": "OD_SHEETS",
    "GS1": "CAGR",
    "ORA": "SISUD_VW",
    "MYSQL": "GAPPS",
    "ETAPAS": "CAGR",
}

# Semillas DW_M_DIM_FUENTE_REGISTRO (ID fijo; CODIGO = linaje). GAPPS/OD_EXCEL sin ingestión.
# NOMBRE es lo que se lee en el DW: Sede central vs OD. CAGR es alias interno, no una base CSEP.
SEMILLAS_FUENTE_REGISTRO = (
    (-1, "ND", "NO ESPECIFICADO", "ND", "NO ESPECIFICADO"),
    (1, "OD_SHEETS", "OD", "F1", "31 Google Sheets OD → STG_GS2_OD_MULTAS"),
    (2, "CAGR", "Sede central", "F2", "10 Google Sheets sede central → STG_GS1_CSEP_MULTAS / ETAPAS"),
    (3, "GAPPS", "MySQL GAPP", "F4", "gappsdb query → STG_MYSQL_MULTAS / DW_M_AUD_F4_GAPPS"),
    (4, "SISUD_VW", "Oracle SISUD", "F5", "SISUD.VW_MULTA_COERCITIVA → STG_ORA_*"),
    (5, "OD_EXCEL", "Excel OD (legacy)", "F1", "Alias histórico; el ETL normaliza a OD_SHEETS"),
)

STG_FUENTE = {
    "GS1": ("F2", "STG_GS1_CSEP_MULTAS", "Sede central Google Sheets multas"),
    "GS2": ("F1", "STG_GS2_OD_MULTAS", "OD Google Sheets multas"),
    "ETAPAS": ("F2-ET", "STG_GS1_ETAPAS", "Etapas sede central (Sheets)"),
    "ORA": ("F5", "STG_ORA_VW_MULTA_COERCITIVA", "SISUD vista multas"),
    "MYSQL": ("F4", "STG_MYSQL_MULTAS", "MySQL gapps query vw_multas_app"),
}

HALLAZGOS = {
    "H1": "Nulos en campos clave / filas casi vacías",
    "H2": "CAM con 11 y 13 dígitos en la misma columna",
    "H3": "Texto con saltos de línea embebidos",
    "H4": "Fechas heterogéneas entre motores",
    "H5": "Tokens de error Excel (#N/A, fórmulas)",
    "H6": "Catálogos IMPORTRANGE rotos",
    "H7": "Dos versiones del registro de multas (F1 vs F2)",
    "H8": "Estados como texto libre sin catálogo único",
    "H9": "Claves de cruce sin correspondencia total entre fuentes",
}
