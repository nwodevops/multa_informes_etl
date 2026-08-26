"""SALIDA default: DataFrame -> tabla MySQL (TRUNCATE + INSERT + COUNT)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import load_vars, require_live_conn


def escribir_mysql(
    df: pd.DataFrame,
    root: Path,
    *,
    tabla: str = "RESULTADO",
) -> int | None:
    variables = load_vars(root)
    cv = require_live_conn("mysql", variables)

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
