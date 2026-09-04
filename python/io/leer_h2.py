"""ENTRADA post-staging: H2 STG_* ya cargadas -> pandas DataFrames.

Contrato lineamientos F1/F2/F4/F5 (multas) + diccionario F2 (DIC_*).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from h2_conn import connect_h2


LECTURAS: dict[str, str] = {
    "GS1": "SELECT * FROM PUBLIC.STG_GS1_MULTAS_COERCITIVAS",
    "ETAPAS": "SELECT * FROM PUBLIC.STG_GS1_ETAPAS",
    "GS2": "SELECT * FROM PUBLIC.STG_GS2_MULTAS_COERCITIVAS",
    "ORA": "SELECT * FROM PUBLIC.STG_ORA_VW_MULTA_COERCITIVA",
    "MYSQL": "SELECT * FROM PUBLIC.STG_MYSQL_T_MVC_MULTACOERCITIVA",
    "DIC_TABLAS": "SELECT * FROM PUBLIC.STG_GS1_DIC_TABLAS",
    "DIC_VARIABLES": "SELECT * FROM PUBLIC.STG_GS1_DIC_VARIABLES",
}


def _coerce_dates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = pd.to_datetime(out[col]).dt.date
    return out


def leer_h2(root: Path, variables: dict[str, str]) -> dict[str, pd.DataFrame]:
    if not LECTURAS:
        raise ValueError("LECTURAS vacío; agrega al menos una query en python/io/leer_h2.py")

    conn = connect_h2(root, variables)
    datos: dict[str, pd.DataFrame] = {}
    try:
        cur = conn.cursor()
        try:
            for nombre, query in LECTURAS.items():
                try:
                    cur.execute(query)
                except Exception as exc:
                    msg = str(exc).split("\n")[0][:120]
                    print(f"AVISO: {nombre} no disponible en H2 ({msg}); DataFrame vacío")
                    datos[nombre] = pd.DataFrame()
                    continue
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
                df = pd.DataFrame.from_records(rows, columns=cols)
                datos[nombre] = _coerce_dates(df)
                print(f"{nombre}: {len(datos[nombre])} x {len(datos[nombre].columns)}")
        finally:
            cur.close()
    finally:
        conn.close()
    return datos
