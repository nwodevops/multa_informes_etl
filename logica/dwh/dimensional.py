"""Fase 5 — construcción del modelo dimensional en memoria (lineamiento sec. 3)."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime

import pandas as pd

from .catalogos import MI_DIM_ESTADO as SEMILLAS_ESTADO, MI_DIM_PARAMETRO_UIT as UIT_MEF
from .constantes import ID_CARGA
from .homologacion import homologar_estado, vacio

ND = -1
MESES = (
    "ENERO",
    "FEBRERO",
    "MARZO",
    "ABRIL",
    "MAYO",
    "JUNIO",
    "JULIO",
    "AGOSTO",
    "SEPTIEMBRE",
    "OCTUBRE",
    "NOVIEMBRE",
    "DICIEMBRE",
)
DIAS = ("LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO")


def _norm_text(s) -> str:
    if vacio(s):
        return ""
    t = str(s).strip().upper()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t)


def _sigla_expediente(exp) -> str | None:
    if vacio(exp):
        return None
    parts = str(exp).strip().upper().split("-")
    if len(parts) >= 2:
        return "-".join(parts[-2:])
    return str(exp).strip().upper()[:30]


def _infer_tipo_organo(sigla: str) -> str:
    u = sigla.upper()
    if u.startswith("OD"):
        return "OD"
    if u.startswith("ODES"):
        return "ODES"
    if "COORD" in u or "-C" in u:
        return "COORDINACION"
    if u.startswith("D"):
        return "DIRECCION"
    return "NO ESPECIFICADO"


def _dias_entre(a, b) -> int | None:
    if vacio(a) or vacio(b):
        return None
    try:
        ta, tb = pd.Timestamp(a), pd.Timestamp(b)
        return int((ta - tb).days)
    except Exception:
        return None


def _anio_fecha(v) -> int | None:
    if vacio(v):
        return None
    try:
        return int(pd.Timestamp(v).year)
    except Exception:
        return None


def _flag_si(val, esperado: str = "S") -> int:
    """Flag 1/0 sin evaluar pandas.NA como booleano."""
    if vacio(val):
        return 0
    return 1 if str(val).strip().upper() == esperado.upper() else 0


def _build_dim_tiempo() -> pd.DataFrame:
    rows = [
        {
            "ID_TIEMPO": ND,
            "FECHA": pd.NaT,
            "ANIO": None,
            "MES": None,
            "NOMBRE_MES": "NO ESPECIFICADO",
            "TRIMESTRE": None,
            "SEMANA_ANIO": None,
            "DIA": None,
            "DIA_SEMANA": "ND",
            "NOMBRE_DIA": "NO ESPECIFICADO",
            "ES_FIN_DE_SEMANA": 0,
            "ES_FERIADO": 0,
            "ES_DIA_HABIL": 0,
            "DESCRIPCION_FERIADO": None,
        }
    ]
    for y in range(2015, 2027):
        for m in range(1, 13):
            for d in range(1, 32):
                try:
                    dt = date(y, m, d)
                except ValueError:
                    continue
                wd = dt.weekday()
                rows.append(
                    {
                        "ID_TIEMPO": y * 10000 + m * 100 + d,
                        "FECHA": pd.Timestamp(dt),
                        "ANIO": y,
                        "MES": m,
                        "NOMBRE_MES": MESES[m - 1],
                        "TRIMESTRE": (m - 1) // 3 + 1,
                        "SEMANA_ANIO": dt.isocalendar()[1],
                        "DIA": d,
                        "DIA_SEMANA": DIAS[wd],
                        "NOMBRE_DIA": DIAS[wd],
                        "ES_FIN_DE_SEMANA": 1 if wd >= 5 else 0,
                        "ES_FERIADO": 0,
                        "ES_DIA_HABIL": 0 if wd >= 5 else 1,
                        "DESCRIPCION_FERIADO": None,
                    }
                )
    return pd.DataFrame(rows)


def _build_dim_estado(df_multas: pd.DataFrame) -> pd.DataFrame:
    seen: set[tuple[str, str]] = set()
    rows = [
        {
            "ID_ESTADO": ND,
            "TIPO_ESTADO": "NO ESPECIFICADO",
            "CODIGO": "ND",
            "DESCRIPCION": "NO ESPECIFICADO",
            "GRUPO": "NO ESPECIFICADO",
        }
    ]
    for tipo, codigo, desc, grupo in SEMILLAS_ESTADO:
        key = (tipo, codigo)
        if key not in seen:
            seen.add(key)
            rows.append(
                {
                    "ID_ESTADO": len(rows),
                    "TIPO_ESTADO": tipo,
                    "CODIGO": codigo,
                    "DESCRIPCION": desc,
                    "GRUPO": grupo,
                }
            )

    def add_from_col(df, col, tipo_default):
        if col not in df.columns:
            return
        for val in df[col].dropna().unique():
            t, c = homologar_estado(val, tipo_default)
            if not c:
                continue
            key = (t or tipo_default, c)
            if key not in seen:
                seen.add(key)
                rows.append(
                    {
                        "ID_ESTADO": len(rows),
                        "TIPO_ESTADO": key[0],
                        "CODIGO": key[1],
                        "DESCRIPCION": str(val)[:200],
                        "GRUPO": "NO ESPECIFICADO",
                    }
                )

    add_from_col(df_multas, "ESTADO_MC", "MULTA")
    add_from_col(df_multas, "ESTADO_MULTA", "MULTA")
    add_from_col(df_multas, "ESTADO_PAGO_MC", "PAGO")
    add_from_col(df_multas, "ESTADO_RESOLUCION", "RESOLUCION")
    return pd.DataFrame(rows)


def _build_dim_uit() -> pd.DataFrame:
    rows = [{"ID_UIT": ND, "ANIO": 0, "VALOR_UIT": 1.0}]
    for i, (anio, valor) in enumerate(sorted(UIT_MEF.items()), start=1):
        rows.append({"ID_UIT": i, "ANIO": anio, "VALOR_UIT": float(valor)})
    return pd.DataFrame(rows)


def _build_dim_materia() -> pd.DataFrame:
    seeds = [
        "NO ESPECIFICADO",
        "HIDROCARBUROS",
        "PESQUERIA",
        "MINERIA",
        "RESIDUOS SOLIDOS",
        "INDUSTRIAS",
        "AGUAS",
    ]
    seen = set()
    rows = []
    for i, nombre in enumerate(seeds):
        n = _norm_text(nombre)
        if n in seen:
            continue
        seen.add(n)
        rows.append({"ID_MATERIA": ND if i == 0 else len(rows), "NOMBRE": n})
    return pd.DataFrame(rows)


def _build_dim_organo(df_multas: pd.DataFrame) -> pd.DataFrame:
    siglas: set[str] = set()
    if "COORD" in df_multas.columns:
        for v in df_multas["COORD"].dropna():
            s = str(v).strip().upper()
            if s:
                siglas.add(s[:30])
    if "NUMERO_EXPEDIENTE" in df_multas.columns:
        for v in df_multas["NUMERO_EXPEDIENTE"].dropna():
            s = _sigla_expediente(v)
            if s:
                siglas.add(s[:30])
    rows = [
        {
            "ID_ORGANO": ND,
            "SIGLA": "ND",
            "NOMBRE": "NO ESPECIFICADO",
            "TIPO": "NO ESPECIFICADO",
            "ORGANO_SUPERIOR": None,
        }
    ]
    for sigla in sorted(siglas):
        rows.append(
            {
                "ID_ORGANO": len(rows),
                "SIGLA": sigla,
                "NOMBRE": sigla,
                "TIPO": _infer_tipo_organo(sigla),
                "ORGANO_SUPERIOR": None,
            }
        )
    return pd.DataFrame(rows)


def _build_dim_administrado(df_multas: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "ID_ADMINISTRADO": ND,
            "COD_ADMINISTRADO": "ND",
            "RAZON_SOCIAL": "NO ESPECIFICADO",
            "RAZON_SOCIAL_NORM": "NO ESPECIFICADO",
            "RUC": None,
        }
    ]
    seen: set[str] = set()

    def add(cod, razon):
        if not cod or cod in seen:
            return
        seen.add(cod)
        norm = _norm_text(razon) if razon else cod
        rows.append(
            {
                "ID_ADMINISTRADO": len(rows),
                "COD_ADMINISTRADO": cod[:50],
                "RAZON_SOCIAL": str(razon)[:300] if razon else cod,
                "RAZON_SOCIAL_NORM": norm[:300],
                "RUC": None,
            }
        )

    if "ADMINISTRADO" in df_multas.columns:
        for val in df_multas["ADMINISTRADO"].dropna().unique():
            norm = _norm_text(val)[:40]
            if norm:
                add(f"NOM-{norm}", val)
    return pd.DataFrame(rows)


def _lk_estado(dim_estado: pd.DataFrame) -> dict[tuple[str, str], int]:
    return {
        (r.TIPO_ESTADO, r.CODIGO): int(r.ID_ESTADO)
        for r in dim_estado.itertuples(index=False)
    }


def _lk_simple(dim: pd.DataFrame, col_key: str, col_id: str = None) -> dict[str, int]:
    col_id = col_id or f"ID_{col_key.split('_')[0] if col_key != 'SIGLA' else 'ORGANO'}"
    if col_key == "NOMBRE":
        col_id = "ID_MATERIA"
    if col_key == "SIGLA":
        col_id = "ID_ORGANO"
    if col_key == "COD_ADMINISTRADO":
        col_id = "ID_ADMINISTRADO"
    if col_key == "ANIO":
        col_id = "ID_UIT"
    out = {}
    for r in dim.itertuples(index=False):
        k = getattr(r, col_key)
        if k is not None and not (isinstance(k, float) and pd.isna(k)):
            out[str(k).strip().upper() if col_key != "ANIO" else int(k)] = int(getattr(r, col_id))
    return out


def _resolve_estado(lk: dict, val, tipo_default: str) -> int:
    if vacio(val):
        return ND
    t, c = homologar_estado(val, tipo_default)
    if not c:
        return ND
    return lk.get((t or tipo_default, c), ND)


def _build_fact_multas(
    df: pd.DataFrame,
    dim_admin: pd.DataFrame,
    dim_org: pd.DataFrame,
    dim_mat: pd.DataFrame,
    dim_est: pd.DataFrame,
    dim_uit: pd.DataFrame,
) -> pd.DataFrame:
    lk_a = _lk_simple(dim_admin, "COD_ADMINISTRADO")
    lk_o = _lk_simple(dim_org, "SIGLA")
    lk_e = _lk_estado(dim_est)
    id_pagado = lk_e.get(("PAGO", "PAGADO"), ND)
    lk_u = _lk_simple(dim_uit, "ANIO")
    _ = dim_mat

    rows = []
    for _, r in df.iterrows():
        id_mc = len(rows) + 1
        id_admin = ND
        id_mat = ND
        if not vacio(r.get("ADMINISTRADO")):
            norm = _norm_text(r.get("ADMINISTRADO"))[:40]
            id_admin = lk_a.get(f"NOM-{norm}", ND)

        sigla = None
        if not vacio(r.get("COORD")):
            sigla = str(r.get("COORD")).strip().upper()[:30]
        elif not vacio(r.get("NUMERO_EXPEDIENTE")):
            sigla = _sigla_expediente(r.get("NUMERO_EXPEDIENTE"))
        id_org = lk_o.get(sigla, ND) if sigla else ND

        est_mul_val = r.get("ESTADO_MC") if not vacio(r.get("ESTADO_MC")) else r.get("ESTADO_MULTA")
        id_est_res = _resolve_estado(lk_e, r.get("ESTADO_RESOLUCION"), "RESOLUCION")
        id_est_mul = _resolve_estado(lk_e, est_mul_val, "MULTA")
        id_est_pago = _resolve_estado(lk_e, r.get("ESTADO_PAGO_MC"), "PAGO")

        anio = _anio_fecha(r.get("F_FIRMA_RES_MC")) or _anio_fecha(r.get("F_NOTIF_DCG"))
        id_uit = lk_u.get(anio, ND) if anio else ND
        valor_uit = UIT_MEF.get(anio) if anio else None
        muit = r.get("MONTO_UIT")
        monto_s = r.get("MONTO_S")
        monto_calc = None
        if valor_uit and not vacio(muit):
            try:
                monto_calc = float(muit) * float(valor_uit)
            except (TypeError, ValueError):
                pass

        fuente = str(r.get("FUENTE_ORIGEN", "CAGR"))
        if fuente not in ("LAM_OD", "CAGR", "GAPPS", "SISUD_VW"):
            fuente = "CAGR"

        rows.append(
            {
                "ID_MC": id_mc,
                "COD_MA": r.get("COD_MA"),
                "COD_PROY_MC": r.get("COD_PROY_MC"),
                "NUMERO_EXPEDIENTE": r.get("NUMERO_EXPEDIENTE"),
                "EXP_RES_MC": r.get("EXP_RES_MC"),
                "N_RES_MC": r.get("N_RES_MC"),
                "CUM": r.get("CUM"),
                "CAM": r.get("CAM"),
                "NUMERO_REGISTRO_SIGED": r.get("NUMERO_REGISTRO_SIGED"),
                "ID_ADMINISTRADO": id_admin,
                "ID_ORGANO": id_org,
                "ID_MATERIA": id_mat,
                "ID_ESTADO_RESOLUCION": id_est_res,
                "ID_ESTADO_MULTA": id_est_mul,
                "ID_ESTADO_PAGO": id_est_pago,
                "ID_UIT": id_uit,
                "F_NOTIF_DCG": r.get("F_NOTIF_DCG"),
                "F_VENC_DCG": r.get("F_VENC_DCG"),
                "F_RPTA_ADM": r.get("F_RPTA_ADM"),
                "F_INIC_ANALISIS": r.get("F_INIC_ANALISIS"),
                "F_FIN_ANALISIS": r.get("F_FIN_ANALISIS"),
                "F_FIRMA_RES_MC": r.get("F_FIRMA_RES_MC"),
                "F_NOTIF_RES_MC": r.get("F_NOTIF_RES_MC"),
                "F_VENC_MC": r.get("F_VENC_MC"),
                "F_VERIF_POST_MC": r.get("F_VERIF_POST_MC"),
                "F_PAGO": r.get("F_PAGO"),
                "F_REMISION_MEMO": r.get("F_REMISION_MEMO"),
                "PRESENTO_DESCARGOS": r.get("PRESENTO_DESCARGOS"),
                "AMERITA_MC": r.get("AMERITA_MC"),
                "REQUIERE_VERIF_CAMPO": r.get("REQUIERE_VERIF_CAMPO"),
                "MEDIDA_ADMINISTRATIVA": r.get("MEDIDA_ADMINISTRATIVA"),
                "MEMO_EF": r.get("MEMO_EF"),
                "SIGED": r.get("SIGED"),
                "DOC_VERIF_MC": r.get("DOC_VERIF_MC"),
                "MONTO_UIT": muit,
                "VALOR_UIT_APLICADO": valor_uit,
                "MONTO_S": monto_s,
                "MONTO_S_CALC": monto_calc,
                "MONTO_MULTA_REC": r.get("MONTO_MULTA_REC"),
                "MONTO_MULTA_TFA": r.get("MONTO_MULTA_TFA"),
                "DIAS_NOTIF_A_RESPUESTA": _dias_entre(r.get("F_RPTA_ADM"), r.get("F_NOTIF_DCG")),
                "DIAS_ANALISIS": _dias_entre(r.get("F_FIN_ANALISIS"), r.get("F_INIC_ANALISIS")),
                "DIAS_NOTIF_A_FIRMA": _dias_entre(r.get("F_FIRMA_RES_MC"), r.get("F_NOTIF_DCG")),
                "DIAS_FIRMA_A_VENC": _dias_entre(r.get("F_VENC_MC"), r.get("F_FIRMA_RES_MC")),
                "DIAS_VENC_A_PAGO": _dias_entre(r.get("F_PAGO"), r.get("F_VENC_MC")),
                "DIAS_RESOL_A_VERIF": _dias_entre(r.get("F_VERIF_POST_MC"), r.get("F_FIRMA_RES_MC")),
                "FLAG_PRESENTO_DCG": _flag_si(r.get("PRESENTO_DESCARGOS")),
                "FLAG_AMERITA_MC": _flag_si(r.get("AMERITA_MC")),
                "FLAG_PAGADA": 1 if id_est_pago == id_pagado and id_pagado != ND else 0,
                "FLAG_EJECUCION_FORZOSA": 0 if vacio(r.get("MEMO_EF")) else 1,
                "FLAG_CUMPLIO_VERIF": 0 if vacio(r.get("F_VERIF_POST_MC")) else 1,
                "FUENTE_REGISTRO": fuente,
                "FECHA_CARGA": datetime.now(),
            }
        )
    return pd.DataFrame(rows)


def _build_det_etapas(df: pd.DataFrame, fact_mc: pd.DataFrame) -> pd.DataFrame:
    lk_proy = {}
    if len(fact_mc) and "COD_PROY_MC" in fact_mc.columns:
        for r in fact_mc.itertuples(index=False):
            if not vacio(r.COD_PROY_MC):
                lk_proy[str(r.COD_PROY_MC).strip()] = int(r.ID_MC)
    rows = []
    for i, r in df.iterrows():
        cod = str(r.get("COD_PROY_MC")).strip() if not vacio(r.get("COD_PROY_MC")) else ""
        rows.append(
            {
                "ID_ETAPA_MC": len(rows) + 1,
                "ID_MC": lk_proy.get(cod),
                "COD_PROY_MC": r.get("COD_PROY_MC"),
                "NRO_ETAPA": r.get("NRO_ETAPA"),
                "ACCION": r.get("ACCION"),
                "PERFIL_ENCARGADO": r.get("PERFIL_ENCARGADO"),
                "ENCARGADO": r.get("ENCARGADO"),
                "F_ASIGNACION": r.get("F_ASIGNACION"),
                "F_ENTREGA_DEV": r.get("F_ENTREGA_DEV"),
                "ESTADO_ETAPA": r.get("ESTADO_ETAPA"),
                "CONFORMIDAD": r.get("CONFORMIDAD"),
                "DIAS_ELABORACION": r.get("DIAS_ELABORACION"),
                "FUENTE_REGISTRO": "CAGR",
                "FECHA_CARGA": datetime.now(),
            }
        )
    return pd.DataFrame(rows)


def construir_modelo(
    df_multas: pd.DataFrame,
    df_etapas: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Fase 5: arma DIM_*, FACT_MULTA y MI_DET_ETAPA_MC listos para carga Oracle."""
    dim_tiempo = _build_dim_tiempo()
    dim_estado = _build_dim_estado(df_multas)
    dim_uit = _build_dim_uit()
    dim_materia = _build_dim_materia()
    dim_organo = _build_dim_organo(df_multas)
    dim_admin = _build_dim_administrado(df_multas)

    fact_multas = _build_fact_multas(
        df_multas, dim_admin, dim_organo, dim_materia, dim_estado, dim_uit
    )
    det_etapas = _build_det_etapas(df_etapas, fact_multas)

    return {
        "MI_DIM_TIEMPO": dim_tiempo,
        "MI_DIM_ADMINISTRADO": dim_admin,
        "MI_DIM_ORGANO_UNIDAD": dim_organo,
        "MI_DIM_MATERIA_SUBSECTOR": dim_materia,
        "MI_DIM_ESTADO": dim_estado,
        "MI_DIM_PARAMETRO_UIT": dim_uit,
        "MI_FACT_MULTA_COERCITIVA": fact_multas,
        "MI_DET_ETAPA_MC": det_etapas,
    }
