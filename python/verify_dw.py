#!/usr/bin/env python3
"""Verifica conteos en Oracle DW (misma conexión que cargar_dw.py).

Uso: .venv/bin/python python/verify_dw.py

Imprime destino JDBC y COUNT por tabla clave. Útil cuando el log Hop dice OK
pero el cliente SQL muestra la tabla vacía (suele ser otra instancia/puerto).
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from config import load_vars, project_root, require_live_conn  # noqa: E402

ESQUEMA = "APP"
TABLAS = (
    "FACT_MULTA_COERCITIVA",
    "FACT_INFORME_SUPERVISION",
    "INDICADOR_RESULTADO",
    "DQ_HALLAZGO",
)


def main() -> int:
    root = project_root()
    cv = require_live_conn("oracle_dw", load_vars(root))

    try:
        import oracledb
    except ImportError:
        print("ERROR: falta oracledb", file=sys.stderr)
        return 1

    dest = f"{cv['username']}@{cv['host']}:{cv['port']}/{cv['database']}"
    print(f"Destino: {dest}  esquema {ESQUEMA}")
    print(f"JDBC:    {cv.get('url') or '(makedsn)'}")
    print()

    dsn = oracledb.makedsn(cv["host"], int(cv["port"] or "1521"), service_name=cv["database"])
    with oracledb.connect(user=cv["username"], password=cv["password"], dsn=dsn) as conn:
        cur = conn.cursor()
        cur.execute("SELECT USER FROM dual")
        print(f"Conectado como: {cur.fetchone()[0]}")
        print()
        for tabla in TABLAS:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.{tabla}")
                n = int(cur.fetchone()[0])
                print(f"  {ESQUEMA}.{tabla}: {n}")
            except Exception as exc:
                print(f"  {ESQUEMA}.{tabla}: ERROR {exc}")
        print()
        try:
            cur.execute(
                f"""
                SELECT COD_INDICADOR, COUNT(*)
                FROM {ESQUEMA}.INDICADOR_RESULTADO
                GROUP BY COD_INDICADOR ORDER BY 1
                """
            )
            rows = cur.fetchall()
            if rows:
                print("Indicadores K1–K5:")
                for cod, n in rows:
                    print(f"  {cod}: {n}")
            else:
                print("INDICADOR_RESULTADO: 0 filas — ejecuta ./init.sh o wf_main.hwf")
        except Exception as exc:
            print(f"Indicadores: ERROR {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
