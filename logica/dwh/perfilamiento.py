"""Fase 2 — perfilamiento de tablas STG (nulos, duplicados, formatos, H1–H9)."""

from __future__ import annotations

import pandas as pd

from .constantes import HALLAZGOS, ID_CARGA, STG_FUENTE
from .homologacion import cols_fecha, cols_monto, parse_fecha_serie, parse_monto, vacio


def _pct(n: int, total: int) -> float:
    return round(100.0 * n / total, 2) if total else 0.0


def _dominio_top(s: pd.Series, n: int = 5) -> str:
    if s.empty:
        return ""
    vc = s.astype("string").value_counts().head(n)
    return "; ".join(f"{k}({v})" for k, v in vc.items())


def perfilar_tabla(
    df: pd.DataFrame, clave_lectura: str
) -> tuple[list[dict], list[dict]]:
    """Devuelve filas PROF_RESUMEN y PROF_HALLAZGO para una tabla STG."""
    fid, tabla, desc = STG_FUENTE.get(clave_lectura, ("?", clave_lectura, clave_lectura))
    n_filas = len(df)
    resumen: list[dict] = []
    hallazgos: list[dict] = []

    if n_filas == 0:
        hallazgos.append(
            {
                "ID_CARGA": ID_CARGA,
                "HALLAZGO": "H1",
                "DESCRIPCION": HALLAZGOS["H1"],
                "FUENTE": fid,
                "TABLA": tabla,
                "DETALLE": "Tabla STG vacía en esta corrida",
            }
        )

    for col in df.columns:
        s = df[col]
        n_nulos = int(s.map(vacio).sum())
        resumen.append(
            {
                "ID_CARGA": ID_CARGA,
                "FUENTE_ID": fid,
                "TABLA": tabla,
                "CAMPO": col,
                "N_FILAS": n_filas,
                "N_NULOS": n_nulos,
                "PCT_NULOS": _pct(n_nulos, n_filas),
                "N_DISTINTOS": int(s.nunique(dropna=True)),
                "DOMINIO_TOP": _dominio_top(s),
                "TIPO_INFERIDO": str(s.dtype),
            }
        )

    # H1 filas casi vacías
    if n_filas:
        no_vacias = df.apply(lambda row: sum(not vacio(v) for v in row), axis=1)
        n_casi_vacias = int((no_vacias <= 1).sum())
        if n_casi_vacias:
            hallazgos.append(
                {
                    "ID_CARGA": ID_CARGA,
                    "HALLAZGO": "H1",
                    "DESCRIPCION": HALLAZGOS["H1"],
                    "FUENTE": fid,
                    "TABLA": tabla,
                    "DETALLE": f"filas_casi_vacias={n_casi_vacias}",
                }
            )

    # H2 CAM/CUM longitudes mixtas
    for col in df.columns:
        u = str(col).upper()
        if u not in ("CAM", "CUM", "TX_IDCAM", "TX_IDCUM"):
            continue
        lens = df[col].dropna().astype(str).str.replace(r"\D", "", regex=True).str.len()
        if lens.empty:
            continue
        uniq = sorted(lens.unique())
        if len(uniq) > 1:
            hallazgos.append(
                {
                    "ID_CARGA": ID_CARGA,
                    "HALLAZGO": "H2",
                    "DESCRIPCION": HALLAZGOS["H2"],
                    "FUENTE": fid,
                    "TABLA": tabla,
                    "DETALLE": f"col={col} longitudes={uniq}",
                }
            )

    # H3 saltos de línea
    for col in df.select_dtypes(include=["object", "string"]).columns:
        mask = df[col].astype("string").str.contains(r"[\r\n]", regex=True, na=False)
        n = int(mask.sum())
        if n:
            hallazgos.append(
                {
                    "ID_CARGA": ID_CARGA,
                    "HALLAZGO": "H3",
                    "DESCRIPCION": HALLAZGOS["H3"],
                    "FUENTE": fid,
                    "TABLA": tabla,
                    "DETALLE": f"col={col} filas={n}",
                }
            )

    # H4 fechas no parseables
    for col in cols_fecha(df):
        malas = ~df[col].map(vacio) & parse_fecha_serie(df[col]).isna()
        n = int(malas.sum())
        if n:
            hallazgos.append(
                {
                    "ID_CARGA": ID_CARGA,
                    "HALLAZGO": "H4",
                    "DESCRIPCION": HALLAZGOS["H4"],
                    "FUENTE": fid,
                    "TABLA": tabla,
                    "DETALLE": f"col={col} no_parseables={n}",
                }
            )

    # H5 tokens error
    for col in df.columns:
        s = df[col].astype("string").str.upper()
        n = int(s.isin({"#N/A", "#REF!", "#VALUE!", "#NAME?"}).sum())
        if n:
            hallazgos.append(
                {
                    "ID_CARGA": ID_CARGA,
                    "HALLAZGO": "H5",
                    "DESCRIPCION": HALLAZGOS["H5"],
                    "FUENTE": fid,
                    "TABLA": tabla,
                    "DETALLE": f"col={col} tokens_error={n}",
                }
            )

    # H6 #REF en diccionarios
    if clave_lectura in ("DIC_TABLAS", "DIC_VARIABLES"):
        n_ref = 0
        if n_filas:
            for col in df.columns:
                n_ref += int(
                    df[col].astype("string").str.contains("#REF!", na=False).sum()
                )
        if n_ref or n_filas == 0:
            hallazgos.append(
                {
                    "ID_CARGA": ID_CARGA,
                    "HALLAZGO": "H6",
                    "DESCRIPCION": HALLAZGOS["H6"],
                    "FUENTE": fid,
                    "TABLA": tabla,
                    "DETALLE": f"filas_ref_o_vacio ref={n_ref} filas={n_filas}",
                }
            )

    # H7 dos versiones multas (solo tablas multas)
    if clave_lectura in ("GS1", "GS2"):
        hallazgos.append(
            {
                "ID_CARGA": ID_CARGA,
                "HALLAZGO": "H7",
                "DESCRIPCION": HALLAZGOS["H7"],
                "FUENTE": fid,
                "TABLA": tabla,
                "DETALLE": f"columnas={len(df.columns)} filas={n_filas}",
            }
        )

    # H8 estados texto libre
    for col in df.columns:
        if "ESTADO" not in str(col).upper() and col != "TXESTADO":
            continue
        hallazgos.append(
            {
                "ID_CARGA": ID_CARGA,
                "HALLAZGO": "H8",
                "DESCRIPCION": HALLAZGOS["H8"],
                "FUENTE": fid,
                "TABLA": tabla,
                "DETALLE": f"col={col} dominio={_dominio_top(df[col], 8)}",
            }
        )

    return resumen, hallazgos


def perfilar_todas(tablas: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    todos_res: list[dict] = []
    todos_hal: list[dict] = []
    for clave, df in tablas.items():
        if clave.startswith("DIC_") or clave in STG_FUENTE:
            r, h = perfilar_tabla(df, clave)
            todos_res.extend(r)
            todos_hal.extend(h)

    # H9 — sin llave conformada (evidencia agregada)
    todos_hal.append(
        {
            "ID_CARGA": ID_CARGA,
            "HALLAZGO": "H9",
            "DESCRIPCION": HALLAZGOS["H9"],
            "FUENTE": "F1-F5",
            "TABLA": "CRUCE",
            "DETALLE": "Integración por UNION con FUENTE_ORIGEN; amarre diferido a Fase 4+",
        }
    )

    prof_resumen = pd.DataFrame(todos_res) if todos_res else pd.DataFrame()
    prof_hallazgo = pd.DataFrame(todos_hal) if todos_hal else pd.DataFrame()
    return prof_resumen, prof_hallazgo
