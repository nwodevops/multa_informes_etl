"""SALIDA default: DataFrame -> tabla MySQL (TRUNCATE + INSERT + COUNT).

Skip si las credenciales DB_MYSQL_* son placeholders.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import conn_vars, is_placeholder, load_vars


def escribir_mysql(
    df: pd.DataFrame,
    root: Path,
    *,
    tabla: str = "RESULTADO",
) -> int | None:
    variables = load_vars(root)
    cv = conn_vars("mysql", variables)
    if (
        is_placeholder(cv["host"])
        or is_placeholder(cv["username"])
        or is_placeholder(cv["password"])
        or is_placeholder(cv["database"])
    ):
        print(
            f"AVISO: credenciales MySQL placeholder -> se OMITE el write (tabla {tabla})."
        )
        return None

    try:
        import mysql.connector
    except ImportError as exc:
        raise SystemExit(
            "Falta mysql-connector-python. Instala: pip install -r python/requirements.txt"
        ) from exc

    conn = mysql.connector.connect(
        host=cv["host"],
        port=int(cv["port"] or "3306"),
        user=cv["username"],
        password=cv["password"],
        database=cv["database"],
    )
    cols = list(df.columns)
    placeholders = ", ".join(["%s"] * len(cols))
    col_list = ", ".join(f"`{c}`" for c in cols)
    rows = [
        tuple(None if pd.isna(v) else v for v in row)
        for row in df.itertuples(index=False, name=None)
    ]
    try:
        cur = conn.cursor()
        cur.execute(f"TRUNCATE TABLE `{tabla}`")
        if rows:
            cur.executemany(
                f"INSERT INTO `{tabla}` ({col_list}) VALUES ({placeholders})", rows
            )
        conn.commit()
        cur.execute(f"SELECT COUNT(*) FROM `{tabla}`")
        n_out = int(cur.fetchone()[0])
    finally:
        conn.close()

    print(f"{tabla}: {len(df)} filas -> MySQL ({n_out} en BD)")
    return n_out
