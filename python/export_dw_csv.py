#!/usr/bin/env python3
"""Vuelca tablas DW (esquema del usuario Oracle) a CSV para verlas en
Power BI sin depender del conector Oracle (que exige ODAC/admin).

Uso (desde la raíz del proyecto, con VPN a 10.6.0.15):
  .venv\\Scripts\\python.exe python\\export_dw_csv.py
Salida: output\\dw_csv\\<TABLA>.csv
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import oracledb

from config import load_vars, project_root


def main() -> int:
    root = project_root()
    variables = load_vars(root)

    dsn = (
        f"{variables['DB_ORA_DW_HOST']}:{variables['DB_ORA_DW_PORT']}/"
        f"{variables['DB_ORA_DW_DATABASE']}"
    )
    user = variables["DB_ORA_DW_USERNAME"]
    password = variables["DB_ORA_DW_PASSWORD"]

    out_dir = root / "output" / "dw_csv"
    out_dir.mkdir(parents=True, exist_ok=True)

    with oracledb.connect(user=user, password=password, dsn=dsn) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT table_name FROM all_tables WHERE owner = :owner "
            "AND (table_name LIKE 'MI\\_%' ESCAPE '\\' OR table_name LIKE 'STG\\_%' ESCAPE '\\') "
            "ORDER BY table_name",
            owner=user.upper(),
        )
        tables = [row[0] for row in cur.fetchall()]

        if not tables:
            print("dw_csv: sin tablas MI_*/STG_* en esquema", user.upper())
            return 0

        total = 0
        for table in tables:
            cur.execute(f'SELECT * FROM "{table}"')
            cols = [d[0] for d in cur.description]
            path = out_dir / f"{table}.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as fh:
                writer = csv.writer(fh)
                writer.writerow(cols)
                count = 0
                for row in cur:
                    writer.writerow(row)
                    count += 1
            print(f"dw_csv: {table} -> {path.relative_to(root)} ({count} filas)")
            total += count

    print(f"dw_csv: OK. {len(tables)} tablas, {total} filas en {out_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except oracledb.Error as exc:
        print(f"ERROR Oracle: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc