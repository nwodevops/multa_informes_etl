"""Catálogo F2 CSEP Google Sheets (docs/inputs/f2_csep_sheets.json)."""

from __future__ import annotations

import json
from pathlib import Path


DEFAULT_REL = Path("docs/inputs/f2_csep_sheets.json")


def catalog_path(root: Path, rel: str | Path | None = None) -> Path:
    return (root / (rel or DEFAULT_REL)).resolve()


def load_catalog(root: Path, rel: str | Path | None = None) -> dict:
    path = catalog_path(root, rel)
    if not path.is_file():
        raise FileNotFoundError(f"Catálogo F2 CSEP no encontrado: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: raíz debe ser un objeto JSON")
    return data


def active_unidades(catalog: dict) -> list[dict]:
    rows = catalog.get("unidades") or []
    return [o for o in rows if isinstance(o, dict) and o.get("activo", True)]


def stg_columns(catalog: dict) -> list[str]:
    cols = list(catalog.get("columns") or [])
    inject = (catalog.get("inject_column") or "COD_UNIDAD").strip()
    if inject and inject not in cols:
        cols = [inject] + cols
    return cols


def etapas_columns(catalog: dict) -> list[str]:
    return list(catalog.get("etapas_columns") or [])


def descripcion_por_sigla(catalog: dict) -> dict[str, str]:
    """Mapa COD_UNIDAD (upper) → nombre largo del catálogo F2."""
    out: dict[str, str] = {}
    for o in catalog.get("unidades") or []:
        if not isinstance(o, dict):
            continue
        cod = str(o.get("cod_unidad") or "").strip().upper()
        nombre = str(o.get("nombre") or "").strip()
        if cod and nombre:
            out[cod] = nombre
    return out
