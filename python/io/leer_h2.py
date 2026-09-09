"""ENTRADA post-staging: H2 STG_* (ya cargadas por Hop) → pandas DataFrames.

Lo llama python/main.py justo después de la acción Hop «Run Python».
Las claves del dict (GS1, GS2, …) se inyectan en logica/ejecutar.py.

Contrato: F1=GS2 OD, F2=GS1 CSEP (+ETAPAS), F5=ORA SISUD, + DIC_* legacy.
Si una tabla STG no existe, se avisa y se deja DataFrame vacío (no aborta toda la corrida).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from h2_conn import connect_h2

# nombre lógico (inyectado a logica/) → SQL sobre H2 PUBLIC
LECTURAS: dict[str, str] = {
    "GS1": "SELECT * FROM PUBLIC.STG_GS1_CSEP_MULTAS",  # F2 CSEP multas
    "ETAPAS": "SELECT * FROM PUBLIC.STG_GS1_ETAPAS",  # F2 etapas
    "GS2": "SELECT * FROM PUBLIC.STG_GS2_OD_MULTAS",  # F1 OD multas
    "ORA": "SELECT * FROM PUBLIC.STG_ORA_VW_MULTA_COERCITIVA",  # F5 SISUD
    "DIC_TABLAS": "SELECT * FROM PUBLIC.STG_GS1_DIC_TABLAS",
    "DIC_VARIABLES": "SELECT * FROM PUBLIC.STG_GS1_DIC_VARIABLES",
}


def _coerce_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza columnas datetime64 a date (más amable para Oracle/downstream)."""
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = pd.to_datetime(out[col]).dt.date
    return out


def leer_h2(root: Path, variables: dict[str, str]) -> dict[str, pd.DataFrame]:
    """Abre H2 mem:csep, ejecuta LECTURAS y cierra. Devuelve {nombre: DataFrame}."""
    # STEP 2.1: validar que exista el catálogo de lecturas.
    if not LECTURAS:
        raise ValueError("LECTURAS vacío; agrega al menos una query en python/io/leer_h2.py")

    # STEP 2.2: abrir la conexión H2 y ejecutar cada SELECT STG_*.
    conn = connect_h2(root, variables)
    datos: dict[str, pd.DataFrame] = {}
    try:
        cur = conn.cursor()
        try:
            for nombre, query in LECTURAS.items():
                try:
                    cur.execute(query)
                except Exception as exc:
                    # Tabla ausente / stage parcial: no tumbar toda la corrida
                    msg = str(exc).split("\n")[0][:120]
                    print(f"AVISO: {nombre} no disponible en H2 ({msg}); DataFrame vacío")
                    datos[nombre] = pd.DataFrame()
                    continue
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
                df = pd.DataFrame.from_records(rows, columns=cols)
                # STEP 2.3: normalizar fechas y guardar cada lectura por nombre lógico.
                datos[nombre] = _coerce_dates(df)
                print(f"{nombre}: {len(datos[nombre])} x {len(datos[nombre].columns)}")
        finally:
            cur.close()
    finally:
        conn.close()
    return datos
