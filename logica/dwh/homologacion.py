"""Fase 3 — normalización CUM/CAM, fechas, texto, estados (H2–H5, H8)."""

from __future__ import annotations

import re
import warnings

import pandas as pd

from .catalogos import MAPEO_ESTADO
from .constantes import VACIOS


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


def limpiar_texto(s: pd.Series) -> pd.Series:
    """H3: quita saltos de línea y caracteres de control."""
    return (
        s.astype("string")
        .str.replace(r"[\r\n\t]+", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def _serie_datetime(s: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(s):
        return pd.to_datetime(s, errors="coerce")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        iso = pd.to_datetime(s, errors="coerce")
        dmy = pd.to_datetime(s, errors="coerce", dayfirst=True)
    return iso.fillna(dmy)


def parse_fecha_serie(s: pd.Series) -> pd.Series:
    """H4: parseo único a datetime."""
    if s.empty:
        return s
    out = s.copy()
    mask_ts = out.astype("string").str.match(r"TIMESTAMP'", na=False)
    if mask_ts.any():
        out.loc[mask_ts] = (
            out.loc[mask_ts]
            .astype("string")
            .str.replace(r"TIMESTAMP'([^']+)'.*", r"\1", regex=True)
        )
    return _serie_datetime(out)


def normalizar_cum(val) -> str | None:
    """H2: solo dígitos, relleno 11 posiciones."""
    if vacio(val):
        return None
    digits = re.sub(r"\D", "", str(val))
    if not digits:
        return None
    if len(digits) <= 11:
        return digits.zfill(11)
    return digits[:11]


def normalizar_cam(val) -> str | None:
    """H2: patrón AAAA(4)+segmento(2)+correlativo(7)=13."""
    if vacio(val):
        return None
    digits = re.sub(r"\D", "", str(val))
    if not digits:
        return None
    if len(digits) == 11:
        return digits
    if len(digits) >= 13:
        return digits[:13]
    return digits.zfill(13) if len(digits) < 13 else digits


def parse_monto(val):
    if vacio(val):
        return None
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return float(val)
    s = str(val).strip().replace(" ", "").replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def homologar_si_no(val) -> str | None:
    if vacio(val):
        return None
    u = str(val).strip().upper()
    if u in ("SI", "S", "YES"):
        return "S"
    if u in ("NO", "N"):
        return "N"
    return u[:1] if u else None


def homologar_estado(val, tipo_default: str = "MULTA") -> tuple[str | None, str | None]:
    """H8: mapea texto libre a (TIPO_ESTADO, CODIGO) del catálogo."""
    if vacio(val):
        return None, None
    u = str(val).strip().upper()
    if u in MAPEO_ESTADO:
        return MAPEO_ESTADO[u]
    return tipo_default, u.replace(" ", "_")[:50]


def cols_fecha(df: pd.DataFrame) -> list[str]:
    found = []
    for c in df.columns:
        u = str(c).upper()
        if u.startswith("F_") or u.startswith("FN") or u.startswith("FE") or "FECHA" in u:
            found.append(c)
    return found


def cols_monto(df: pd.DataFrame) -> list[str]:
    hints = ("MULTA", "MONTO", "UIT")
    return [c for c in df.columns if any(h in str(c).upper() for h in hints)]


def aplicar_homologacion(df: pd.DataFrame, fuente: str) -> pd.DataFrame:
    """Tipifica columnas conocidas según fuente."""
    out = df.copy()
    for c in out.columns:
        if out[c].dtype == object or pd.api.types.is_string_dtype(out[c]):
            out[c] = limpiar_texto(out[c])

    cum_cols = [c for c in out.columns if "CUM" in str(c).upper()]
    for c in cum_cols:
        out[c] = out[c].map(normalizar_cum)

    cam_cols = [c for c in out.columns if str(c).upper() in ("CAM", "TX_IDCAM")]
    for c in cam_cols:
        out[c] = out[c].map(normalizar_cam)

    for c in cols_fecha(out):
        out[c] = parse_fecha_serie(out[c])

    for c in cols_monto(out):
        out[c] = out[c].map(parse_monto)

    si_no_cols = [
        c
        for c in out.columns
        if any(
            k in str(c).upper()
            for k in ("PRESENT", "AMERIT", "REQ_VERIF", "REQUIERE_VERIF")
        )
    ]
    for c in si_no_cols:
        out[c] = out[c].map(homologar_si_no)

    estado_cols = [c for c in out.columns if "ESTADO" in str(c).upper() or c == "TXESTADO"]
    for c in estado_cols:
        tipo = "MULTA"
        mapped = out[c].map(lambda v: homologar_estado(v, tipo))
        out[f"{c}_TIPO_ESTADO"] = mapped.map(lambda x: x[0])
        out[f"{c}_CODIGO_ESTADO"] = mapped.map(lambda x: x[1])

    out["FUENTE_ORIGEN"] = fuente
    return out
