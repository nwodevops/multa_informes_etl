"""c) Diagnostico de calidad: marcar, no borrar. Controles warn."""

from __future__ import annotations

import warnings

import pandas as pd

from .constantes import (
    COLS_QA_EXC,
    DETALLE,
    FECHA_CORRIDA,
    ID_CORRIDA,
    MAX_EXC_POR_TABLA,
    MONTO_HINT,
    VACIOS,
)


def vacio(v) -> bool:
    if v is None:
        return True
    try:
        if pd.isna(v):
            return True
    except (TypeError, ValueError):
        pass
    s = str(v).strip()
    return s.upper() in VACIOS or s == ""


def serie_llave(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    partes = []
    for c in cols:
        if c not in df.columns:
            partes.append(pd.Series([""] * len(df), index=df.index))
            continue
        partes.append(df[c].map(lambda x: "" if vacio(x) else str(x).strip()))
    if not partes:
        return pd.Series([""] * len(df), index=df.index)
    out = partes[0]
    for p in partes[1:]:
        out = out + "|" + p
    return out


def cols_fecha(df: pd.DataFrame) -> list[str]:
    found = []
    for c in df.columns:
        if c in ("ID_CORRIDA", "FUENTE"):
            continue
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            found.append(c)
            continue
        u = str(c).upper()
        if u.startswith("F_") or u.startswith("FE") or "FECHA" in u:
            found.append(c)
    return found


def cols_monto(df: pd.DataFrame) -> list[str]:
    found = []
    for c in df.columns:
        if c in ("ID_CORRIDA", "FUENTE"):
            continue
        u = str(c).upper()
        if any(h in u for h in MONTO_HINT):
            found.append(c)
    return found


def _serie_vacio(s: pd.Series) -> pd.Series:
    t = s.astype("string").str.strip().str.upper()
    return s.isna() | t.isin(VACIOS) | t.eq("") | t.eq("<NA>")


def _serie_datetime(s: pd.Series) -> pd.Series:
    """ISO/YMD primero; DMY (Excel PE) solo si el primero falla. Sin UserWarning a stderr."""
    if pd.api.types.is_datetime64_any_dtype(s):
        return pd.to_datetime(s, errors="coerce")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        iso = pd.to_datetime(s, errors="coerce")
        dmy = pd.to_datetime(s, errors="coerce", dayfirst=True)
    return iso.fillna(dmy)


def fechas_malas(s: pd.Series) -> pd.Series:
    return ~_serie_vacio(s) & _serie_datetime(s).isna()


def parse_fecha(v):
    if vacio(v):
        return None
    if hasattr(v, "year"):
        return v
    ts = _serie_datetime(pd.Series([v])).iloc[0]
    if pd.isna(ts):
        return "BAD"
    return ts


def parse_monto(v):
    if vacio(v):
        return None
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return v
    s = str(v).strip().replace(" ", "").replace(",", "")
    try:
        return float(s)
    except ValueError:
        return "BAD"


def _n_malos(df: pd.DataFrame, cols: list[str], parser) -> int:
    n = 0
    for c in cols:
        if c not in df.columns:
            continue
        n += int(df[c].map(parser).eq("BAD").sum())
    return n


def _exc(tipo: str, tabla: str, fuente: str, llave: str, detalle: str) -> dict:
    return {
        "ID_CORRIDA": ID_CORRIDA,
        "FECHA_CORRIDA": FECHA_CORRIDA,
        "TABLA": tabla,
        "FUENTE": fuente,
        "TIPO": tipo,
        "LLAVE": llave,
        "DETALLE": detalle,
    }


def diagnosticar(
    df: pd.DataFrame, tabla: str, fuente: str, capa: str, llave_cols: list[str]
) -> tuple[dict, list[dict]]:
    n = len(df)
    llave = serie_llave(df, llave_cols)
    n_nula = int((llave == "").sum()) if n else 0
    no_nulas = llave[llave != ""]
    n_dup = int(no_nulas.duplicated(keep="first").sum()) if n else 0
    n_fecha = 0
    for c in cols_fecha(df):
        n_fecha += int(fechas_malas(df[c]).sum())
    n_monto = _n_malos(df, cols_monto(df), parse_monto)
    corrida = {
        "ID_CORRIDA": ID_CORRIDA,
        "FECHA_CORRIDA": FECHA_CORRIDA,
        "CAPA": capa,
        "FUENTE": fuente,
        "TABLA": tabla,
        "N_FILAS": n,
        "N_LLAVE_NULA": n_nula,
        "N_DUPLICADO_LLAVE": n_dup,
        "CHECK_STS": "OK" if n_nula == 0 and n_dup == 0 else "WARN",
        "DETALLE": (
            f"{DETALLE}; llave={'+'.join(llave_cols)}; "
            f"fecha_mala={n_fecha}; monto_malo={n_monto}"
        ),
    }
    excs: list[dict] = []
    if n:
        for i, val in llave.items():
            if val == "" and len(excs) < MAX_EXC_POR_TABLA:
                excs.append(
                    _exc("LLAVE_NULA", tabla, fuente, "", f"fila={i} cols={'+'.join(llave_cols)}")
                )
        seen: dict[str, int] = {}
        for i, val in llave.items():
            if val == "":
                continue
            seen[val] = seen.get(val, 0) + 1
            if seen[val] > 1 and len(excs) < MAX_EXC_POR_TABLA:
                excs.append(
                    _exc(
                        "DUPLICADO_LLAVE",
                        tabla,
                        fuente,
                        val[:400],
                        f"fila={i} ocurrencia={seen[val]}",
                    )
                )
        for c in cols_fecha(df):
            malas = fechas_malas(df[c])
            for i in df.index[malas]:
                if len(excs) >= MAX_EXC_POR_TABLA:
                    break
                excs.append(
                    _exc(
                        "FECHA_NO_PARSEABLE",
                        tabla,
                        fuente,
                        str(llave.loc[i])[:400],
                        f"col={c} valor={df.at[i, c]!r}"[:1000],
                    )
                )
        for c in cols_monto(df):
            parsed = df[c].map(parse_monto)
            for i, flag in parsed.items():
                if flag != "BAD":
                    continue
                if len(excs) >= MAX_EXC_POR_TABLA:
                    break
                excs.append(
                    _exc(
                        "MONTO_NO_PARSEABLE",
                        tabla,
                        fuente,
                        str(llave.loc[i])[:400],
                        f"col={c} valor={df.at[i, c]!r}"[:1000],
                    )
                )
    recorte = max(0, n_nula + n_dup + n_fecha + n_monto - MAX_EXC_POR_TABLA)
    if recorte > 0:
        corrida["DETALLE"] += f"; excepciones_recortadas~={recorte}"
    return corrida, excs[:MAX_EXC_POR_TABLA]


def armar_qa(
    piezas: list[tuple[pd.DataFrame, str, str, str, list[str]]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    corridas: list[dict] = []
    excs: list[dict] = []
    for df, tabla, fuente, capa, cols in piezas:
        row, xs = diagnosticar(df, tabla, fuente, capa, cols)
        corridas.append(row)
        excs.extend(xs)
    qa_corrida = pd.DataFrame(corridas)
    qa_exc = (
        pd.DataFrame(excs)
        if excs
        else pd.DataFrame(columns=COLS_QA_EXC)
    )
    return qa_corrida, qa_exc
