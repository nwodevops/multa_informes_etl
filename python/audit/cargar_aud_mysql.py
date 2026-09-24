"""Foto cruda STG → MySQL DW_M_AUD_* (espejo de cargar_aud Oracle).

Lo llama main.py después de cargar_dw_mysql. Soft-fail si MySQL DW no responde.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from config import is_placeholder, load_vars, project_root, require_live_conn

# Mismo mapeo que python/audit/cargar_aud.py
MAPEO_AUD: dict[str, str] = {
    "GS1": "DW_M_AUD_F2_CSEP_MULTAS",
    "ETAPAS": "DW_M_AUD_F2_CSEP_ETAPAS",
    "GS2": "DW_M_AUD_F1_OD_MULTAS",
    "ORA": "DW_M_AUD_F5_SISUD_VW",
    "MYSQL": "DW_M_AUD_F4_FORM",
}

VARCHAR_LEN = 4000  # truncado al serializar; DDL usa TEXT (evita row size MySQL)


def _connect(root: Path):
    variables = load_vars(root)
    cv = require_live_conn("mysql_dw", variables)
    try:
        import mysql.connector
    except ImportError as exc:
        raise RuntimeError(
            "Falta mysql-connector-python. Instala: pip install -r python/requirements.txt"
        ) from exc
    port = int(cv["port"]) if str(cv["port"]).isdigit() else 3306
    conn = mysql.connector.connect(
        host=cv["host"],
        port=port,
        user=cv["username"],
        password=cv["password"],
        database=cv["database"],
        autocommit=False,
    )
    return conn, cv


def _safe_col(name: str) -> str:
    s = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in str(name).upper())
    if not s or s[0].isdigit():
        s = "C_" + s
    return s[:64]


def _as_str(v) -> str | None:
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
    return s[:VARCHAR_LEN]


def _columnas_plantilla(stg_key: str, df: pd.DataFrame | None, root: Path) -> list[str]:
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
    cur.execute(f"DROP TABLE IF EXISTS `{tabla}`")
    names = _columnas_plantilla(stg_key, df, root)
    if not names:
        cur.execute(
            f"CREATE TABLE `{tabla}` ("
            f"`FECHA_CARGA` DATETIME DEFAULT CURRENT_TIMESTAMP"
            f") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
        )
        print(f"AUD-MYSQL: {tabla}: 0 filas (STG vacío)", flush=True)
        return 0

    cols = [_safe_col(c) for c in names]
    seen: dict[str, int] = {}
    unique_cols: list[str] = []
    for c in cols:
        base = c
        n = seen.get(base, 0)
        seen[base] = n + 1
        unique_cols.append(base if n == 0 else f"{base[:60]}_{n}")

    col_defs = ", ".join(f"`{c}` TEXT" for c in unique_cols)
    col_defs += ", `FECHA_CARGA` DATETIME DEFAULT CURRENT_TIMESTAMP"
    cur.execute(
        f"CREATE TABLE `{tabla}` ({col_defs}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
    )

    col_list = ", ".join(f"`{c}`" for c in unique_cols)
    placeholders = ", ".join(["%s"] * len(unique_cols))
    rows = []
    if df is not None and not df.empty:
        for row in df.itertuples(index=False, name=None):
            rows.append(tuple(_as_str(v) for v in row))
    if rows:
        cur.executemany(
            f"INSERT INTO `{tabla}` ({col_list}) VALUES ({placeholders})",
            rows,
        )
    cur.execute(f"SELECT COUNT(*) FROM `{tabla}`")
    n = int(cur.fetchone()[0])
    n_stg = 0 if df is None else len(df)
    print(f"AUD-MYSQL: {tabla}: {n_stg} filas STG -> {n} en BD", flush=True)
    return n


def cargar_aud_mysql(
    stg: dict[str, pd.DataFrame],
    root: Path | None = None,
) -> dict[str, int]:
    """Crea/llena DW_M_AUD_* en MySQL DW. Soft-fail si no hay conexión."""
    root = root or project_root()
    variables = load_vars(root)
    try:
        if (
            is_placeholder(variables.get("DB_MYSQL_DW_HOST"))
            or is_placeholder(variables.get("DB_MYSQL_DW_USERNAME"))
            or is_placeholder(variables.get("DB_MYSQL_DW_PASSWORD"))
        ):
            print(
                "AUD-MYSQL: AVISO credenciales placeholder; se omite AUD MySQL",
                flush=True,
            )
            return {}
        conn, cv = _connect(root)
    except Exception as exc:
        print(f"AUD-MYSQL: AVISO no disponible ({exc})", flush=True)
        return {}

    counts: dict[str, int] = {}
    try:
        cur = conn.cursor()
        try:
            dest = f"{cv['username']}@{cv['host']}:{cv['port']}/{cv['database']}"
            print(f"AUD-MYSQL: foto cruda STG → {dest}.DW_M_AUD_*", flush=True)
            for stg_key, tabla in MAPEO_AUD.items():
                df = stg.get(stg_key)
                if df is None and stg_key != "MYSQL":
                    print(
                        f"AUD-MYSQL: AVISO falta STG '{stg_key}' → skip {tabla}",
                        flush=True,
                    )
                    continue
                if df is None:
                    print(
                        f"AUD-MYSQL: AVISO MySQL INPUT no stageado; {tabla} vacía",
                        flush=True,
                    )
                    df = pd.DataFrame()
                elif df.empty and stg_key == "MYSQL":
                    print(
                        f"AUD-MYSQL: AVISO STG MySQL vacío; {tabla} vacía",
                        flush=True,
                    )
                counts[tabla] = _create_and_load(
                    cur, tabla, df, stg_key=stg_key, root=root
                )
                conn.commit()
        finally:
            cur.close()
    except Exception as exc:
        print(f"AUD-MYSQL: AVISO fallo ({exc})", flush=True)
        try:
            conn.rollback()
        except Exception:
            pass
        return counts
    finally:
        conn.close()
    return counts
