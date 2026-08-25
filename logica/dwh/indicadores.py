"""Fase 7 — indicadores K1–K5 sobre el modelo dimensional (lineamiento sec. 5)."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from .calidad import REGLAS
from .constantes import ID_CARGA
from .homologacion import vacio

ND = -1

NOMBRES = {
    "K1": "Cobertura",
    "K2": "Oportunidad del ciclo de multa",
    "K3": "Efectividad de cobranza",
    "K4": "Tasa de verificación post-multa",
    "K5": "Calidad del dato",
}

COLS = [
    "ID_CARGA",
    "FECHA_CARGA",
    "COD_INDICADOR",
    "NOMBRE_INDICADOR",
    "ANIO",
    "ID_ORGANO",
    "ID_MATERIA",
    "METRICA",
    "SUBGRANO",
    "NUMERADOR",
    "DENOMINADOR",
    "VALOR",
    "UNIDAD",
]


def _anio_fecha(v) -> int | None:
    if vacio(v):
        return None
    try:
        return int(pd.Timestamp(v).year)
    except Exception:
        return None


def _fila(
    cod: str,
    metrica: str,
    *,
    anio: int | None = None,
    id_organo: int = ND,
    id_materia: int = ND,
    subgrano: str | None = None,
    numerador: float | None = None,
    denominador: float | None = None,
    valor: float | None = None,
    unidad: str | None = None,
) -> dict:
    return {
        "ID_CARGA": ID_CARGA,
        "FECHA_CARGA": datetime.now(),
        "COD_INDICADOR": cod,
        "NOMBRE_INDICADOR": NOMBRES[cod],
        "ANIO": anio,
        "ID_ORGANO": id_organo,
        "ID_MATERIA": id_materia,
        "METRICA": metrica,
        "SUBGRANO": subgrano,
        "NUMERADOR": numerador,
        "DENOMINADOR": denominador,
        "VALOR": valor,
        "UNIDAD": unidad,
    }


def _ratio(num: float, den: float) -> float | None:
    if den is None or den == 0:
        return None
    return round(float(num) / float(den), 4)


def _prep_multas(fact_mc: pd.DataFrame) -> pd.DataFrame:
    if fact_mc.empty:
        return fact_mc.copy()
    df = fact_mc.copy()
    anios = []
    for _, r in df.iterrows():
        anios.append(_anio_fecha(r.get("F_FIRMA_RES_MC")) or _anio_fecha(r.get("F_NOTIF_DCG")))
    df["_ANIO"] = anios
    df["_ORG"] = df["ID_ORGANO"].apply(lambda x: int(x) if not vacio(x) else ND)
    return df


def _prep_informes(fact_inf: pd.DataFrame) -> pd.DataFrame:
    if fact_inf.empty:
        return fact_inf.copy()
    df = fact_inf.copy()
    anios = []
    for _, r in df.iterrows():
        anios.append(_anio_fecha(r.get("F_INFORME")) or _anio_fecha(r.get("F_FIN")))
    df["_ANIO"] = anios
    df["_ORG"] = df["ID_ORGANO"].apply(lambda x: int(x) if not vacio(x) else ND)
    return df


def _k1_cobertura(fact_mc: pd.DataFrame, fact_inf: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    mc = _prep_multas(fact_mc)
    inf = _prep_informes(fact_inf)

    if len(mc):
        g = mc.groupby(["_ANIO", "_ORG"], dropna=False).size()
        for (anio, org), n in g.items():
            rows.append(
                _fila(
                    "K1",
                    "N_MULTAS",
                    anio=int(anio) if not pd.isna(anio) else None,
                    id_organo=int(org),
                    numerador=float(n),
                    denominador=float(n),
                    valor=float(n),
                    unidad="REGISTROS",
                )
            )
        rows.append(
            _fila(
                "K1",
                "N_MULTAS",
                anio=None,
                id_organo=ND,
                subgrano="TOTAL",
                numerador=float(len(mc)),
                denominador=float(len(mc)),
                valor=float(len(mc)),
                unidad="REGISTROS",
            )
        )

    if len(inf):
        g = inf.groupby(["_ANIO", "_ORG"], dropna=False).size()
        for (anio, org), n in g.items():
            rows.append(
                _fila(
                    "K1",
                    "N_INFORMES",
                    anio=int(anio) if not pd.isna(anio) else None,
                    id_organo=int(org),
                    numerador=float(n),
                    denominador=float(n),
                    valor=float(n),
                    unidad="REGISTROS",
                )
            )
        rows.append(
            _fila(
                "K1",
                "N_INFORMES",
                anio=None,
                id_organo=ND,
                subgrano="TOTAL",
                numerador=float(len(inf)),
                denominador=float(len(inf)),
                valor=float(len(inf)),
                unidad="REGISTROS",
            )
        )
    return rows


def _k2_oportunidad(fact_mc: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    mc = _prep_multas(fact_mc)
    if mc.empty or "DIAS_NOTIF_A_FIRMA" not in mc.columns:
        return rows
    valid = mc[mc["DIAS_NOTIF_A_FIRMA"].notna()].copy()
    if valid.empty:
        return rows
    g = valid.groupby(["_ANIO", "_ORG"], dropna=False)["DIAS_NOTIF_A_FIRMA"]
    for (anio, org), s in g:
        n = len(s)
        total_d = float(s.sum())
        rows.append(
            _fila(
                "K2",
                "PROM_DIAS_NOTIF_FIRMA",
                anio=int(anio) if not pd.isna(anio) else None,
                id_organo=int(org),
                numerador=total_d,
                denominador=float(n),
                valor=round(total_d / n, 4) if n else None,
                unidad="DIAS",
            )
        )
    n_all = len(valid)
    total_all = float(valid["DIAS_NOTIF_A_FIRMA"].sum())
    rows.append(
        _fila(
            "K2",
            "PROM_DIAS_NOTIF_FIRMA",
            anio=None,
            id_organo=ND,
            subgrano="TOTAL",
            numerador=total_all,
            denominador=float(n_all),
            valor=round(total_all / n_all, 4) if n_all else None,
            unidad="DIAS",
        )
    )
    return rows


def _k3_cobranza(fact_mc: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    mc = _prep_multas(fact_mc)
    if mc.empty:
        return rows

    imp_all = mc[mc["F_FIRMA_RES_MC"].apply(lambda x: not vacio(x))]
    for (anio, org), sub in imp_all.groupby(["_ANIO", "_ORG"], dropna=False):
        pag = sub[sub["FLAG_PAGADA"] == 1] if "FLAG_PAGADA" in sub.columns else sub.iloc[0:0]
        den_s = float(sub["MONTO_S"].fillna(0).sum()) if "MONTO_S" in sub.columns else float(len(sub))
        num_s = float(pag["MONTO_S"].fillna(0).sum()) if "MONTO_S" in pag.columns else 0.0
        rows.append(
            _fila(
                "K3",
                "RATIO_COBRANZA_SOLES",
                anio=int(anio) if not pd.isna(anio) else None,
                id_organo=int(org),
                subgrano="SOLES",
                numerador=num_s,
                denominador=den_s,
                valor=_ratio(num_s, den_s),
                unidad="SOLES",
            )
        )
        den_u = float(sub["MONTO_UIT"].fillna(0).sum()) if "MONTO_UIT" in sub.columns else float(len(sub))
        num_u = float(pag["MONTO_UIT"].fillna(0).sum()) if "MONTO_UIT" in pag.columns else 0.0
        rows.append(
            _fila(
                "K3",
                "RATIO_COBRANZA_UIT",
                anio=int(anio) if not pd.isna(anio) else None,
                id_organo=int(org),
                subgrano="UIT",
                numerador=num_u,
                denominador=den_u,
                valor=_ratio(num_u, den_u),
                unidad="UIT",
            )
        )

    if len(imp_all):
        pag_all = imp_all[imp_all["FLAG_PAGADA"] == 1] if "FLAG_PAGADA" in imp_all.columns else imp_all.iloc[0:0]
        den_s = float(imp_all["MONTO_S"].fillna(0).sum()) if "MONTO_S" in imp_all.columns else float(len(imp_all))
        num_s = float(pag_all["MONTO_S"].fillna(0).sum()) if "MONTO_S" in pag_all.columns else 0.0
        rows.append(
            _fila(
                "K3",
                "RATIO_COBRANZA_SOLES",
                anio=None,
                id_organo=ND,
                subgrano="TOTAL",
                numerador=num_s,
                denominador=den_s,
                valor=_ratio(num_s, den_s),
                unidad="SOLES",
            )
        )
        den_u = float(imp_all["MONTO_UIT"].fillna(0).sum()) if "MONTO_UIT" in imp_all.columns else float(len(imp_all))
        num_u = float(pag_all["MONTO_UIT"].fillna(0).sum()) if "MONTO_UIT" in pag_all.columns else 0.0
        rows.append(
            _fila(
                "K3",
                "RATIO_COBRANZA_UIT",
                anio=None,
                id_organo=ND,
                subgrano="TOTAL",
                numerador=num_u,
                denominador=den_u,
                valor=_ratio(num_u, den_u),
                unidad="UIT",
            )
        )
    return rows


def _k4_verificacion(fact_mc: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    mc = _prep_multas(fact_mc)
    if mc.empty:
        return rows
    res = mc[mc["F_FIRMA_RES_MC"].apply(lambda x: not vacio(x))]
    if res.empty:
        return rows
    for (anio, org), sub in res.groupby(["_ANIO", "_ORG"], dropna=False):
        den = float(len(sub))
        num = float((sub["FLAG_CUMPLIO_VERIF"] == 1).sum()) if "FLAG_CUMPLIO_VERIF" in sub.columns else 0.0
        rows.append(
            _fila(
                "K4",
                "TASA_VERIF_POST_MC",
                anio=int(anio) if not pd.isna(anio) else None,
                id_organo=int(org),
                numerador=num,
                denominador=den,
                valor=_ratio(num, den),
                unidad="PORCENTAJE",
            )
        )
    den_all = float(len(res))
    num_all = float((res["FLAG_CUMPLIO_VERIF"] == 1).sum()) if "FLAG_CUMPLIO_VERIF" in res.columns else 0.0
    rows.append(
        _fila(
            "K4",
            "TASA_VERIF_POST_MC",
            anio=None,
            id_organo=ND,
            subgrano="TOTAL",
            numerador=num_all,
            denominador=den_all,
            valor=_ratio(num_all, den_all),
            unidad="PORCENTAJE",
        )
    )
    return rows


def _k5_calidad(
    df_multas: pd.DataFrame,
    df_informes: pd.DataFrame,
    dq_hallazgo: pd.DataFrame,
    qa_amarre: pd.DataFrame,
) -> list[dict]:
    rows: list[dict] = []
    tablas = {
        "MULTAS": ("FACT_MULTA_COERCITIVA", df_multas),
        "INFORMES": ("FACT_INFORME_SUPERVISION", df_informes),
    }

    for etiqueta, (tabla, df) in tablas.items():
        total = len(df)
        if total == 0:
            continue
        if "FG_CONFORME" in df.columns:
            n_conf = int((df["FG_CONFORME"] == "S").sum())
            rows.append(
                _fila(
                    "K5",
                    "PCT_CONFORME",
                    subgrano=f"GLOBAL_{etiqueta}",
                    numerador=float(n_conf),
                    denominador=float(total),
                    valor=round(100.0 * n_conf / total, 4),
                    unidad="PORCENTAJE",
                )
            )
        for regla in REGLAS:
            n_afect = 0
            if len(dq_hallazgo) and "REGLA_CODIGO" in dq_hallazgo.columns and "TABLA_DESTINO" in dq_hallazgo.columns:
                mask = (dq_hallazgo["REGLA_CODIGO"] == regla) & (dq_hallazgo["TABLA_DESTINO"] == tabla)
                n_afect = int(dq_hallazgo.loc[mask, "REGISTRO_ID"].nunique()) if mask.any() else 0
            n_ok = max(total - n_afect, 0)
            rows.append(
                _fila(
                    "K5",
                    "PCT_CONFORME",
                    subgrano=f"{regla}_{etiqueta}",
                    numerador=float(n_ok),
                    denominador=float(total),
                    valor=round(100.0 * n_ok / total, 4),
                    unidad="PORCENTAJE",
                )
            )

    if len(qa_amarre):
        for _, r in qa_amarre.iterrows():
            puente = str(r.get("PUENTE", ""))
            n_match = float(r.get("N_MATCH", 0) or 0)
            n_izq = float(r.get("N_IZQ", 0) or 0)
            pct = r.get("PCT_MATCH_IZQ")
            valor = float(pct) if not vacio(pct) else _ratio(n_match, n_izq)
            rows.append(
                _fila(
                    "K5",
                    "PCT_AMARRE",
                    subgrano=puente,
                    numerador=n_match,
                    denominador=n_izq,
                    valor=valor,
                    unidad="PORCENTAJE",
                )
            )
    return rows


def _verificar_invariantes(rows: list[dict], fact_mc: pd.DataFrame, fact_inf: pd.DataFrame) -> None:
    n_mc = len(fact_mc)
    n_inf = len(fact_inf)
    sum_mc = sum(
        r["VALOR"] or 0
        for r in rows
        if r["COD_INDICADOR"] == "K1" and r["METRICA"] == "N_MULTAS" and r.get("SUBGRANO") != "TOTAL"
    )
    sum_inf = sum(
        r["VALOR"] or 0
        for r in rows
        if r["COD_INDICADOR"] == "K1" and r["METRICA"] == "N_INFORMES" and r.get("SUBGRANO") != "TOTAL"
    )
    if n_mc and abs(sum_mc - n_mc) > 0.01:
        print(f"AVISO K1: sum(N_MULTAS)={sum_mc} vs fact={n_mc}")
    if n_inf and abs(sum_inf - n_inf) > 0.01:
        print(f"AVISO K1: sum(N_INFORMES)={sum_inf} vs fact={n_inf}")


def calcular_indicadores(
    fact_mc: pd.DataFrame,
    fact_inf: pd.DataFrame,
    df_multas: pd.DataFrame,
    df_informes: pd.DataFrame,
    dq_hallazgo: pd.DataFrame,
    qa_amarre: pd.DataFrame,
    dim_org: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Calcula K1–K5 en memoria listos para INDICADOR_RESULTADO."""
    _ = dim_org
    rows: list[dict] = []
    rows.extend(_k1_cobertura(fact_mc, fact_inf))
    rows.extend(_k2_oportunidad(fact_mc))
    rows.extend(_k3_cobranza(fact_mc))
    rows.extend(_k4_verificacion(fact_mc))
    rows.extend(
        _k5_calidad(
            df_multas if df_multas is not None else pd.DataFrame(),
            df_informes if df_informes is not None else pd.DataFrame(),
            dq_hallazgo if dq_hallazgo is not None else pd.DataFrame(),
            qa_amarre if qa_amarre is not None else pd.DataFrame(),
        )
    )
    _verificar_invariantes(rows, fact_mc, fact_inf)
    if not rows:
        return pd.DataFrame(columns=COLS)
    return pd.DataFrame(rows, columns=COLS)
