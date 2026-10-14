"""Fact de negocio: vertical F1∪F2, horizontal lookup SISUD (CUM/CAM y afines).

Port fiel de docs/lineamientos/ddl/07_enrich_sheets_sisud.sql.
Sin conexiones: opera sobre DataFrames de evidencia en memoria.
"""

from __future__ import annotations

import pandas as pd

from .homologacion import clave_join_res_monto, vacio

ND = -1

_COLS_SISUD = (
    "CUM",
    "CAM",
    "NUMERO_REGISTRO_SIGED",
    "ID_ESTADO_RESOLUCION",
    "MEDIDA_ADMINISTRATIVA",
    "MONTO_MULTA_REC",
    "MONTO_MULTA_TFA",
    "ID_ADMINISTRADO",
)

# Sombra: valores SISUD con otro nombre para no pisar N_RES_MC / MONTO_UIT del Sheet.
_SOMBRA_SISUD = (
    ("N_RES_MC", "N_RES_SISUD"),
    ("MONTO_UIT", "MONTO_UIT_SISUD"),
)


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


def _es_nd(val) -> bool:
    """True si no hay FK usable (nulo o surrogate -1). vacio(-1) es False."""
    if vacio(val):
        return True
    try:
        return int(val) == ND
    except (TypeError, ValueError):
        return False


def _tomar_si_nd(base, extra):
    """Como _tomar_si_vacio, pero -1 de planilla no bloquea el pegote SISUD."""
    if _es_nd(base):
        if _es_nd(extra):
            return ND
        return extra
    return base


def enriquecer_sheets_sisud(
    fact_csep: pd.DataFrame,
    fact_od: pd.DataFrame,
    fact_sisud: pd.DataFrame,
    fact_gapps: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """DW_M_FACT_MULTA_COERCITIVA = (CSEP ∪ OD) LEFT JOIN SISUD ∪ GAPPS.

    Filas planilla = F1∪F2. SISUD no agrega filas; pega CUM/CAM/NUMERO_REGISTRO_SIGED
    y, si hay match, ID_ESTADO_RESOLUCION / MEDIDA_ADMINISTRATIVA / montos REC/TFA
    cuando la planilla los trae vacíos (o ID = -1). ID_ADMINISTRADO se rellena
    igual si la planilla quedó ND (típico OD sin ADM).
    N_RES_SISUD / MONTO_UIT_SISUD son sombra: no pisan el Sheet.
    GAPPS se concatena al final, sin lookup SISUD (CUM/CAM de la app).
    Empate SISUD: primera fila por CUM, CAM, ID_MC.
    ID_MC 1..N en orden CSEP, OD, GAPPS (DET CSEP sigue en 1..n_csep).
    """
    sheets = pd.concat([fact_csep, fact_od], ignore_index=True, sort=False)
    sombra_dest = [dest for _, dest in _SOMBRA_SISUD]
    lookup_cols = ["_CLAVE"] + [f"_S_{c}" for c in _COLS_SISUD] + [
        f"_S_{c}" for c in sombra_dest
    ]

    if sheets.empty:
        out = sheets.copy()
    else:
        out = sheets.copy()
        out["ID_MC"] = range(1, len(out) + 1)
        out["_CLAVE"] = _serie_clave(out)

        sis = fact_sisud.copy() if fact_sisud is not None else pd.DataFrame()
        lookup = pd.DataFrame(columns=lookup_cols)
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
                for c in _COLS_SISUD:
                    if c not in sis.columns:
                        sis[c] = pd.NA
                for src, dest in _SOMBRA_SISUD:
                    sis[dest] = sis[src] if src in sis.columns else pd.NA
                lookup = sis[["_CLAVE", *_COLS_SISUD, *sombra_dest]].rename(
                    columns={c: f"_S_{c}" for c in (*_COLS_SISUD, *sombra_dest)}
                )

        out = out.merge(lookup, on="_CLAVE", how="left")
        out["CUM"] = [_tomar_si_vacio(a, b) for a, b in zip(out["CUM"], out["_S_CUM"])]
        out["CAM"] = [_tomar_si_vacio(a, b) for a, b in zip(out["CAM"], out["_S_CAM"])]
        out["NUMERO_REGISTRO_SIGED"] = [
            _tomar_si_vacio(a, b)
            for a, b in zip(out["NUMERO_REGISTRO_SIGED"], out["_S_NUMERO_REGISTRO_SIGED"])
        ]
        out["ID_ESTADO_RESOLUCION"] = [
            _tomar_si_nd(a, b)
            for a, b in zip(out["ID_ESTADO_RESOLUCION"], out["_S_ID_ESTADO_RESOLUCION"])
        ]
        out["ID_ADMINISTRADO"] = [
            _tomar_si_nd(a, b)
            for a, b in zip(out["ID_ADMINISTRADO"], out["_S_ID_ADMINISTRADO"])
        ]
        out["MEDIDA_ADMINISTRATIVA"] = [
            _tomar_si_vacio(a, b)
            for a, b in zip(out["MEDIDA_ADMINISTRATIVA"], out["_S_MEDIDA_ADMINISTRATIVA"])
        ]
        out["MONTO_MULTA_REC"] = [
            _tomar_si_vacio(a, b)
            for a, b in zip(out["MONTO_MULTA_REC"], out["_S_MONTO_MULTA_REC"])
        ]
        out["MONTO_MULTA_TFA"] = [
            _tomar_si_vacio(a, b)
            for a, b in zip(out["MONTO_MULTA_TFA"], out["_S_MONTO_MULTA_TFA"])
        ]
        out["N_RES_SISUD"] = out["_S_N_RES_SISUD"] if "_S_N_RES_SISUD" in out.columns else None
        out["MONTO_UIT_SISUD"] = (
            out["_S_MONTO_UIT_SISUD"] if "_S_MONTO_UIT_SISUD" in out.columns else None
        )
        out = out.drop(columns=["_CLAVE", *lookup_cols[1:]], errors="ignore")

    gapps = fact_gapps.copy() if fact_gapps is not None and not fact_gapps.empty else pd.DataFrame()
    if not gapps.empty:
        for c in ("N_RES_SISUD", "MONTO_UIT_SISUD"):
            if c not in gapps.columns:
                gapps[c] = None
        out = pd.concat([out, gapps], ignore_index=True, sort=False)
    if not out.empty:
        out = out.copy()
        out["ID_MC"] = range(1, len(out) + 1)
    return out
