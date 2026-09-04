"""Fase 4 — reglas R01–R05 y bitácora MI_DQ_HALLAZGO (lineamiento sec. 4)."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from .catalogos import MI_DIM_PARAMETRO_UIT
from .constantes import ID_CARGA
from .homologacion import vacio

REGLAS = {
    "R01": "Completitud de campos clave (COD_MA, expediente, CUM/CAM)",
    "R02": "Formato válido de CUM/CAM",
    "R03": "Coherencia temporal (vencimiento >= notificación)",
    "R04": "Montos UIT >= 0",
    "R05": "Coherencia UIT↔soles (MONTO_S vs MULTA_UIT × UIT)",
}

MAX_HALLAZGOS = 5000


def _hallazgo(
    regla: str,
    fuente: str,
    tabla: str,
    registro_id: str,
    campo: str,
    valor,
    severidad: str = "CRITICA",
    obs: str = "",
) -> dict:
    return {
        "ID_CARGA": ID_CARGA,
        "FECHA_CARGA": datetime.now(),
        "REGLA_CODIGO": regla,
        "REGLA_DESCRIPCION": REGLAS[regla],
        "FUENTE_ORIGEN": fuente,
        "TABLA_DESTINO": tabla,
        "REGISTRO_ID": str(registro_id)[:200] if registro_id else "",
        "CAMPO": campo,
        "VALOR_ENCONTRADO": str(valor)[:500] if valor is not None and not pd.isna(valor) else "",
        "SEVERIDAD": severidad,
        "ESTADO": "PENDIENTE",
        "OBSERVACION": obs[:500],
        "FECHA_RESOLUCION": pd.NaT,
        "RESUELTO_POR": "",
    }


def _registro_id(row: pd.Series) -> str:
    if not vacio(row.get("COD_MA")):
        return str(row.get("COD_MA"))
    cum = row.get("CUM")
    cam = row.get("CAM")
    if not vacio(cum) or not vacio(cam):
        return f"{cum or ''}|{cam or ''}"
    if not vacio(row.get("NUMERO_EXPEDIENTE")):
        return str(row.get("NUMERO_EXPEDIENTE"))
    if not vacio(row.get("IDACTIVIDAD")):
        return str(row.get("IDACTIVIDAD"))
    return ""


def _anio_fecha(v) -> int | None:
    if vacio(v):
        return None
    try:
        return int(pd.Timestamp(v).year)
    except Exception:
        return None


def _uit_anio(anio: int | None) -> float | None:
    if anio is None:
        return None
    return MI_DIM_PARAMETRO_UIT.get(anio)


def _validar_multas(df: pd.DataFrame) -> tuple[pd.Series, list[dict]]:
    n = len(df)
    conforme = pd.Series([True] * n, index=df.index)
    hallazgos: list[dict] = []

    def add(regla, i, row, campo, valor, sev="CRITICA", obs=""):
        nonlocal hallazgos
        if len(hallazgos) >= MAX_HALLAZGOS:
            return
        conforme.at[i] = False
        hallazgos.append(
            _hallazgo(
                regla,
                str(row.get("FUENTE_ORIGEN", "")),
                "MI_FACT_MULTA_COERCITIVA",
                _registro_id(row),
                campo,
                valor,
                sev,
                obs,
            )
        )

    for i, row in df.iterrows():
        fuente = str(row.get("FUENTE_ORIGEN", ""))
        rid = _registro_id(row)

        if fuente in ("LAM_OD", "CAGR"):
            if vacio(row.get("COD_MA")):
                add("R01", i, row, "COD_MA", row.get("COD_MA"))
        elif fuente in ("GAPPS", "SISUD_VW"):
            if vacio(row.get("CUM")) and vacio(row.get("CAM")):
                add("R01", i, row, "CUM/CAM", "")
        if vacio(rid):
            add("R01", i, row, "REGISTRO_ID", "", obs="sin clave natural")

        cum = row.get("CUM")
        if not vacio(cum):
            s = str(cum)
            if not s.isdigit() or len(s) != 11:
                add("R02", i, row, "CUM", cum, "ADVERTENCIA")
        cam = row.get("CAM")
        if not vacio(cam):
            s = str(cam)
            if not s.isdigit() or len(s) not in (11, 13):
                add("R02", i, row, "CAM", cam, "ADVERTENCIA")

        for fin, inicio in [("F_VENC_DCG", "F_NOTIF_DCG"), ("F_VENC_MC", "F_FIRMA_RES_MC")]:
            a, b = row.get(fin), row.get(inicio)
            if vacio(a) or vacio(b):
                continue
            try:
                if pd.Timestamp(a) < pd.Timestamp(b):
                    add("R03", i, row, fin, a, obs=f"{fin} < {inicio}")
            except Exception:
                pass

        muit = row.get("MONTO_UIT")
        if not vacio(muit):
            try:
                if float(muit) < 0:
                    add("R04", i, row, "MONTO_UIT", muit)
            except (TypeError, ValueError):
                add("R04", i, row, "MONTO_UIT", muit, obs="no numerico")

        if not vacio(muit) and not vacio(row.get("MONTO_S")):
            try:
                uit_val = float(muit)
                monto_s = float(row.get("MONTO_S"))
                anio = _anio_fecha(row.get("F_FIRMA_RES_MC")) or _anio_fecha(row.get("F_NOTIF_DCG"))
                uit = _uit_anio(anio)
                if uit and uit_val > 0:
                    calc = uit_val * uit
                    tol = max(1.0, calc * 0.01)
                    if abs(monto_s - calc) > tol:
                        add(
                            "R05",
                            i,
                            row,
                            "MONTO_S",
                            row.get("MONTO_S"),
                            "ADVERTENCIA",
                            obs=f"calc={calc:.2f} uit_anio={anio}",
                        )
            except (TypeError, ValueError):
                pass

    return conforme, hallazgos


def _amarre(df_multas: pd.DataFrame) -> pd.DataFrame:
    puentes: list[tuple[str, pd.Series, pd.Series]] = []
    if not df_multas.empty:
        excel = df_multas[df_multas["FUENTE_ORIGEN"].isin(["LAM_OD", "CAGR"])]
        sisud = df_multas[df_multas["FUENTE_ORIGEN"] == "SISUD_VW"]
        gapp = df_multas[df_multas["FUENTE_ORIGEN"] == "GAPPS"]
        if "COD_MA" in excel.columns and "NUMERO_EXPEDIENTE" in excel.columns:
            puentes.append(
                (
                    "COD_MA_vs_EXPEDIENTE_excel",
                    excel["COD_MA"].dropna().astype(str).str.strip(),
                    excel["NUMERO_EXPEDIENTE"].dropna().astype(str).str.strip(),
                )
            )
        if not excel.empty and not sisud.empty and "COD_MA" in excel.columns and "CUM" in sisud.columns:
            puentes.append(
                (
                    "COD_MA_vs_CUM_SISUD",
                    excel["COD_MA"].dropna().astype(str).str.strip(),
                    sisud["CUM"].dropna().astype(str).str.strip(),
                )
            )
        if not sisud.empty and not gapp.empty and "CUM" in sisud.columns and "CUM" in gapp.columns:
            puentes.append(
                (
                    "CUM_SISUD_vs_GAPP",
                    sisud["CUM"].dropna().astype(str).str.strip(),
                    gapp["CUM"].dropna().astype(str).str.strip(),
                )
            )

    rows = []
    for puente, izq, der in puentes:
        set_i = set(izq.unique()) - {""}
        set_d = set(der.unique()) - {""}
        match = set_i & set_d
        n_i, n_d, n_m = len(set_i), len(set_d), len(match)
        pct = round(100.0 * n_m / n_i, 2) if n_i else 0.0
        rows.append(
            {
                "ID_CARGA": ID_CARGA,
                "PUENTE": puente,
                "N_IZQ": n_i,
                "N_DER": n_d,
                "N_MATCH": n_m,
                "PCT_MATCH_IZQ": pct,
            }
        )
    cols = ["ID_CARGA", "PUENTE", "N_IZQ", "N_DER", "N_MATCH", "PCT_MATCH_IZQ"]
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=cols)


def aplicar_calidad(
    df_multas: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Marca conformidad, arma MI_DQ_HALLAZGO y QA_AMARRE. No elimina filas."""
    multas = df_multas.copy()
    hallazgos: list[dict] = []

    if len(multas):
        ok_m, h_m = _validar_multas(multas)
        multas["FG_CONFORME"] = ok_m.map(lambda x: "S" if x else "N")
        hallazgos.extend(h_m)
    else:
        multas["FG_CONFORME"] = pd.Series(dtype=str)

    dq_cols = [
        "ID_CARGA",
        "FECHA_CARGA",
        "REGLA_CODIGO",
        "REGLA_DESCRIPCION",
        "FUENTE_ORIGEN",
        "TABLA_DESTINO",
        "REGISTRO_ID",
        "CAMPO",
        "VALOR_ENCONTRADO",
        "SEVERIDAD",
        "ESTADO",
        "OBSERVACION",
        "FECHA_RESOLUCION",
        "RESUELTO_POR",
    ]
    dq = pd.DataFrame(hallazgos) if hallazgos else pd.DataFrame(columns=dq_cols)
    amarre = _amarre(multas)
    return multas, dq, amarre
