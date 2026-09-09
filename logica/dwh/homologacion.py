"""Fase 3 — normalización de valores (H2–H5, H8).

Homologar = tipificar / limpiar para que F1, F2 y F5 sean COMPARABLES.
NO fusiona fuentes (eso no ocurre aquí). NO arma facts.

Analogía Java: un Normalizer / ValueObject factory aplicado columna a columna.

Orden en aplicar_homologacion:
  texto → CUM/CAM → fechas → montos → sí/no → estados (+ FUENTE_ORIGEN)

Clave de enrich Sheet↔SISUD (usada también en SQL 07):
  normalizar_resolucion(N_RES) + "|" + MONTO_UIT a 4 decimales
  → 0153-… ≡ 00153-… si el monto coincide.
"""

from __future__ import annotations

import re
import warnings

import pandas as pd

from .catalogos import MAPEO_ESTADO
from .constantes import VACIOS


def vacio(v) -> bool:
    """True si null/NaN/blanco o token de error Excel (#N/A, etc.). Ver constantes.VACIOS."""
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
    """H3: quita saltos de línea y caracteres de control; colapsa espacios."""
    return (
        s.astype("string")
        .str.replace(r"[\r\n\t]+", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def _serie_datetime(s: pd.Series) -> pd.Series:
    """Intenta ISO; si falla, day-first (DD/MM típico Sheets)."""
    if pd.api.types.is_datetime64_any_dtype(s):
        return pd.to_datetime(s, errors="coerce")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        iso = pd.to_datetime(s, errors="coerce")
        dmy = pd.to_datetime(s, errors="coerce", dayfirst=True)
    return iso.fillna(dmy)


def parse_fecha_serie(s: pd.Series) -> pd.Series:
    """H4: parseo único a datetime (incluye TIMESTAMP'...' de algunos exports)."""
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
    """H2: solo dígitos, relleno a 11 posiciones (ej. 46882612 → 00046882612)."""
    if vacio(val):
        return None
    digits = re.sub(r"\D", "", str(val))
    if not digits:
        return None
    if len(digits) <= 11:
        return digits.zfill(11)
    return digits[:11]


def normalizar_cam(val) -> str | None:
    """H2: CAM institucional — 11 dígitos o pad/truncate a 13 (AAAA+seg+correlativo)."""
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
    """Convierte montos texto/número a float; quita espacios y comas de miles."""
    if vacio(val):
        return None
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return float(val)
    s = str(val).strip().replace(" ", "").replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def normalizar_resolucion(val) -> str | None:
    """Homologa N_RES_MC / RESOLUCION para join Sheet↔SISUD (0153 ≡ 00153).

    Quita ceros a la izquierda del primer bloque numérico; el resto del texto se conserva.
    Misma idea que REGEXP_REPLACE(..., '^0+', '') en SQL 07.
    """
    if vacio(val):
        return None
    s = re.sub(r"\s+", "", str(val).strip().upper())
    if not s:
        return None
    m = re.match(r"^0*(\d+)(.*)$", s)
    if m:
        return f"{m.group(1)}{m.group(2)}"
    return s


def clave_join_res_monto(n_res, monto_uit) -> str | None:
    """Clave estable resolución_norm|MONTO_UIT (4 decimales). Usada en amarre y alineada a SQL 07."""
    nr = normalizar_resolucion(n_res)
    m = parse_monto(monto_uit)
    if nr is None or m is None:
        return None
    return f"{nr}|{m:.4f}"


def homologar_si_no(val) -> str | None:
    """SI/S/YES → S ; NO/N → N (flags de planilla)."""
    if vacio(val):
        return None
    u = str(val).strip().upper()
    if u in ("SI", "S", "YES"):
        return "S"
    if u in ("NO", "N"):
        return "N"
    return u[:1] if u else None


def homologar_estado(val, tipo_default: str = "MULTA") -> tuple[str | None, str | None]:
    """H8: texto libre → (TIPO_ESTADO, CODIGO) vía catalogos.MAPEO_ESTADO.

    Ej.: "INCUMPLIDO" → ("MULTA","INCUMPLIDO"); "PAGADO" → ("PAGO","PAGADO").
    Si no está en el mapa: (tipo_default, TEXTO_CON_GUIONES).
    dimensional._resolve_estado usa esto para obtener ID_ESTADO_*.
    """
    if vacio(val):
        return None, None
    u = str(val).strip().upper()
    if u in MAPEO_ESTADO:
        return MAPEO_ESTADO[u]
    return tipo_default, u.replace(" ", "_")[:50]


def cols_fecha(df: pd.DataFrame) -> list[str]:
    """Heurística: columnas cuyo nombre sugiere fecha (F_, FN, FE, FECHA)."""
    found = []
    for c in df.columns:
        u = str(c).upper()
        if u.startswith("F_") or u.startswith("FN") or u.startswith("FE") or "FECHA" in u:
            found.append(c)
    return found


def cols_monto(df: pd.DataFrame) -> list[str]:
    """Heurística: columnas con MULTA / MONTO / UIT en el nombre."""
    hints = ("MULTA", "MONTO", "UIT")
    return [c for c in df.columns if any(h in str(c).upper() for h in hints)]


def aplicar_homologacion(df: pd.DataFrame, fuente: str) -> pd.DataFrame:
    """Tipifica columnas conocidas y etiqueta FUENTE_ORIGEN.

    No renombra columnas de negocio (MULTA_UIT→MONTO_UIT lo hace integracion._renombrar).
    """
    out = df.copy()

    # 1) Texto en columnas object/string
    for c in out.columns:
        if out[c].dtype == object or pd.api.types.is_string_dtype(out[c]):
            out[c] = limpiar_texto(out[c])

    # 2) Identificadores institucionales
    cum_cols = [c for c in out.columns if "CUM" in str(c).upper()]
    for c in cum_cols:
        out[c] = out[c].map(normalizar_cum)

    cam_cols = [c for c in out.columns if str(c).upper() in ("CAM", "TX_IDCAM")]
    for c in cam_cols:
        out[c] = out[c].map(normalizar_cam)

    # 3) Fechas y montos
    for c in cols_fecha(out):
        out[c] = parse_fecha_serie(out[c])

    for c in cols_monto(out):
        out[c] = out[c].map(parse_monto)

    # 4) Flags sí/no de planilla
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

    # 5) Estados: deja columnas auxiliares *_TIPO_ESTADO / *_CODIGO_ESTADO
    estado_cols = [c for c in out.columns if "ESTADO" in str(c).upper() or c == "TXESTADO"]
    for c in estado_cols:
        tipo = "MULTA"
        mapped = out[c].map(lambda v: homologar_estado(v, tipo))
        out[f"{c}_TIPO_ESTADO"] = mapped.map(lambda x: x[0])
        out[f"{c}_CODIGO_ESTADO"] = mapped.map(lambda x: x[1])

    out["FUENTE_ORIGEN"] = fuente  # OD_SHEETS | CAGR | SISUD_VW
    return out
