#!/usr/bin/env python3
"""DEPRECATED — usar python/verify_dw.py.

Histórico: verificación K1–K5 / QA / VW en Oracle. El DW canónico ya no publica
esos objetos; el harness (init.sh / init.bat) valida con verify_dw.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from config import load_vars, project_root, require_live_conn  # noqa: E402


def main() -> int:
    root = project_root()
    try:
        cv = require_live_conn("oracle_dw", load_vars(root))
    except ValueError as exc:
        print(f"AVISO: Oracle DW omitido (credenciales placeholder): {exc}")
        return 0

    try:
        import oracledb
    except ImportError:
        print("ERROR: falta oracledb", file=sys.stderr)
        return 1

    try:
        oracledb.init_oracle_client()
    except Exception:
        pass

    dsn = oracledb.makedsn(cv["host"], int(cv["port"] or "1521"), service_name=cv["database"])
    with oracledb.connect(user=cv["username"], password=cv["password"], dsn=dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT USER FROM dual")
            esq = str(cur.fetchone()[0])

            cur.execute(f"SELECT COUNT(*) FROM {esq}.MI_INDICADOR_RESULTADO")
            n = int(cur.fetchone()[0])
            print(f"MI_INDICADOR_RESULTADO: {n} filas en Oracle")
            cur.execute(
                f"SELECT DISTINCT COD_INDICADOR FROM {esq}.MI_INDICADOR_RESULTADO ORDER BY 1"
            )
            codes = {r[0] for r in cur.fetchall()}
            missing = sorted({"K1", "K2", "K3", "K4", "K5"} - codes)
            if missing:
                print(f"ERROR: faltan indicadores en Oracle: {missing}", file=sys.stderr)
                return 1
            print("Indicadores K1-K5 presentes")

            cur.execute(
                "SELECT COUNT(*) FROM all_tables WHERE owner = :1 AND table_name = 'MI_FACT_INFORME_SUPERVISION'",
                [esq],
            )
            if int(cur.fetchone()[0]):
                print("ERROR: APP.MI_FACT_INFORME_SUPERVISION aun existe (F3)", file=sys.stderr)
                return 1
            print("MI_FACT_INFORME_SUPERVISION: inexistente")

            cur.execute(
                "SELECT COUNT(*) FROM all_tab_columns WHERE owner = :1 AND table_name = 'MI_FACT_MULTA_COERCITIVA' AND column_name = 'ID_INFORME'",
                [esq],
            )
            if int(cur.fetchone()[0]):
                print("ERROR: MI_FACT_MULTA_COERCITIVA.ID_INFORME aun existe (F3)", file=sys.stderr)
                return 1
            print("ID_INFORME: inexistente en MI_FACT_MULTA_COERCITIVA")

            cur.execute(
                "SELECT COUNT(*) FROM all_tab_columns WHERE owner = :1 AND table_name = 'MI_FACT_MULTA_COERCITIVA' AND column_name = 'FUENTE_REGISTRO'",
                [esq],
            )
            if int(cur.fetchone()[0]):
                print("ERROR: MI_FACT_MULTA_COERCITIVA.FUENTE_REGISTRO aun existe", file=sys.stderr)
                return 1
            print("FUENTE_REGISTRO VARCHAR: inexistente")

            cur.execute(
                "SELECT COUNT(*) FROM all_tab_columns WHERE owner = :1 AND table_name = 'MI_FACT_MULTA_COERCITIVA' AND column_name = 'ID_TIEMPO_FIRMA'",
                [esq],
            )
            if not int(cur.fetchone()[0]):
                print("ERROR: falta MI_FACT_MULTA_COERCITIVA.ID_TIEMPO_FIRMA", file=sys.stderr)
                return 1
            print("ID_TIEMPO_FIRMA: presente")

            cur.execute(
                f"""
                SELECT 'CSEP' AS U, COUNT(*) FROM {esq}.MI_FACT_MC_CSEP
                UNION ALL
                SELECT 'OD', COUNT(*) FROM {esq}.MI_FACT_MC_OD
                UNION ALL
                SELECT 'SISUD', COUNT(*) FROM {esq}.MI_FACT_MC_SISUD
                UNION ALL
                SELECT 'ENRIQUECIDA', COUNT(*) FROM {esq}.MI_FACT_MULTA_COERCITIVA
                """
            )
            by_tbl = {r[0]: int(r[1]) for r in cur.fetchall()}
            print(f"Conteos evidencia+enriquecida: {by_tbl}")
            expected_min = {"CSEP": 200, "OD": 50, "SISUD": 50}
            for cod, mn in expected_min.items():
                n = by_tbl.get(cod, 0)
                if n < mn:
                    print(
                        f"ERROR: conteo {cod}={n} bajo minimo esperado {mn} (posible fallo de staging)",
                        file=sys.stderr,
                    )
                    return 1
            n_enriq = by_tbl.get("ENRIQUECIDA", 0)
            n_sheets = by_tbl.get("CSEP", 0) + by_tbl.get("OD", 0)
            if n_enriq != n_sheets:
                print(
                    f"ERROR: enriquecida={n_enriq} debe igualar CSEP+OD={n_sheets}",
                    file=sys.stderr,
                )
                return 1

            cur.execute(
                f"""
                SELECT COUNT(*),
                       SUM(CASE WHEN CUM IS NOT NULL AND CAM IS NOT NULL THEN 1 ELSE 0 END)
                FROM {esq}.MI_FACT_MULTA_COERCITIVA
                WHERE REGEXP_REPLACE(UPPER(REPLACE(TRIM(N_RES_MC), ' ', '')), '^0+([0-9]+)', '\\1')
                      LIKE '153-2026-OEFA/DSEM'
                  AND MONTO_UIT = 64
                """
            )
            row = cur.fetchone()
            n0153 = int(row[0] or 0)
            n_con_cum = int(row[1] or 0)
            print(f"Caso 0153/64: {n0153} filas enriquecida, {n_con_cum} con CUM+CAM")
            if n0153 < 2:
                print(
                    f"ERROR: caso 0153/64: esperado >=2 filas enriquecida, hay {n0153}",
                    file=sys.stderr,
                )
                return 1

            cur.execute(f"SELECT COUNT(*) FROM {esq}.MI_DIM_ORGANO_UNIDAD")
            n_org = int(cur.fetchone()[0])
            if n_org > 20:
                print(f"ERROR: MI_DIM_ORGANO_UNIDAD={n_org} (esperado ~11 CSEP+ND)", file=sys.stderr)
                return 1
            print(f"MI_DIM_ORGANO_UNIDAD: {n_org}")

            for v in ("VW_MC_CSEP", "VW_MC_OD", "VW_MC_SISUD", "VW_MC_ENRIQUECIDA"):
                cur.execute(
                    "SELECT COUNT(*) FROM all_views WHERE owner=:1 AND view_name=:2",
                    [esq, v],
                )
                if not int(cur.fetchone()[0]):
                    print(f"ERROR: falta vista {esq}.{v}", file=sys.stderr)
                    return 1
            print("Vistas VW_MC_*: OK")

            cur.execute(f"SELECT COUNT(*) FROM {esq}.MI_QA_AMARRE_DETALLE")
            n_det = int(cur.fetchone()[0])
            print(f"MI_QA_AMARRE_DETALLE: {n_det} filas")
            if n_det < 1:
                print("ERROR: MI_QA_AMARRE_DETALLE vacio (esperado claves sin match H9)", file=sys.stderr)
                return 1

            cur.execute(f"SELECT COUNT(*) FROM {esq}.MI_QA_AMARRE")
            n_am = int(cur.fetchone()[0])
            print(f"MI_QA_AMARRE: {n_am} filas")
            if n_am < 1:
                print("ERROR: MI_QA_AMARRE vacio (esperado resumen de puentes H9)", file=sys.stderr)
                return 1

            cur.execute(
                f"SELECT COUNT(*) FROM {esq}.MI_QA_AMARRE WHERE PUENTE = 'RES_MONTO_Sheets_vs_SISUD'"
            )
            if not int(cur.fetchone()[0]):
                print("ERROR: falta puente RES_MONTO_Sheets_vs_SISUD en MI_QA_AMARRE", file=sys.stderr)
                return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())