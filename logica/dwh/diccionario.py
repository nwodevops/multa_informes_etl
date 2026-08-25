"""Fase 2 — diccionario de datos (STG DIC_* + fallback catálogo institucional H6)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .catalogos import CATALOGO_CAMPOS
from .constantes import EXCEL_CAGR, ID_CARGA


def _desde_stg_dic_tablas(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    rows = []
    cols = {str(c).upper(): c for c in df.columns}
    ds = cols.get("DATASET", list(df.columns)[0] if len(df.columns) else None)
    desc = cols.get("DESCRIPCION / INSTRUCCIONES", cols.get("DESCRIPCION"))
    if ds is None:
        return []
    for _, row in df.iterrows():
        dataset = row.get(ds, "")
        if pd.isna(dataset) or str(dataset).strip().upper() in ("#REF!", ""):
            continue
        rows.append(
            {
                "ID_CARGA": ID_CARGA,
                "FUENTE": "F2",
                "DATASET": str(dataset).strip(),
                "CAMPO": "",
                "TIPO": "",
                "DESCRIPCION": str(row.get(desc, "")).strip() if desc else "",
                "ORIGEN": "STG_DIC_TABLAS",
            }
        )
    return rows


def _desde_stg_dic_variables(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    rows = []
    norm = {str(c).upper().strip(): c for c in df.columns}
    cod = norm.get("CODIGO CAMPO") or norm.get("CAMPO EN BD")
    desc = norm.get("DESCRIPCION")
    tipo = norm.get("TIPO DE VARIABLE")
    dataset = norm.get("DATASET")
    if cod is None:
        return []
    for _, row in df.iterrows():
        campo = row.get(cod, "")
        if pd.isna(campo) or str(campo).strip().upper() in ("#REF!", ""):
            continue
        rows.append(
            {
                "ID_CARGA": ID_CARGA,
                "FUENTE": "F2",
                "DATASET": str(row.get(dataset, "")).strip() if dataset else "",
                "CAMPO": str(campo).strip(),
                "TIPO": str(row.get(tipo, "")).strip() if tipo else "",
                "DESCRIPCION": str(row.get(desc, "")).strip() if desc else "",
                "ORIGEN": "STG_DIC_VARIABLES",
            }
        )
    return rows


def _desde_excel(root: Path) -> list[dict]:
    path = root / EXCEL_CAGR
    if not path.is_file():
        return []
    rows: list[dict] = []
    try:
        for sheet, header in (("DIC_TABLAS", 0), ("DIC_VARIABLES", 0)):
            df = pd.read_excel(path, sheet_name=sheet, header=header, dtype=str)
            if sheet == "DIC_TABLAS":
                rows.extend(_desde_stg_dic_tablas(df))
            else:
                rows.extend(_desde_stg_dic_variables(df))
    except Exception:
        return []
    for r in rows:
        r["ORIGEN"] = f"EXCEL_{r.get('ORIGEN', 'DIC')}"
    return rows


def _desde_catalogo_estatico() -> list[dict]:
    return [
        {
            "ID_CARGA": ID_CARGA,
            "FUENTE": r["fuente"],
            "DATASET": r["dataset"],
            "CAMPO": r["campo"],
            "TIPO": r["tipo"],
            "DESCRIPCION": r["descripcion"],
            "ORIGEN": "CATALOGO_LINEAMIENTOS",
        }
        for r in CATALOGO_CAMPOS
    ]


def _campos_observados_stg(tablas: dict[str, pd.DataFrame]) -> list[dict]:
    from .constantes import STG_FUENTE

    rows = []
    for clave, df in tablas.items():
        if clave not in STG_FUENTE or clave.startswith("DIC_"):
            continue
        fid, tabla, _ = STG_FUENTE[clave]
        for col in df.columns:
            rows.append(
                {
                    "ID_CARGA": ID_CARGA,
                    "FUENTE": fid,
                    "DATASET": tabla,
                    "CAMPO": col,
                    "TIPO": str(df[col].dtype),
                    "DESCRIPCION": "Observado en STG corrida",
                    "ORIGEN": "STG_VIVO",
                }
            )
    return rows


def armar_diccionario(
    tablas: dict[str, pd.DataFrame], root: Path | None = None
) -> pd.DataFrame:
    """Reconstruye diccionario: STG DIC → Excel → catálogo estático + campos STG vivos."""
    filas: list[dict] = []
    filas.extend(_desde_stg_dic_tablas(tablas.get("DIC_TABLAS", pd.DataFrame())))
    filas.extend(_desde_stg_dic_variables(tablas.get("DIC_VARIABLES", pd.DataFrame())))

    if not filas and root is not None:
        filas.extend(_desde_excel(root))

    filas.extend(_desde_catalogo_estatico())
    filas.extend(_campos_observados_stg(tablas))

    if not filas:
        return pd.DataFrame(
            columns=["ID_CARGA", "FUENTE", "DATASET", "CAMPO", "TIPO", "DESCRIPCION", "ORIGEN"]
        )

    dic = pd.DataFrame(filas).drop_duplicates(
        subset=["FUENTE", "DATASET", "CAMPO"], keep="first"
    )
    return dic.sort_values(["FUENTE", "DATASET", "CAMPO"]).reset_index(drop=True)
