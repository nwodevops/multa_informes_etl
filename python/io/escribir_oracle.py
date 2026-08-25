"""SALIDA legado: DataFrame -> tabla Oracle BD_CURSOR (TRUNCATE + INSERT + COUNT).

Skip si las credenciales DB_ORA_REPO_* son placeholders. Smoke test H2-only
sin Oracle. ETLs nuevos: MySQL o Excel, no este escritor.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import conn_vars, is_placeholder, load_vars


def escribir_oracle(
    df: pd.DataFrame,
    root: Path,
    *,
    tabla: str = "MI_TABLA",
    esquema: str = "MI_ESQUEMA",
) -> int | None:
    variables = load_vars(root)
    cv = conn_vars("oracle_BD_CURSOR", variables)
    if (
        is_placeholder(cv["host"])
        or is_placeholder(cv["username"])
        or is_placeholder(cv["password"])
        or is_placeholder(cv["database"])
    ):
        print(
            f"AVISO: credenciales Oracle placeholder -> se OMITE el write "
            f"(tabla {esquema}.{tabla})."
        )
        print(f"Resultado en memoria: {len(df)} filas x {len(df.columns)} columnas")
        return None

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
