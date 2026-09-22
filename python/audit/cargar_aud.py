"""Foto cruda de staging → Oracle DW_M_AUD_* (fuera de la estrella Kimball).

Lo llama python/main.py DESPUÉS de cargar_dw, pasando los DataFrames de leer_h2
(no los facts). Sirve para contrastar “qué bajó Hop” vs “qué quedó en DW_M_FACT_*”.

Mapeo STG lógico → tabla audit:
  GS1    → DW_M_AUD_F2_CSEP_MULTAS
  ETAPAS → DW_M_AUD_F2_CSEP_ETAPAS
  GS2    → DW_M_AUD_F1_OD_MULTAS
  ORA    → DW_M_AUD_F5_SISUD_VW
  MYSQL  → DW_M_AUD_F4_FORM

Todas las columnas se guardan como VARCHAR2 (foto 1:1 textual) + FECHA_CARGA.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from config import load_vars, project_root, require_live_conn

ESQUEMA_DEFAULT = "APP"
ESQUEMA = ESQUEMA_DEFAULT

# Clave de leer_h2 → tabla Oracle de auditoría
MAPEO_AUD: dict[str, str] = {
    "GS1": "DW_M_AUD_F2_CSEP_MULTAS",
    "ETAPAS": "DW_M_AUD_F2_CSEP_ETAPAS",
    "GS2": "DW_M_AUD_F1_OD_MULTAS",
    "ORA": "DW_M_AUD_F5_SISUD_VW",
    "MYSQL": "DW_M_AUD_F4_FORM",
}

VARCHAR_LEN = 4000


def _connect(root: Path):
    variables = load_vars(root)
    cv = require_live_conn("oracle_dw", variables)
    try:
        import oracledb
    except ImportError as exc:
        raise SystemExit("Falta oracledb. Instala: pip install -r python/requirements.txt") from exc
    dsn = oracledb.makedsn(cv["host"], int(cv["port"] or "1521"), service_name=cv["database"])
    return oracledb.connect(user=cv["username"], password=cv["password"], dsn=dsn), cv


def _bind_schema(cur) -> str:
    global ESQUEMA
    cur.execute("SELECT USER FROM DUAL")
    ESQUEMA = str(cur.fetchone()[0])
    return ESQUEMA


def _safe_col(name: str) -> str:
    """Nombre de columna Oracle-safe (≤30, sin caracteres raros)."""
    s = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in str(name).upper())
    if not s or s[0].isdigit():
        s = "C_" + s
    return s[:30]


def _as_str(v) -> str | None:
    """Serializa cualquier valor STG a texto (o None) para VARCHAR2."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(v, pd.Timestamp):
        return v.isoformat(sep=" ", timespec="seconds")
    if isinstance(v, datetime):
        return v.isoformat(sep=" ", timespec="seconds")
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace")[:VARCHAR_LEN]
    s = str(v)
    if len(s.encode("utf-8")) <= VARCHAR_LEN:
        return s
    cut = s
    while cut and len(cut.encode("utf-8")) > VARCHAR_LEN:
        cut = cut[:-1]
    return cut


def _drop_table(cur, tabla: str) -> None:
    cur.execute(
        "SELECT COUNT(*) FROM user_tables WHERE table_name = :1",
        [tabla.upper()],
    )
    if int(cur.fetchone()[0]) == 0:
        return
    cur.execute(f"DROP TABLE {ESQUEMA}.{tabla} CASCADE CONSTRAINTS PURGE")
    print(f"AUD: DROP TABLE {tabla}", flush=True)


def _columnas_plantilla(stg_key: str, df: pd.DataFrame | None, root: Path) -> list[str]:
    """Columnas de la foto AUD. Si MySQL no bajó filas, usa aliases del sql_file."""
    if df is not None and len(df.columns):
        return [str(c) for c in df.columns]
    if stg_key == "MYSQL":
        from introspect.mysql import introspect

        cols = introspect(
            {
                "stg_table": "STG_MYSQL_MULTAS",
                "sql_file": "input_legacy/input_mysql/vw_multas_app.sql",
                "types": "varchar",
            },
            {},
            root,
        )
        return [c.name for c in cols]
    return []


def _create_and_load(
    cur,
    tabla: str,
    df: pd.DataFrame | None,
    *,
    stg_key: str,
    root: Path,
) -> int:
    """DROP+CREATE+INSERT de una tabla DW_M_AUD_* a partir de un DataFrame STG.

    STG vacío o MySQL caído: crea la tabla (columnas de plantilla) con 0 filas.
    """
    _drop_table(cur, tabla)
    names = _columnas_plantilla(stg_key, df, root)
    if not names:
        cur.execute(
            f"CREATE TABLE {ESQUEMA}.{tabla} ("
            f"FECHA_CARGA DATE DEFAULT SYSDATE)"
        )
        print(f"AUD: {tabla}: 0 filas (STG vacío)", flush=True)
        return 0

    cols = [_safe_col(c) for c in names]
    # Evitar duplicados tras truncar a 30 chars
    seen: dict[str, int] = {}
    unique_cols: list[str] = []
    for c in cols:
        base = c
        n = seen.get(base, 0)
        seen[base] = n + 1
        unique_cols.append(base if n == 0 else f"{base[:28]}_{n}")

    col_defs = ", ".join(f"{c} VARCHAR2({VARCHAR_LEN})" for c in unique_cols)
    col_defs += ", FECHA_CARGA DATE DEFAULT SYSDATE"
    cur.execute(f"CREATE TABLE {ESQUEMA}.{tabla} ({col_defs})")

    col_list = ", ".join(unique_cols)
    binds = ", ".join(f":{i + 1}" for i in range(len(unique_cols)))
    rows = []
    if df is not None and not df.empty:
        for row in df.itertuples(index=False, name=None):
            rows.append(tuple(_as_str(v) for v in row))
    if rows:
        cur.executemany(
            f"INSERT INTO {ESQUEMA}.{tabla} ({col_list}) VALUES ({binds})",
            rows,
        )
    cur.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.{tabla}")
    n = int(cur.fetchone()[0])
    n_stg = 0 if df is None else len(df)
    print(f"AUD: {tabla}: {n_stg} filas STG -> {n} en BD", flush=True)
    return n


def cargar_aud(
    stg: dict[str, pd.DataFrame],
    root: Path | None = None,
) -> dict[str, int]:
    """Punto de entrada desde main.py: crea/llena DW_M_AUD_* desde STG (GS1/ETAPAS/GS2/ORA/MYSQL)."""
    root = root or project_root()
    # STEP 8.1: abrir Oracle para guardar la fotografía cruda del staging.
    conn, _cv = _connect(root)
    counts: dict[str, int] = {}
    try:
        cur = conn.cursor()
        try:
            # STEP 8.2: recorrer el mapeo STG lógico → tabla DW_M_AUD_*.
            _bind_schema(cur)
            print(f"AUD: foto cruda STG → {ESQUEMA}.DW_M_AUD_*", flush=True)
            for stg_key, tabla in MAPEO_AUD.items():
                df = stg.get(stg_key)
                if df is None and stg_key != "MYSQL":
                    print(f"AUD: AVISO falta STG '{stg_key}' → skip {tabla}", flush=True)
                    continue
                if df is None:
                    print(f"AUD: AVISO MySQL no stageado; {tabla} vacía", flush=True)
                    df = pd.DataFrame()
                elif df.empty and stg_key == "MYSQL":
                    print(f"AUD: AVISO STG MySQL vacío; {tabla} vacía", flush=True)
                counts[tabla] = _create_and_load(
                    cur, tabla, df, stg_key=stg_key, root=root
                )
                conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()
    return counts
