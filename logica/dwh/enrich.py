"""Fact de negocio: vertical F1∪F2, horizontal lookup SISUD (CUM/CAM y afines).

Port fiel de docs/lineamientos/ddl/07_enrich_sheets_sisud.sql.
Sin conexiones: opera sobre DataFrames de evidencia en memoria.
"""

from __future__ import annotations

import pandas as pd

from .homologacion import clave_join_res_monto, vacio


def _serie_clave(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=object)
    return df.apply(
        lambda r: clave_join_res_monto(r.get("N_RES_MC"), r.get("MONTO_UIT")),
        axis=1,
    )


def _tomar_si_vacio(base, extra):
    if vacio(base):
        return extra if not vacio(extra) else None
    return base


def enriquecer_sheets_sisud(
    fact_csep: pd.DataFrame,
    fact_od: pd.DataFrame,
    fact_sisud: pd.DataFrame,
) -> pd.DataFrame:
    """DW_M_FACT_MULTA_COERCITIVA = (CSEP ∪ OD) LEFT JOIN SISUD.

    Filas = F1∪F2. SISUD no agrega filas; pega CUM/CAM/NUMERO_REGISTRO_SIGED
    si el Sheet viene vacío. Empate SISUD: primera fila por CUM, CAM, ID_MC.
    ID_MC 1..N en orden CSEP luego OD (DET CSEP sigue en 1..n_csep).
    """
    sheets = pd.concat([fact_csep, fact_od], ignore_index=True, sort=False)
    if sheets.empty:
        return sheets.copy()

    out = sheets.copy()
    out["ID_MC"] = range(1, len(out) + 1)
    out["_CLAVE"] = _serie_clave(out)

    sis = fact_sisud.copy() if fact_sisud is not None else pd.DataFrame()
    lookup = pd.DataFrame(columns=["_CLAVE", "_S_CUM", "_S_CAM", "_S_SIGED"])
    if not sis.empty:
        sis["_CLAVE"] = _serie_clave(sis)
        sis = sis[sis["_CLAVE"].notna()].copy()
        if not sis.empty:
            sis = sis.sort_values(
                by=["_CLAVE", "CUM", "CAM", "ID_MC"],
                na_position="last",
                kind="mergesort",
            )
            sis = sis.drop_duplicates(subset=["_CLAVE"], keep="first")
            lookup = sis[["_CLAVE", "CUM", "CAM", "NUMERO_REGISTRO_SIGED"]].rename(
                columns={
                    "CUM": "_S_CUM",
                    "CAM": "_S_CAM",
                    "NUMERO_REGISTRO_SIGED": "_S_SIGED",
                }
            )

    out = out.merge(lookup, on="_CLAVE", how="left")
    out["CUM"] = [_tomar_si_vacio(a, b) for a, b in zip(out["CUM"], out["_S_CUM"])]
    out["CAM"] = [_tomar_si_vacio(a, b) for a, b in zip(out["CAM"], out["_S_CAM"])]
    out["NUMERO_REGISTRO_SIGED"] = [
        _tomar_si_vacio(a, b)
        for a, b in zip(out["NUMERO_REGISTRO_SIGED"], out["_S_SIGED"])
    ]
    return out.drop(columns=["_CLAVE", "_S_CUM", "_S_CAM", "_S_SIGED"], errors="ignore")
