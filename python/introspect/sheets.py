"""Introspección Google Sheets: fila de headers. Todo VARCHAR. No extrae filas."""

from __future__ import annotations

from pathlib import Path

from h2_ddl import Column, map_h2_type, sanitize_ident


def introspect(source: dict, variables: dict[str, str], root: Path | None = None) -> list[Column]:
    try:
        import gspread
    except ImportError as exc:
        raise SystemExit(
            "Falta gspread. Instala: pip install -r python/requirements.txt"
        ) from exc

    if root is None:
        raise ValueError("sheets: falta root del proyecto")

    secret = root / "client_secret.json"
    if not secret.is_file():
        raise FileNotFoundError(
            f"No se encuentra {secret} (service account Google, gitignored)"
        )

    key = (source.get("spreadsheet_key") or "").strip()
    worksheet = source.get("worksheet")
    if not key:
        raise ValueError(f"{source.get('stg_table')}: falta spreadsheet_key")
    if not worksheet:
        raise ValueError(f"{source.get('stg_table')}: falta worksheet")
    if key.startswith("${"):
        raise ValueError(
            f"spreadsheet_key no resuelta: {key}. "
            "Define la variable en project-config.json"
        )

    gc = gspread.service_account(filename=str(secret))
    book = gc.open_by_key(key)
    sheet = book.worksheet(str(worksheet))
    headers = sheet.row_values(1)
    if not headers:
        raise ValueError(f"Sheets '{worksheet}': fila 1 vacía")

    used: set[str] = set()
    cols: list[Column] = []
    for header in headers:
        if header is None or str(header).strip() == "":
            continue
        cols.append(
            Column(
                name=sanitize_ident(str(header), used),
                h2_type=map_h2_type("VARCHAR", sheets=True),
            )
        )
    if not cols:
        raise ValueError(f"Sheets '{worksheet}': sin headers usables")
    return cols
