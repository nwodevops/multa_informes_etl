"""Fase 3 — integración por universo: F2 CSEP, F1 OD, F5 SISUD + etapas.

Tres dataframes de evidencia (sin merge enriquecido). el hecho enriquecido se arma en Oracle SQL
después de cargar MI_FACT_MC_CSEP / _OD / _SISUD.
"""

from __future__ import annotations

import pandas as pd

from .constantes import F1_OD_LECTURAS, FUENTE_REGISTRO, ID_CARGA
from .homologacion import aplicar_homologacion

COLS_MULTAS = [
    "ID_CARGA",
    "FUENTE_ORIGEN",
    "COD_OD",
    "COD_MA",
    "COD_PROY_MC",
    "JEFE",
    "UF",
    "N_PROY_MC",
    "ETA_REG_PROY_MC",
    "ETA_REG_MC",
    "RESULT_PROY_MC",
    "NUMERO_EXPEDIENTE",
    "EXP_RES_MC",
    "N_RES_MC",
    "CUM",
    "CAM",
    "NUMERO_REGISTRO_SIGED",
    "F_NOTIF_DCG",
    "F_VENC_DCG",
    "F_RPTA_ADM",
    "F_INIC_ANALISIS",
    "F_FIN_ANALISIS",
    "F_FIRMA_RES_MC",
    "F_NOTIF_RES_MC",
    "F_VENC_MC",
    "F_VERIF_POST_MC",
    "F_PAGO",
    "F_REMISION_MEMO",
    "PRESENTO_DESCARGOS",
    "AMERITA_MC",
    "REQUIERE_VERIF_CAMPO",
    "MEDIDA_ADMINISTRATIVA",
    "MEMO_EF",
    "SIGED",
    "DOC_VERIF_MC",
    "MONTO_UIT",
    "MONTO_S",
    "MONTO_MULTA_REC",
    "MONTO_MULTA_TFA",
    "ESTADO_MC",
    "ESTADO_PAGO_MC",
    "ESTADO_RESOLUCION",
    "ESTADO_MULTA",
    "COORD",
    "ADMINISTRADO",
]

COLS_ETAPAS = [
    "ID_CARGA",
    "FUENTE_ORIGEN",
    "COD_PROY_MC",
    "NRO_ETAPA",
    "ACCION",
    "PERFIL_ENCARGADO",
    "ENCARGADO",
    "F_ASIGNACION",
    "F_ENTREGA_DEV",
    "ESTADO_ETAPA",
    "CONFORMIDAD",
    "DIAS_ELABORACION",
]


def _renombrar(df: pd.DataFrame, mapeo: dict[str, str]) -> pd.DataFrame:
    exist = {k: v for k, v in mapeo.items() if k in df.columns}
    return df.rename(columns=exist)


