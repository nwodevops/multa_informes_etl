"""Catálogo F1 OD Google Sheets (docs/inputs/f1_ods_sheets.json).

Usado por stage_sheets / Hop y por dimensional (MI_DIM_OD / COD_OD).
No descarga datos: solo lee el JSON de oficinas activas y spreadsheet_key.
"""

from __future__ import annotations

import json
from pathlib import Path


DEFAULT_REL = Path("docs/inputs/f1_ods_sheets.json")


def catalog_path(root: Path, rel: str | Path | None = None) -> Path:
    return (root / (rel or DEFAULT_REL)).resolve()


def load_catalog(root: Path, rel: str | Path | None = None) -> dict:
    path = catalog_path(root, rel)
    if not path.is_file():
        raise FileNotFoundError(f"Catálogo F1 OD no encontrado: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: raíz debe ser un objeto JSON")
    return data


def active_ods(catalog: dict) -> list[dict]:
    rows = catalog.get("ods") or []
    return [o for o in rows if isinstance(o, dict) and o.get("activo", True)]


def stg_columns(catalog: dict) -> list[str]:
    cols = list(catalog.get("columns") or [])
    if "COD_OD" not in cols:
        cols = ["COD_OD"] + cols
    return cols
