#!/usr/bin/env python3
"""ENTRY POINT capa lógica post-staging (orquestación delgada).

Quién lo llama:
  - Apache Hop: acción Shell «Run Python» en wf_main.hwf / wf_main_win.hwf
  - Harness: ./init.sh o init.bat (mismo comando)

Qué NO hace: no lee Sheets/SISUD fuente, no homologa, no arma facts.
Eso ya pasó en Hop→STG_* y en logica/dwh/*.

Flujo interno:
  1. SETUP   : root + variables de project-config.json
  2. ENTRADA : io/leer_h2.py → DataFrames (claves = LECTURAS)
  3. LOGICA  : único .py en logica/ → PROF_*, DF_*, DW_M_DIM_*, DW_M_FACT_*, …
  4. SALIDA  : cargar_dw (estrella + DQ + enrich 07) + cargar_aud (DW_M_AUD_*)
               QA/K quedan en memoria (no se publican a Oracle)

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

# DataFrame obligatorio que debe dejar logica/ejecutar.py.
# Es el resumen de una corrida (conteos, fase, carga y hallazgos) y sirve
# como evidencia en memoria/log; si falta, main.py aborta antes de Oracle.
SALIDA_DF = "RESULTADO"


def _load(name: str, path: Path):
    """Carga un .py por ruta (sin instalar el paquete)."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo cargar {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _es_salida(nombre: str) -> bool:
    """True si el nombre del DataFrame es una salida exportable del contrato."""
    if nombre == SALIDA_DF or nombre == "DICCIONARIO":
        return True
    return any(
        nombre.startswith(p)
        for p in (
            "PROF_",
            "DF_",
            "DQ_",
            "QA_",
            "DIM_",
            "FACT_",
            "DET_",
            "IND_",
            "DW_M_DIM_",
            "DW_M_FACT_",
            "DW_M_DET_",
            "DW_M_DQ_",
            "DW_M_QA_",
            "DW_M_INDICADOR_",
        )
    )


def main() -> int:
    # STEP 1: localizar la raíz del repo y cargar variables de configuración.
    root = project_root()
    variables = load_vars(root)

    # STEP 2: leer las tablas STG_* que Hop dejó en H2.
    # Claves típicas: GS1 (F2), GS2 (F1), ETAPAS, ORA (F5), DIC_*
    leer = _load("leer_h2", HERE / "io" / "leer_h2.py")
    datos = leer.leer_h2(root, variables)
    if not datos:
        raise SystemExit("leer_h2() no devolvió DataFrames; revisa LECTURAS en python/io/leer_h2.py")

    # STEP 3: localizar y validar el único archivo .py de logica/.
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

    # STEP 4: inyectar los DataFrames de entrada y ejecutar la lógica.
    # La lógica deja allí las variables de salida, incluido RESULTADO.
    ns: dict = {
        "__name__": "__logica__",
        "__file__": str(archivos[0]),
        "pd": pd,
    }
    ns.update(datos)
    exec(compile(archivos[0].read_text(encoding="utf-8"), str(archivos[0]), "exec"), ns)

    # STEP 5: recolectar automáticamente los DataFrames cuyo nombre siga el contrato:
    # RESULTADO/DICCIONARIO o uno de los prefijos PROF_, DF_, DW_M_DIM_, etc.
    # Esta detección solo arma el catálogo de salidas en memoria; todavía no
    # decide qué tablas se publican en Oracle (ese filtro ocurre más abajo).
    salidas: dict[str, pd.DataFrame] = {}
    for nombre, val in ns.items():
        if _es_salida(nombre) and isinstance(val, pd.DataFrame):
            salidas[nombre] = val

    # STEP 6: verificar que la lógica produjo el resumen obligatorio.
    if SALIDA_DF not in salidas:
        raise SystemExit(
            f"La logica no dejo el DataFrame '{SALIDA_DF}'. Ver python/CONTRATO.md"
        )

    for nombre, df in salidas.items():
        print(f"Salida {nombre}: {len(df)} filas x {len(df.columns)} columnas")

    # STEP 7: seleccionar y publicar en Oracle únicamente estrella + DQ.
    # Estrella + DQ a Oracle. QA/K NO se publican (solo memoria / RESULTADO).
    _evidencia_memoria = {
        "DW_M_FACT_MC_CSEP",
        "DW_M_FACT_MC_OD",
        "DW_M_FACT_MC_SISUD",
    }
    tablas_dw = {
        k: v
        for k, v in salidas.items()
        if (
            k.startswith(("DIM_", "FACT_", "DET_", "DW_M_DIM_", "DW_M_FACT_", "DW_M_DET_"))
            or k == "DW_M_DQ_HALLAZGO"
        )
        and not k.startswith(("DW_M_QA_", "DW_M_INDICADOR_"))
        and k not in _evidencia_memoria
    }
    if tablas_dw:
        # wipe + DDL + INSERT dims/enriquecida/DET/DQ (evidencia FACT_MC_* no se publica)
        cargar = _load("cargar_dw", HERE / "io" / "cargar_dw.py")
        cargar.cargar_dw(tablas_dw, root)

        # Foto cruda 1:1 del staging (usa `datos` de leer_h2, no los facts)
        aud = _load("cargar_aud", HERE / "audit" / "cargar_aud.py")
        aud.cargar_aud(datos, root)

    print(
        "Listo (H2 -> logica -> Oracle canónico dims/enriquecida/DET/DQ + DW_M_AUD_*). "
        "Evidencia FACT_MC_* y QA/K solo en memoria de corrida."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, KeyError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1)
    except Exception as exc:
        print(f"ERROR no controlado: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1)
