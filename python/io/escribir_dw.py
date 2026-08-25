"""SALIDA fase 1+: DataFrames INT_* / QA_* / DQ_* -> Oracle BD_CURSOR (esquema APP).

INT_*: CREATE si no existe, TRUNCATE + INSERT + COUNT leido de vuelta.
QA_* / DQ_*: CREATE si no existe, APPEND (historico por ID_CARGA).

Skip si las credenciales DB_ORA_DW_* son placeholders.
Excel se escribe igual; si el PDB no responde, este modulo lanza error.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import conn_vars, is_placeholder, load_vars

ESQUEMA = "APP"
VARCHAR_MAX = 4000


def _ora_ident(name: str) -> str:
    ident = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in str(name).strip())
    ident = ident.upper()[:128]
    if not ident or ident[0].isdigit():
        ident = "C_" + ident
    return ident


def _cell(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(v, pd.Timestamp):
        return v.to_pydatetime()
    if hasattr(v, "to_pydatetime"):
        try:
            return v.to_pydatetime()
        except Exception:
            pass
    if isinstance(v, str) and len(v) > VARCHAR_MAX:
        return v[:VARCHAR_MAX]
    return v


def _ora_type(series: pd.Series) -> str:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "TIMESTAMP"
    return f"VARCHAR2({VARCHAR_MAX})"


def _connect(root: Path):
    variables = load_vars(root)
    cv = conn_vars("oracle_dw", variables)
    if (
        is_placeholder(cv["host"])
        or is_placeholder(cv["username"])
        or is_placeholder(cv["password"])
        or is_placeholder(cv["database"])
    ):
        print("AVISO: credenciales Oracle DW placeholder -> se OMITE el write a BD_CURSOR.")
        return None

    try:
        import oracledb
    except ImportError as exc:
        raise SystemExit(
            "Falta oracledb. Instala: pip install -r python/requirements.txt"
        ) from exc

    dsn = oracledb.makedsn(cv["host"], int(cv["port"] or "1521"), service_name=cv["database"])
    return oracledb.connect(user=cv["username"], password=cv["password"], dsn=dsn)


def _table_exists(cur, tabla: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) FROM user_tables WHERE table_name = :1",
        [tabla],
    )
    return int(cur.fetchone()[0]) > 0


def _tablespace(cur, tabla: str) -> str | None:
    cur.execute(
        "SELECT tablespace_name FROM user_tables WHERE table_name = :1",
        [tabla],
    )
    row = cur.fetchone()
    return None if row is None else str(row[0])


def _ensure_table(cur, tabla: str, df: pd.DataFrame) -> list[str]:
    cols = [_ora_ident(c) for c in df.columns]
    seen: dict[str, int] = {}
    unique: list[str] = []
    for c in cols:
        n = seen.get(c, 0)
        seen[c] = n + 1
        unique.append(c if n == 0 else f"{c}_{n}")
    ts = _tablespace(cur, tabla)
    if ts and ts.upper() == "SYSTEM":
        print(f"DW: {tabla} estaba en SYSTEM -> DROP")
        _drop(cur, tabla)
        ts = None
    if ts is None:
        parts = []
        for name, src in zip(unique, df.columns):
            parts.append(f"{name} {_ora_type(df[src])}")
        ddl = (
            f"CREATE TABLE {ESQUEMA}.{tabla} ({', '.join(parts)}) TABLESPACE USERS"
        )
        cur.execute(ddl)
        print(f"DW: CREATE TABLE {ESQUEMA}.{tabla} TABLESPACE USERS")
    return unique


def _insert(cur, tabla: str, ora_cols: list[str], df: pd.DataFrame) -> int:
    if df.empty:
        cur.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.{tabla}")
        return int(cur.fetchone()[0])
    binds = ", ".join(f":{i + 1}" for i in range(len(ora_cols)))
    col_list = ", ".join(ora_cols)
    rows = [
        tuple(_cell(v) for v in row)
        for row in df.itertuples(index=False, name=None)
    ]
    # stringify non-datetime leftover objects so VARCHAR2 accepts them
    norm = []
    for row in rows:
        out = []
        for v in row:
            if v is None or hasattr(v, "year"):
                out.append(v)
            elif isinstance(v, (bytes, bytearray)):
                out.append(v.decode("utf-8", errors="replace")[:VARCHAR_MAX])
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                out.append(None if pd.isna(v) else str(v))
            else:
                out.append(str(v)[:VARCHAR_MAX] if v is not None else None)
        norm.append(tuple(out))
    cur.executemany(
        f"INSERT INTO {ESQUEMA}.{tabla} ({col_list}) VALUES ({binds})",
        norm,
    )
    cur.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.{tabla}")
    return int(cur.fetchone()[0])


def _drop(cur, tabla: str) -> None:
    cur.execute(f"DROP TABLE {ESQUEMA}.{tabla} PURGE")


def escribir_dw(tablas: dict[str, pd.DataFrame], root: Path) -> dict[str, int]:
    """Escribe INT_* (full refresh) y QA_*/DQ_* (append). Devuelve COUNT por tabla."""
    if not tablas:
        print("AVISO: no hay tablas INT_/QA_/DQ_ para BD_CURSOR.")
        return {}

    conn = _connect(root)
    if conn is None:
        return {}

    counts: dict[str, int] = {}
    try:
        cur = conn.cursor()
        try:
            for nombre, df in tablas.items():
                tabla = _ora_ident(nombre)
                ora_cols = _ensure_table(cur, tabla, df)
                modo = "append" if tabla.startswith(("QA_", "DQ_")) else "truncate"
                if modo == "truncate":
                    cur.execute(f"TRUNCATE TABLE {ESQUEMA}.{tabla}")
                try:
                    n_out = _insert(cur, tabla, ora_cols, df)
                except Exception as exc:
                    msg = str(exc)
                    if "ORA-01950" not in msg:
                        raise
                    print(f"DW: {tabla} en tablespace sin cuota -> DROP y recreate en USERS")
                    _drop(cur, tabla)
                    ora_cols = _ensure_table(cur, tabla, df)
                    n_out = _insert(cur, tabla, ora_cols, df)
                conn.commit()
                counts[tabla] = n_out
                print(
                    f"{tabla}: {len(df)} filas -> {ESQUEMA}.{tabla} "
                    f"({modo}, {n_out} en BD)"
                )
        finally:
            cur.close()
    finally:
        conn.close()
    return counts