def _a_canonico(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    out.insert(0, "ID_CARGA", ID_CARGA)
    for c in cols:
        if c not in out.columns:
            out[c] = pd.NA
    return out[cols]


def _integrar_gs2(gs2: pd.DataFrame, cod_od: str | None = None) -> pd.DataFrame:
    h = aplicar_homologacion(gs2, FUENTE_REGISTRO["GS2"])
    m = {
        "FN_MC": "F_NOTIF_DCG",
        "FN_RES_MC": "F_NOTIF_RES_MC",
        "F_REMIS": "F_REMISION_MEMO",
        "PRESENT_DCG_ADM": "PRESENTO_DESCARGOS",
        "AMERIT_MC": "AMERITA_MC",
        "REQ_VERIF_CAMPO": "REQUIERE_VERIF_CAMPO",
        "EXP_INF_INCUMP": "NUMERO_EXPEDIENTE",
        "MULTA_UIT": "MONTO_UIT",
        "MULTA_S": "MONTO_S",
    }
    h = _renombrar(h, m)
    if cod_od:
        h["COD_OD"] = cod_od
    elif "COD_OD" in gs2.columns:
        h["COD_OD"] = gs2["COD_OD"].values
    elif "COD_OD" not in h.columns:
        h["COD_OD"] = pd.NA
    h["FUENTE_ORIGEN"] = FUENTE_REGISTRO["GS2"]
    return _a_canonico(h, COLS_MULTAS)


def _integrar_gs1(gs1: pd.DataFrame) -> pd.DataFrame:
    h = aplicar_homologacion(gs1, FUENTE_REGISTRO["GS1"])
    m = {
        "FN_MC": "F_NOTIF_DCG",
        "FN_RES_MC": "F_NOTIF_RES_MC",
        "F_REMIS": "F_REMISION_MEMO",
        "PRESENT_DCG_ADM": "PRESENTO_DESCARGOS",
        "AMERIT_MC": "AMERITA_MC",
        "REQ_VERIF_CAMPO": "REQUIERE_VERIF_CAMPO",
        "EXP_INF_INCUMP": "NUMERO_EXPEDIENTE",
        "ADM": "ADMINISTRADO",
        "MULTA_UIT": "MONTO_UIT",
        "MULTA_S": "MONTO_S",
    }
    h = _renombrar(h, m)
    if "COORD" in gs1.columns:
        h["COORD"] = gs1["COORD"].values
    if "COD_UNIDAD" in gs1.columns:
        coord = h["COORD"] if "COORD" in h.columns else pd.Series(pd.NA, index=h.index)
        empty = coord.isna() | (coord.astype("string").str.strip() == "")
        h["COORD"] = coord.where(~empty, gs1["COD_UNIDAD"].astype("string").values)
    return _a_canonico(h, COLS_MULTAS)


def _integrar_ora(ora: pd.DataFrame) -> pd.DataFrame:
    if ora is None or ora.empty:
        return _a_canonico(pd.DataFrame(), COLS_MULTAS)
    h = aplicar_homologacion(ora, FUENTE_REGISTRO["ORA"])
    m = {
        "RESOLUCION": "N_RES_MC",
        "MONTO_MULTA": "MONTO_UIT",
        "NUMERO_REGISTRO": "NUMERO_REGISTRO_SIGED",
        "FECHA_EMISION": "F_FIRMA_RES_MC",
        "ADMINISTRADO": "ADMINISTRADO",
    }
    h = _renombrar(h, m)
    return _a_canonico(h, COLS_MULTAS)


def _integrar_etapas(etapas: pd.DataFrame) -> pd.DataFrame:
    h = aplicar_homologacion(etapas, FUENTE_REGISTRO["ETAPAS"])
    m = {
        "NRO_ETAPA_MC": "NRO_ETAPA",
        "ACCION_MC": "ACCION",
        "PERF_ENCARG_MC": "PERFIL_ENCARGADO",
        "ENCARGADO_MC": "ENCARGADO",
        "F_ASIG_MC": "F_ASIGNACION",
        "F_ENT_DEV_MC": "F_ENTREGA_DEV",
        "EST_ETAPA_MC": "ESTADO_ETAPA",
        "CONFORMIDAD_MC": "CONFORMIDAD",
        "T_ELAB_MC": "DIAS_ELABORACION",
    }
    h = _renombrar(h, m)
    return _a_canonico(h, COLS_ETAPAS)


def integrar(
    gs1: pd.DataFrame,
    gs2: pd.DataFrame,
    etapas: pd.DataFrame,
    ora: pd.DataFrame,
    gs2_ods: dict[str, pd.DataFrame] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Devuelve (df_csep, df_od, df_sisud, df_etapas). Sin enrich Sheets←SISUD."""
    df_csep = _integrar_gs1(gs1)

    partes_od = [_integrar_gs2(gs2, None)]
    for clave, df in (gs2_ods or {}).items():
        if df is None or df.empty:
            continue
        cod = F1_OD_LECTURAS.get(clave)
        if cod == "*":
            cod = None
        partes_od.append(_integrar_gs2(df, cod))
    df_od = pd.concat(partes_od, ignore_index=True, sort=False)

    df_sisud = _integrar_ora(ora)
    df_etapas = _integrar_etapas(etapas)
    return df_csep, df_od, df_sisud, df_etapas
