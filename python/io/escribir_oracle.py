"""SALIDA legado: DataFrame -> tabla Oracle BD_CURSOR (TRUNCATE + INSERT + COUNT).

ETLs nuevos: MySQL o Excel, no este escritor.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import load_vars, require_live_conn


def escribir_oracle(
    df: pd.DataFrame,
    root: Path,
    *,
    tabla: str = "MI_TABLA",
    esquema: str = "MI_ESQUEMA",
) -> int | None:
    variables = load_vars(root)
    cv = require_live_conn("oracle_BD_CURSOR", variables)

    try:
        import oracledb
    except ImportError as exc:
        raise SystemExit(
            "Falta oracledb. Instala: pip install -r python/requirements.txt"
        ) from exc

    dsn = oracledb.makedsn(cv["host"], int(cv["port"] or "1521"), service_name=cv["database"])
    conn = oracledb.connect(user=cv["username"], password=cv["password"], dsn=dsn)
    fq = f"{esquema}.{tabla}"
    cols = list(df.columns)
    placeholders = ", ".join(f":{i + 1}" for i in range(len(cols)))
    col_list = ", ".join(cols)
    rows = [
        tuple(None if pd.isna(v) else v for v in row)
        for row in df.itertuples(index=False, name=None)
    ]
    try:
        cur = conn.cursor()
        cur.execute(f"TRUNCATE TABLE {fq}")
        if rows:
            cur.executemany(f"INSERT INTO {fq} ({col_list}) VALUES ({placeholders})", rows)
        conn.commit()
        cur.execute(f"SELECT COUNT(*) FROM {fq}")
        n_out = int(cur.fetchone()[0])
    finally:
        conn.close()

    print(f"{tabla}: {len(df)} filas -> {fq} ({n_out} en BD)")
    return n_out
