"""Espejo del canónico DW en MySQL (DB_MYSQL_DW_*) — invocado por main.py tras Oracle.

Wipe solo DW_M_% (no toca T_MVC_*). DDL se infiere de los DataFrames.
Si MySQL DW no responde: aviso y return {} (no tumba la corrida).
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pandas as pd

from config import is_placeholder, load_vars, project_root, require_live_conn

# Mismo orden que python/io/cargar_dw.py
TABLAS_DIM = (
    "DW_M_DIM_TIEMPO",
    "DW_M_DIM_ADMINISTRADO",
    "DW_M_DIM_ORGANO_UNIDAD",
    "DW_M_DIM_OD",
    "DW_M_DIM_FUENTE_REGISTRO",
    "DW_M_DIM_MATERIA_SUBSECTOR",
    "DW_M_DIM_ESTADO",
    "DW_M_DIM_PARAMETRO_UIT",
)
INSERT_ORDEN = (
    *TABLAS_DIM,
    "DW_M_FACT_MULTA_COERCITIVA",
    "DW_M_DET_ETAPA_MC",
    "DW_M_DQ_HALLAZGO",
)

_DATE_PREFIXES = ("F_", "FECHA")
_INT_HINTS = (
    "ID_",
    "FLAG_",
    "ANIO",
    "MES",
    "DIA",
    "TRIMESTRE",
    "SEMANA",
    "N_PROY",
    "DIAS_",
    "ES_",
)


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


def _destino_label(cv: dict[str, str]) -> str:
    return f"{cv['username']}@{cv['host']}:{cv['port']}/{cv['database']}"


def _mysql_type(col: str, series: pd.Series) -> str:
    name = str(col).upper()
    if any(name.startswith(p) for p in _DATE_PREFIXES) or name in (
        "FECHA",
        "FECHA_CARGA",
        "FECHA_ACTUALIZACION",
        "FECHA_RESOLUCION",
    ):
        return "DATETIME"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "DATETIME"
    if any(h in name for h in _INT_HINTS) or pd.api.types.is_integer_dtype(series):
        return "BIGINT"
    if pd.api.types.is_float_dtype(series):
        return "DECIMAL(18,4)"
    if name.startswith("MONTO") or name.startswith("VALOR") or name.startswith("PCT_"):
        return "DECIMAL(18,4)"
    # TEXT evita MySQL 1118 (row size) en fact ancho (~60 cols string)
    return "TEXT"


def _create_sql(tabla: str, df: pd.DataFrame) -> str:
    if df is None or len(df.columns) == 0:
        raise ValueError(f"{tabla}: DataFrame sin columnas para DDL MySQL")
    cols = []
    for c in df.columns:
        name = str(c).upper()
        safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name)
        if not safe or safe[0].isdigit():
            safe = "C_" + safe
        cols.append(f"`{safe}` {_mysql_type(c, df[c])}")
    body = ",\n  ".join(cols)
    return f"CREATE TABLE `{tabla}` (\n  {body}\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"


def _drop_dw_tables(cur) -> None:
    cur.execute("SHOW TABLES LIKE 'DW_M_%'")
    tablas = [r[0] for r in cur.fetchall()]
    if not tablas:
        return
    cur.execute("SET FOREIGN_KEY_CHECKS=0")
    for t in tablas:
        cur.execute(f"DROP TABLE IF EXISTS `{t}`")
        print(f"DW-MYSQL: DROP TABLE {t}", flush=True)
    cur.execute("SET FOREIGN_KEY_CHECKS=1")


def _coerce(v, mysql_type: str):
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(v, pd.Timestamp):
        return v.to_pydatetime()
    if isinstance(v, datetime):
        return v
    if isinstance(v, date) and not isinstance(v, datetime):
        return datetime(v.year, v.month, v.day)
    if mysql_type.startswith("DATETIME"):
        try:
            ts = pd.Timestamp(v)
            if pd.isna(ts):
                return None
            return ts.to_pydatetime()
        except Exception:
            return None
    if mysql_type.startswith(("BIGINT", "DECIMAL")):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return None if pd.isna(v) else v
        if isinstance(v, str) and v.strip() == "":
            return None
        try:
            return float(v) if "." in str(v) or mysql_type.startswith("DECIMAL") else int(float(v))
        except (TypeError, ValueError):
            return None
    s = v.decode("utf-8", errors="replace") if isinstance(v, bytes) else str(v)
    return s[:65535]


def _insert_df(cur, tabla: str, df: pd.DataFrame) -> int:
    if df is None or df.empty:
        cur.execute(f"SELECT COUNT(*) FROM `{tabla}`")
        return int(cur.fetchone()[0])

    col_names = []
    types = []
    for c in df.columns:
        name = str(c).upper()
        safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name)
        if not safe or safe[0].isdigit():
            safe = "C_" + safe
        col_names.append(safe)
        types.append(_mysql_type(c, df[c]))

    placeholders = ", ".join(["%s"] * len(col_names))
    col_list = ", ".join(f"`{c}`" for c in col_names)
    rows = []
    for row in df.itertuples(index=False, name=None):
        rows.append(tuple(_coerce(v, t) for v, t in zip(row, types)))
    if rows:
        cur.executemany(
            f"INSERT INTO `{tabla}` ({col_list}) VALUES ({placeholders})",
            rows,
        )
    cur.execute(f"SELECT COUNT(*) FROM `{tabla}`")
    return int(cur.fetchone()[0])


def cargar_dw_mysql(
    tablas: dict[str, pd.DataFrame],
    root: Path | None = None,
) -> dict[str, int]:
    """Wipe DW_M_* + CREATE + INSERT espejo del canónico Oracle. Soft-fail si no hay MySQL."""
    root = root or project_root()
    if not tablas:
        print("DW-MYSQL: AVISO no hay tablas para cargar", flush=True)
        return {}

    variables = load_vars(root)
    try:
        cv_check = {
            "host": variables.get("DB_MYSQL_DW_HOST", ""),
            "username": variables.get("DB_MYSQL_DW_USERNAME", ""),
            "password": variables.get("DB_MYSQL_DW_PASSWORD", ""),
        }
        if (
            is_placeholder(cv_check["host"])
            or is_placeholder(cv_check["username"])
            or is_placeholder(cv_check["password"])
        ):
            print(
                "DW-MYSQL: AVISO credenciales placeholder; se omite carga MySQL DW",
                flush=True,
            )
            return {}
        conn, cv = _connect(root)
    except Exception as exc:
        print(f"DW-MYSQL: AVISO no disponible ({exc}); Oracle ya cargó", flush=True)
        return {}

    counts: dict[str, int] = {}
    try:
        cur = conn.cursor()
        try:
            print(f"DW-MYSQL: wipe+carga → {_destino_label(cv)}", flush=True)
            _drop_dw_tables(cur)
            conn.commit()

            for tabla in INSERT_ORDEN:
                df = tablas.get(tabla)
                if df is None:
                    continue
                if len(df.columns) == 0:
                    print(f"DW-MYSQL: AVISO {tabla} sin columnas; skip", flush=True)
                    continue
                cur.execute(_create_sql(tabla, df))
                n_df = len(df)
                n_bd = _insert_df(cur, tabla, df)
                conn.commit()
                counts[tabla] = n_bd
                ok = "OK" if n_bd == n_df else "REVISAR"
                print(f"DW-MYSQL: {tabla}: {n_df} filas -> {n_bd} en BD ({ok})", flush=True)

            print(f"DW-MYSQL: destino {_destino_label(cv)}", flush=True)
            for tabla in (
                "DW_M_FACT_MULTA_COERCITIVA",
                "DW_M_DET_ETAPA_MC",
                "DW_M_DQ_HALLAZGO",
            ):
                if tabla not in counts:
                    continue
                cur.execute(f"SELECT COUNT(*) FROM `{tabla}`")
                n = int(cur.fetchone()[0])
                print(
                    f"DW-MYSQL: POST-CARGA {tabla} = {n} filas "
                    f"(esperado {counts[tabla]})",
                    flush=True,
                )
        finally:
            cur.close()
    except Exception as exc:
        print(f"DW-MYSQL: AVISO fallo durante carga ({exc}); Oracle intacto", flush=True)
        try:
            conn.rollback()
        except Exception:
            pass
        return counts
    finally:
        conn.close()
    return counts
