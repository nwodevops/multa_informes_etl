"""Fase 3 — integración F1+F2+F4+F5 (DF_MULTAS) y F3 (DF_INFORMES), F2-ET (DF_ETAPAS)."""

from __future__ import annotations

import pandas as pd

from .constantes import FUENTE_REGISTRO, ID_CARGA
from .homologacion import aplicar_homologacion

# Columnas canónicas pre-FACT_MULTA (ANEXO_MAPEO_CAMPOS.md)
COLS_MULTAS = [
    "ID_CARGA",
    "FUENTE_ORIGEN",
    "COD_MA",
    "COD_PROY_MC",
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

COLS_INFORMES = [
    "ID_CARGA",
    "FUENTE_ORIGEN",
    "IDACTIVIDAD",
    "TXCUC",
    "TXNUMEXP",
    "TXINFORME",
    "TXESTADO",
    "TXTIPSUP",
    "TXFUENTE",
    "TXSUBSECTOR_UND",
    "TXCOORDINACION",
    "IDADMINISTRADO",
    "TXADMINISTRADO",
    "F_INICIO",
    "F_FIN",
    "F_INFORME_ESPERADO",
    "F_INFORME",
    "F_REG_INFORME",
    "TX_DOC_DERIVACION",
    "TXNIVELES_REVISION",
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


def _integrar_gs2(gs2: pd.DataFrame) -> pd.DataFrame:
    h = aplicar_homologacion(gs2, FUENTE_REGISTRO["GS2"])
    m = {
        "FN_MC": "F_NOTIF_DCG",
        "FN_RES_MC": "F_NOTIF_RES_MC",
        "F_REMIS": "F_REMISION_MEMO",
        "PRESENT_DCG_ADM": "PRESENTO_DESCARGOS",
        "AMERIT_MC": "AMERITA_MC",
        "REQ_VERIF_CAMPO": "REQUIERE_VERIF_CAMPO",
        "EXP_INF_INCUMP": "NUMERO_EXPEDIENTE",
    }
    h = _renombrar(h, m)
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
    }
    h = _renombrar(h, m)
    if "COORD" not in h.columns and "COORD" in gs1.columns:
        h["COORD"] = gs1["COORD"].values
    return _a_canonico(h, COLS_MULTAS)


def _integrar_ora(ora: pd.DataFrame) -> pd.DataFrame:
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


def _integrar_mysql(mysql: pd.DataFrame) -> pd.DataFrame:
    h = aplicar_homologacion(mysql, FUENTE_REGISTRO["MYSQL"])
    m = {
        "TX_IDCUM": "CUM",
        "TX_IDCAM": "CAM",
        "NU_MONTOMCUIT": "MONTO_UIT",
        "NU_MONTOMCS": "MONTO_S",
        "FG_ESTADOMULTA": "ESTADO_MULTA",
        "TX_EXP_SIGED_DOC": "NUMERO_REGISTRO_SIGED",
        "FE_F_VERIF_POST_MC": "F_VERIF_POST_MC",
        "TX_DOC_VERIF_MC": "DOC_VERIF_MC",
    }
    h = _renombrar(h, m)
    if "NU_IDINFORMACIONMC" in mysql.columns:
        h["COD_MA"] = mysql["NU_IDINFORMACIONMC"].values
    return _a_canonico(h, COLS_MULTAS)


def _integrar_informes(informes: pd.DataFrame) -> pd.DataFrame:
    h = aplicar_homologacion(informes, FUENTE_REGISTRO["INFORMES"])
    m = {
        "FEINICIO": "F_INICIO",
        "FEFIN": "F_FIN",
        "FEINFORME_ESPERADO": "F_INFORME_ESPERADO",
        "FEINFORME": "F_INFORME",
        "FEREG_INFORME": "F_REG_INFORME",
        "TXNIVELES_REVISION": "TXNIVELES_REVISION",
        "TX_DOC_DERIVACION": "TX_DOC_DERIVACION",
    }
    h = _renombrar(h, m)
    return _a_canonico(h, COLS_INFORMES)


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
    mysql: pd.DataFrame,
    informes: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    partes = [
        _integrar_gs2(gs2),
        _integrar_gs1(gs1),
        _integrar_mysql(mysql),
        _integrar_ora(ora),
    ]
    df_multas = pd.concat(partes, ignore_index=True, sort=False)
    df_informes = _integrar_informes(informes)
    df_etapas = _integrar_etapas(etapas)
    return df_multas, df_informes, df_etapas
