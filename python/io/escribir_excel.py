"""SALIDA default: DataFrame -> Excel en output/."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def escribir_excel(df: pd.DataFrame, root: Path, *, nombre: str = "resultado.xlsx") -> Path:
    out_dir = root / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / nombre
    df.to_excel(path, index=False, engine="openpyxl")
    print(f"Excel: {len(df)} filas x {len(df.columns)} columnas -> {path.relative_to(root)}")
    return path
