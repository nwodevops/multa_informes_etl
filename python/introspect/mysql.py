"""Introspección MySQL: aliases del sql_file o INFORMATION_SCHEMA. No extrae filas."""

from __future__ import annotations

import re
from pathlib import Path

from config import project_root, require_live_conn
from .h2_ddl import Column, map_h2_type, sanitize_ident

_AS_RE = re.compile(r"\bAS\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)


def _first_select(sql: str) -> str:
    """Primer SELECT no comentado hasta el ';' que cierra el query."""
    lines = []
    for line in sql.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("--"):
            continue
        lines.append(line)
    body = "\n".join(lines)
    m = re.search(r"(?is)\bSELECT\b.*?;", body)
    if not m:
        raise ValueError("sql_file: no se encontró un SELECT … ;")
    return m.group(0)


def _outer_select_list(sql: str) -> str:
    """Lista del SELECT externo (hasta el FROM a profundidad 0)."""
    select = _first_select(sql)
    depth = 0
    i = 0
    upper = select.upper()
    start = upper.find("SELECT")
    if start < 0:
        raise ValueError("sql_file: SELECT no encontrado")
    i = start + 6
    while i < len(select):
        ch = select[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif depth == 0 and upper.startswith("FROM", i) and (
            i == 0 or not upper[i - 1].isalnum()
        ):
            return select[start + 6 : i]
        i += 1
    raise ValueError("sql_file: FROM externo no encontrado")


def _aliases_from_sql(sql: str) -> list[str]:
    head = _outer_select_list(sql)
    aliases = _AS_RE.findall(head)
    if "NU_IDMC" not in {a.upper() for a in aliases}:
        aliases.append("NU_IDMC")
    if not aliases:
        raise ValueError("sql_file: 0 aliases AS …")
    return aliases


def introspect(source: dict, variables: dict[str, str], root=None) -> list[Column]:
    root = Path(root) if root is not None else project_root()
    sql_file = source.get("sql_file")
    if sql_file:
        path = Path(sql_file)
        if not path.is_absolute():
            path = root / path
        if not path.is_file():
            raise ValueError(f"{source.get('stg_table')}: no existe sql_file {path}")
        used: set[str] = set()
        cols: list[Column] = []
        force_varchar = str(source.get("types") or "").lower() == "varchar"
        for alias in _aliases_from_sql(path.read_text(encoding="utf-8")):
            cols.append(
                Column(
                    name=sanitize_ident(alias, used),
                    h2_type="VARCHAR(4000)" if force_varchar else "VARCHAR(4000)",
                )
            )
        return cols

    try:
        import mysql.connector
    except ImportError as exc:
        raise SystemExit(
            "Falta mysql-connector-python. Instala: pip install -r python/requirements.txt"
        ) from exc

    connection = source.get("connection") or "mysql"
    object_name = source.get("object")
    if not object_name:
        raise ValueError(f"{source.get('stg_table')}: falta sql_file u object (schema.tabla)")

    parts = object_name.strip().split(".")
    if len(parts) != 2:
        raise ValueError(f"object MySQL debe ser schema.tabla, recibido: {object_name!r}")
    schema, table = parts[0], parts[1]
    cv = require_live_conn(connection, variables)
    port = int(cv["port"]) if str(cv["port"]).isdigit() else 3306

    conn = mysql.connector.connect(
        host=cv["host"],
        port=port,
        user=cv["username"],
        password=cv["password"],
        database=schema,
    )
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COLUMN_NAME, DATA_TYPE, NUMERIC_SCALE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
            """,
            (schema, table),
        )
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    if not rows:
        raise ValueError(f"MySQL {schema}.{table}: 0 columnas (¿schema/tabla mal?)")

    used: set[str] = set()
    cols: list[Column] = []
    for name, data_type, scale in rows:
        sc = None if scale is None else int(scale)
        cols.append(
            Column(
                name=sanitize_ident(str(name), used),
                h2_type=map_h2_type(str(data_type), scale=sc),
            )
        )
    return cols
