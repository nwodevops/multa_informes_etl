#!/usr/bin/env python3
"""ENTRY POINT de la capa de lógica post-staging (orquestación delgada).

CAPA POST-STAGING — no importar python/introspect ni create_stg.

Flujo:
  1. SETUP   : root + variables de project-config.json
  2. ENTRADA : io/leer_h2.py              -> DataFrames (nombres = claves de LECTURAS)
  3. LOGICA  : el UNICO .py de logica/    -> RESULTADO + INT_* + QA_*
  4. SALIDA  : Excel multi-hoja (siempre) + Oracle BD_CURSOR (INT_ refresh, QA_ append)

No escribe a MySQL gappsdb (es fuente) ni a Oracle REPOCSEP (legado).
Contrato: python/CONTRATO.md
Uso: .venv/bin/python python/main.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from config import load_vars, project_root  # noqa: E402

SALIDA_DF = "RESULTADO"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo cargar {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _es_salida(nombre: str) -> bool:
    return nombre == SALIDA_DF or nombre.startswith("INT_") or nombre.startswith("QA_")


def main() -> int:
    root = project_root()
    variables = load_vars(root)

    leer = _load("leer_h2", HERE / "io" / "leer_h2.py")
    datos = leer.leer_h2(root, variables)
    if not datos:
        raise SystemExit("leer_h2() no devolvió DataFrames; revisa LECTURAS en python/io/leer_h2.py")

    logica_dir = root / "logica"
    archivos = sorted(p for p in logica_dir.glob("*.py") if p.name != "__init__.py")
    if not archivos:
        raise SystemExit(
            "No hay ningun .py en logica/. Pega ahi tu logica (ver python/plantilla_logica.py)"
        )
    if len(archivos) > 1:
        raise SystemExit(
            f"Hay mas de un .py en logica/: {len(archivos)}. Deja un solo archivo de logica."
        )

    print(f"Logica: {archivos[0].name}")
    import pandas as pd

    if str(logica_dir) not in sys.path:
        sys.path.insert(0, str(logica_dir))

    ns: dict = {
        "__name__": "__logica__",
        "__file__": str(archivos[0]),
        "pd": pd,
    }
    ns.update(datos)
    exec(compile(archivos[0].read_text(encoding="utf-8"), str(archivos[0]), "exec"), ns)

    salidas: dict[str, pd.DataFrame] = {}
    for nombre, val in ns.items():
        if _es_salida(nombre) and isinstance(val, pd.DataFrame):
            salidas[nombre] = val

    if SALIDA_DF not in salidas:
        raise SystemExit(
            f"La logica no dejo el DataFrame '{SALIDA_DF}' (configurable en main.py). Ver python/CONTRATO.md"
        )

    for nombre, df in salidas.items():
        print(f"Salida {nombre}: {len(df)} filas x {len(df.columns)} columnas")

    excel = _load("escribir_excel", HERE / "io" / "escribir_excel.py")
    excel.escribir_libro(salidas, root, nombre="fase1.xlsx")

    dw = _load("escribir_dw", HERE / "io" / "escribir_dw.py")
    dw.escribir_dw(
        {k: v for k, v in salidas.items() if k.startswith("INT_") or k.startswith("QA_")},
        root,
    )

    print("Listo (H2 -> logica -> Excel + BD_CURSOR).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
