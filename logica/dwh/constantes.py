"""Constantes de corrida y mapa de fuentes F1/F2/F5 (multas). Semilla GAPPS (F4) histórica."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

ID_CARGA = datetime.now().strftime("%Y%m%d%H%M%S")
FECHA_CARGA = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

VACIOS = {"", "#N/A", "#NA", "N/A", "NA", "NULL", "NONE", "-", "—", "#REF!", "#VALUE!"}

# F1=familia Sheets OD (GS2), F2=GS1 CSEP Sheets (FUENTE_REGISTRO CAGR), F5=ORA
FUENTE_REGISTRO = {
    "GS2": "OD_SHEETS",
    "GS1": "CAGR",
    "ORA": "SISUD_VW",
    "ETAPAS": "CAGR",
}

# Semillas MI_DIM_FUENTE_REGISTRO (ID fijo; CODIGO = linaje). GAPPS se conserva sin ingestión.
SEMILLAS_FUENTE_REGISTRO = (
    (-1, "ND", "NO ESPECIFICADO", "ND", "NO ESPECIFICADO"),
    (1, "OD_SHEETS", "Sheets OD", "F1", "31 Google Sheets OD → STG_GS2_OD_MULTAS"),
    (2, "CAGR", "Sheets CSEP", "F2", "10 Google Sheets CSEP → STG_GS1_CSEP_MULTAS / ETAPAS"),
    (3, "GAPPS", "MySQL GAPP (histórico)", "F4", "Fuera de ingestión; semilla conservada"),
    (4, "SISUD_VW", "Oracle SISUD", "F5", "SISUD.VW_MULTA_COERCITIVA → STG_ORA_*"),
    (5, "OD_EXCEL", "Excel OD (legacy)", "F1", "Alias histórico; el ETL normaliza a OD_SHEETS"),
)

# Lectura H2 unificada F1 (COD_OD viene en la STG). Ampliación = catálogo JSON.
F1_OD_LECTURAS: dict[str, str] = {"GS2": "*"}

STG_FUENTE = {
    "GS1": ("F2", "STG_GS1_CSEP_MULTAS", "CSEP Google Sheets multas"),
    "GS2": ("F1", "STG_GS2_OD_MULTAS", "ODs Google Sheets multas"),
    "ETAPAS": ("F2-ET", "STG_GS1_ETAPAS", "CSEP etapas (Sheets)"),
    "ORA": ("F5", "STG_ORA_VW_MULTA_COERCITIVA", "SISUD vista multas"),
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

EXCEL_CAGR = "input_excel/legacy/CAGR_ MA OEFA - 3) MULTAS COERCITIVAS.xlsx"
F1_OD_CATALOG = "docs/inputs/f1_ods_sheets.json"
F2_CSEP_CATALOG = "docs/inputs/f2_csep_sheets.json"


def load_f1_od_codigos(root: Path | None = None) -> list[str]:
    """Lista COD_OD activos del catálogo Sheets (sin CODE / consolidados)."""
    try:
        from f1_ods_catalog import active_ods, load_catalog
    except ImportError:
        import sys

        here = Path(__file__).resolve().parents[2] / "python"
        if str(here) not in sys.path:
            sys.path.insert(0, str(here))
        from f1_ods_catalog import active_ods, load_catalog

    base = root or Path(__file__).resolve().parents[2]
    return [str(o["cod_od"]) for o in active_ods(load_catalog(base))]
