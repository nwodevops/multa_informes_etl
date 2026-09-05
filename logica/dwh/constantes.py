"""Constantes de corrida y mapa de fuentes F1/F2/F4/F5 (multas)."""

from __future__ import annotations

from datetime import datetime

ID_CARGA = datetime.now().strftime("%Y%m%d%H%M%S")
FECHA_CARGA = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

VACIOS = {"", "#N/A", "#NA", "N/A", "NA", "NULL", "NONE", "-", "—", "#REF!", "#VALUE!"}

# F1=familia Excel OD (GS2*), F2=GS1 CAGR, F4=MYSQL, F5=ORA
FUENTE_REGISTRO = {
    "GS2": "OD_EXCEL",
    "GS1": "CAGR",
    "MYSQL": "GAPPS",
    "ORA": "SISUD_VW",
    "ETAPAS": "CAGR",
}

# Lectura H2 -> COD_OD (familia f1_od). Ampliar al cablear otra oficina.
F1_OD_LECTURAS: dict[str, str] = {
    "GS2": "LAMBAYEQUE",
    "GS2_ICA": "ICA",
    "GS2_PUNO": "PUNO",
}

STG_FUENTE = {
    "GS1": ("F2", "STG_GS1_MULTAS_COERCITIVAS", "CAGR multas"),
    "GS2": ("F1", "STG_GS2_MULTAS_COERCITIVAS", "Lambayeque multas"),
    "GS2_ICA": ("F1", "STG_GS2_ICA_MULTAS_COERCITIVAS", "Ica multas"),
    "GS2_PUNO": ("F1", "STG_GS2_PUNO_MULTAS_COERCITIVAS", "Puno multas"),
    "ETAPAS": ("F2-ET", "STG_GS1_ETAPAS", "CAGR etapas"),
    "ORA": ("F5", "STG_ORA_VW_MULTA_COERCITIVA", "SISUD vista multas"),
    "MYSQL": ("F4", "STG_MYSQL_T_MVC_MULTACOERCITIVA", "GAPP multas"),
    "DIC_TABLAS": ("F2", "STG_GS1_DIC_TABLAS", "DIC_TABLAS"),
    "DIC_VARIABLES": ("F2", "STG_GS1_DIC_VARIABLES", "DIC_VARIABLES"),
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

EXCEL_CAGR = "input_excel/CAGR_ MA OEFA - 3) MULTAS COERCITIVAS.xlsx"
