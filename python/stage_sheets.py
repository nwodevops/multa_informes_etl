"""Orquesta el staging de Google Sheets (F1 ODs / F2 CSEP) hacia H2 con hop-run.

Se usa desde scripts shell/bat o como parte de la corrida Hop (antes de «Run Python»).
No es main.py: solo llena STG_*; la transformación DW empieza cuando Hop llama a main.py.

Windows (rama windows): reemplaza scripts/stage_ods_sheets.sh y
scripts/stage_csep_sheets.sh. Pipelines Hop (pl_stage_*_sheet.hpl) y catálogos
docs/inputs/f1_ods_sheets.json / f2_csep_sheets.json no cambian.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from config import load_vars, project_root
from h2_conn import connect_h2

RETRY_ENV = {"csep": "STAGE_CSEP_RETRIES", "ods": "STAGE_ODS_RETRIES"}
SLEEP_ENV = {"csep": "STAGE_CSEP_RETRY_SLEEP", "ods": "STAGE_ODS_RETRY_SLEEP"}


def resolve_hop_run() -> str:
    r"""Igual orden que init.bat: HOP_RUN > D:\Eder\hop > %USERPROFILE%\apps\hop > PATH."""
    existing = os.environ.get("HOP_RUN")
    if existing and os.path.isfile(existing):
        return existing
    candidates = [
        r"D:\Eder\hop\hop-run.bat",
        os.path.join(os.path.expanduser("~"), "apps", "hop", "hop-run.bat"),
        os.path.join(os.path.expanduser("~"), "apps", "hop", "hop-run.cmd"),
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    if shutil.which("hop-run"):
        return "hop-run"
    raise SystemExit(
        "no se encontro hop-run (define HOP_RUN o instala en D:\\Eder\\hop)"
    )


def as_int(value: str | None, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def truncate_conn(root: Path, variables: dict[str, str], tables: list[str]) -> None:
    conn = connect_h2(root, variables)
    try:
        cur = conn.cursor()
        for table in tables:
            cur.execute(f"TRUNCATE TABLE PUBLIC.{table}")
        conn.commit()
        print("TRUNCATED " + ", ".join(tables))
    finally:
        conn.close()


def update_conn(root: Path, variables: dict[str, str], statement: str, value: str) -> None:
    conn = connect_h2(root, variables)
    try:
        cur = conn.cursor()
        cur.execute(statement, [value])
        conn.commit()
        print(f"filas_actualizadas={cur.rowcount}")
    finally:
        conn.close()


def classify_error(output: str) -> str:
    low = output.lower()
    if any(token in low for token in (
        "429", "resource_exhausted", "quota exceeded", "userratelimit",
        "ratelimit", "rate limit",
    )):
        return "causa=POSIBLE CUOTA/RATE-LIMIT de Google (HTTP 429)"
    if any(token in low for token in (
        "connect timed out", "sockettimeoutexception", "connectexception",
        "socketexception", "connection refused", "timed out",
    )):
        return "causa=TIMEOUT/SIN RED hacia Google (OAuth o Sheets)"
    if any(token in low for token in (
        "401", "403", "invalid credentials", "invalid_grant",
        "access token", "unauthorized", "insufficient permissions",
    )):
        return "causa=ERROR DE AUTENTICACION/PERMISOS (service account)"
    if any(token in low for token in (
        "400", "bad request", "failed to initialize", "transform",
    )):
        return "causa=FALLO DE INICIALIZACION del transform (revisar pipeline/hoja/rango)"
    if not output.strip():
        return "causa=sin detalle Hop (rc no cero sin mensaje)"
    return "causa=no clasificada (revisar detalle Hop abajo)"


def run_with_retry(
    hop: str,
    project: str,
    root: Path,
    pipeline: str,
    params: str,
    retries: int,
    retry_sleep: int,
    label: str,
) -> None:
    max_attempts = retries + 1
    for attempt in range(1, max_attempts + 1):
        cmd = [
            hop,
            "-j",
            project,
            "-f",
            str(root / "pipelines" / pipeline),
            "-r",
            "local",
            "-p",
            params,
        ]
        proc = subprocess.run(cmd, cwd=str(root), capture_output=True)
        output = (
            (proc.stdout or b"").decode("utf-8", errors="ignore")
            + (proc.stderr or b"").decode("utf-8", errors="ignore")
        ).rstrip()
        if output:
            print(output)
        rc = int(proc.returncode)
        if rc == 0:
            if attempt == 1:
                print(f"OK: {label} completo al primer intento (rc=0)")
            else:
                print(
                    f"OK: {label} completo en ejecucion {attempt}/{max_attempts}"
                    f" (tras {attempt - 1} reintento(s))"
                )
            return
        cause = classify_error(output)
        if attempt >= max_attempts:
            print(
                f"FAIL: {label} agotado tras {max_attempts} ejecuciones"
                f" (1 inicial + {retries} reintentos); rc={rc}; {cause}"
            )
            raise SystemExit(rc)
        remain = max_attempts - attempt
        print(
            f"AVISO: {label} fallo en ejecucion {attempt}/{max_attempts} (rc={rc});"
            f" {cause}; reintento {attempt} de {retries} en {retry_sleep}s"
            f" (quedan {remain} ejecuciones)"
        )
        time.sleep(retry_sleep)


def load_catalog(root: Path, name: str) -> dict:
    path = root / "docs" / "inputs" / name
    if not path.is_file():
        raise SystemExit(f"FAIL: falta {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("csep", "ods"))
    args = parser.parse_args()
    mode = args.mode

    if not os.path.isfile("client_secret.json"):
        raise SystemExit("FAIL: falta client_secret.json (service account)")

    root = project_root()
    variables = load_vars(root)
    hop = resolve_hop_run()
    project = root.name
    retries = as_int(os.environ.get(RETRY_ENV[mode]), 4)
    retry_sleep = as_int(os.environ.get(SLEEP_ENV[mode]), 8)

    if mode == "csep":
        catalog_file = "f2_csep_sheets.json"
        catalog = load_catalog(root, catalog_file)
        cat, key, cod_field = catalog, "unidades", "cod_unidad"
        truncate_conn(
            root,
            variables,
            ["STG_GS1_CSEP_MULTAS", "STG_GS1_ETAPAS"],
        )
        entries = [o for o in cat.get(key, []) if o.get("activo", True)]
        for n, entry in enumerate(entries, start=1):
            cod, spkey = entry[cod_field], entry["spreadsheet_key"]
            print(f"==> [{n}/{len(entries)}] Unidad {cod} (multas)")
            run_with_retry(
                hop, project, root, "pl_stage_csep_sheet.hpl",
                f"SPREADSHEET_KEY={spkey},COD_UNIDAD={cod}",
                retries, retry_sleep, f"CSEP {cod} multas",
            )
            update_conn(
                root, variables,
                "UPDATE PUBLIC.STG_GS1_CSEP_MULTAS SET COD_UNIDAD = ? WHERE COD_UNIDAD IS NULL",
                cod,
            )
            print(f"==> [{n}/{len(entries)}] Unidad {cod} (etapas)")
            run_with_retry(
                hop, project, root, "pl_stage_csep_etapa.hpl",
                f"SPREADSHEET_KEY={spkey}",
                retries, retry_sleep, f"CSEP {cod} etapas",
            )
        print(f"==> Stage CSEP Sheets OK ({len(entries)} unidades)")
    else:
        catalog_file = "f1_ods_sheets.json"
        catalog = load_catalog(root, catalog_file)
        cat, key, cod_field = catalog, "ods", "cod_od"
        truncate_conn(root, variables, ["STG_GS2_OD_MULTAS"])
        entries = [o for o in cat.get(key, []) if o.get("activo", True)]
        for n, entry in enumerate(entries, start=1):
            cod, spkey = entry[cod_field], entry["spreadsheet_key"]
            print(f"==> [{n}/{len(entries)}] OD {cod}")
            run_with_retry(
                hop, project, root, "pl_stage_od_sheet.hpl",
                f"SPREADSHEET_KEY={spkey},COD_OD={cod}",
                retries, retry_sleep, f"OD {cod}",
            )
            update_conn(
                root, variables,
                "UPDATE PUBLIC.STG_GS2_OD_MULTAS SET COD_OD = ? WHERE COD_OD IS NULL",
                cod,
            )
        print(f"==> Stage ODs Sheets OK ({len(entries)} oficinas)")

    return 0


if __name__ == "__main__":
    sys.exit(main())