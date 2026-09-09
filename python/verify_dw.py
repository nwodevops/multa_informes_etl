#!/usr/bin/env python3
"""Verifica conteos en Oracle DW canónico (misma conexión que cargar_dw.py).

Uso: .venv/bin/python python/verify_dw.py
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

TABLAS_NUCLEO = (
    "MI_FACT_MC_CSEP",
    "MI_FACT_MC_OD",
    "MI_FACT_MC_SISUD",
    "MI_FACT_MULTA_COERCITIVA",
    "MI_DET_ETAPA_MC",
    "MI_DQ_HALLAZGO",
    "MI_AUD_F1_OD_MULTAS",
    "MI_AUD_F2_CSEP_MULTAS",
    "MI_AUD_F2_CSEP_ETAPAS",
    "MI_AUD_F5_SISUD_VW",
)

PROHIBIDAS = (
    "MI_QA_AMARRE",
    "MI_QA_AMARRE_DETALLE",
    "MI_INDICADOR_RESULTADO",
)


def main() -> int:
    global ESQUEMA
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

    dest = f"{cv['username']}@{cv['host']}:{cv['port']}/{cv['database']}"
    dsn = oracledb.makedsn(cv["host"], int(cv["port"] or "1521"), service_name=cv["database"])
    rc = 0
    with oracledb.connect(user=cv["username"], password=cv["password"], dsn=dsn) as conn:
        cur = conn.cursor()
        cur.execute("SELECT USER FROM dual")
        ESQUEMA = str(cur.fetchone()[0])
        print(f"Conectado como: {ESQUEMA}")
        print(f"Destino: {dest}  esquema {ESQUEMA}")
        print()
        for tabla in TABLAS_NUCLEO:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.{tabla}")
                n = int(cur.fetchone()[0])
                print(f"  {ESQUEMA}.{tabla}: {n}")
            except Exception as exc:
                print(f"  {ESQUEMA}.{tabla}: ERROR {exc}")
                rc = 1
        print()
        cur.execute(
            """
            SELECT view_name FROM user_views
            WHERE view_name LIKE 'VW_MC_%' OR view_name LIKE 'VW_FCT_%'
            ORDER BY 1
            """
        )
        vistas = [r[0] for r in cur.fetchall()]
        if vistas:
            print(f"AVISO: quedan vistas (deberían haberse wipeado): {', '.join(vistas)}")
            rc = 1
        else:
            print("Vistas VW_MC_/VW_FCT_: ninguna (OK)")
        leftover = []
        for tabla in PROHIBIDAS:
            cur.execute(
                "SELECT COUNT(*) FROM user_tables WHERE table_name = :1",
                [tabla],
            )
            if int(cur.fetchone()[0]) > 0:
                leftover.append(tabla)
        if leftover:
            print(f"AVISO: tablas consultoría aún en esquema: {', '.join(leftover)}")
            rc = 1
        else:
            print("QA/K en Oracle: ausentes (OK); MI_DQ_HALLAZGO es canónico")

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
