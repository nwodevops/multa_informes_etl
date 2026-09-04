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

ESQUEMA_DEFAULT = "APP"
ESQUEMA = ESQUEMA_DEFAULT
TABLAS = (
    "MI_FACT_MULTA_COERCITIVA",
    "MI_INDICADOR_RESULTADO",
    "MI_DQ_HALLAZGO",
)


def main() -> int:
    root = project_root()
    cv = require_live_conn("oracle_dw", load_vars(root))

    try:
        import oracledb
    except ImportError:
        print("ERROR: falta oracledb", file=sys.stderr)
        return 1

    try:
        oracledb.init_oracle_client()
    except Exception:
        pass

    with oracledb.connect(user=cv["username"], password=cv["password"], dsn=dsn) as conn:
        global ESQUEMA
        cur = conn.cursor()
        cur.execute("SELECT USER FROM dual")
        ESQUEMA = str(cur.fetchone()[0])
        print(f"Conectado como: {ESQUEMA}")
        print(f"Destino: {dest}  esquema {ESQUEMA}")
        print(f"JDBC:    {cv.get('url') or '(makedsn)'}")
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
                FROM {ESQUEMA}.MI_INDICADOR_RESULTADO
                GROUP BY COD_INDICADOR ORDER BY 1
                """
            )
            rows = cur.fetchall()
            if rows:
                print("Indicadores K1–K5:")
                for cod, n in rows:
                    print(f"  {cod}: {n}")
            else:
                print("MI_INDICADOR_RESULTADO: 0 filas — ejecuta ./init.sh o wf_main.hwf")
        except Exception as exc:
            print(f"Indicadores: ERROR {exc}")
        print()
        cur.execute(
            """
            SELECT COUNT(*) FROM all_tables
            WHERE owner = :own AND table_name = 'MI_FACT_INFORME_SUPERVISION'
            """,
            {"own": ESQUEMA},
        )
        n_inf = int(cur.fetchone()[0])
        if n_inf:
            print(f"  {ESQUEMA}.MI_FACT_INFORME_SUPERVISION: AÚN EXISTE (F3)")
            return 1
        print(f"  {ESQUEMA}.MI_FACT_INFORME_SUPERVISION: inexistente")
        cur.execute(
            """
            SELECT COUNT(*) FROM all_tab_columns
            WHERE owner = :own AND table_name = 'MI_FACT_MULTA_COERCITIVA'
              AND column_name = 'ID_INFORME'
            """,
            {"own": ESQUEMA},
        )
        n_col = int(cur.fetchone()[0])
        if n_col:
            print("  MI_FACT_MULTA_COERCITIVA.ID_INFORME: AÚN EXISTE (F3)")
            return 1
        print("  MI_FACT_MULTA_COERCITIVA.ID_INFORME: inexistente")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
