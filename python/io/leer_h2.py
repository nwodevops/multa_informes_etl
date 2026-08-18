"""ENTRADA genérica: H2 mem:csep -> pandas DataFrames.

La dict `LECTURAS` define el contrato de entrada de la lógica:
  nombre -> query SQL sobre H2.
Cada clave se convierte en un DataFrame con ESE MISMO nombre (lo inyecta main.py).

PARA UN ETL NUEVO: agregar/editar entradas en `LECTURAS` (no tocar el resto).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from h2_ddl import connect_h2


LECTURAS: dict[str, str] = {
    "DEMO": "SELECT ID, TXNOMBRE, FEALTA FROM PUBLIC.DEMO_TABLA_EJEMPLO",
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
                cur.execute(query)
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
