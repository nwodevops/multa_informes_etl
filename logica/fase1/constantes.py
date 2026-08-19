"""Constantes y llaves candidatas de la fase 1."""

from __future__ import annotations

import subprocess
from datetime import datetime

ID_CORRIDA = datetime.now().strftime("%Y%m%d%H%M%S")
FECHA_CORRIDA = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
VACIOS = {"", "#N/A", "#NA", "N/A", "NA", "NULL", "NONE", "-", "—"}
MAX_EXC_POR_TABLA = 2000

LLAVES: dict[str, list[str]] = {
    "GS1": ["COD_MA"],
    "GS2": ["COD_MA"],
    "ETAPAS": ["COD_PROY_MC", "NRO_ETAPA_MC"],
    "ORA": ["NUMERO_EXPEDIENTE"],
    "MYSQL": ["NU_IDINFORMACIONMC"],
    "INFORMES": ["IDACTIVIDAD"],
    "INT_MC_EXCEL": ["COD_MA"],
    "INT_MC_ETAPAS": ["COD_PROY_MC", "NRO_ETAPA_MC"],
    "INT_MC_SISUD": ["NUMERO_EXPEDIENTE"],
    "INT_MC_GAPP": ["NU_IDINFORMACIONMC"],
    "INT_INFORMES": ["IDACTIVIDAD"],
}

MONTO_HINT = ("MULTA", "MONTO")
COLS_QA_EXC = [
    "ID_CORRIDA",
    "FECHA_CORRIDA",
    "TABLA",
    "FUENTE",
    "TIPO",
    "LLAVE",
    "DETALLE",
]


def detalle_corrida() -> str:
    try:
        rama = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return f"id={ID_CORRIDA} rama={rama} commit={commit}"
    except Exception:
        return f"id={ID_CORRIDA} git=n/d"


DETALLE = detalle_corrida()
