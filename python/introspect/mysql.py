"""Introspección MySQL: INFORMATION_SCHEMA.COLUMNS. No extrae filas."""

from __future__ import annotations

from config import require_live_conn
from .h2_ddl import Column, map_h2_type, sanitize_ident


def _split_object(object_name: str) -> tuple[str, str]:
    parts = object_name.strip().split(".")
    if len(parts) != 2:
        raise ValueError(
            f"object MySQL debe ser schema.tabla, recibido: {object_name!r}"
        )
    return parts[0], parts[1]


def introspect(source: dict, variables: dict[str, str], root=None) -> list[Column]:
    try:
        import mysql.connector
    except ImportError as exc:
        raise SystemExit(
            "Falta mysql-connector-python. Instala: pip install -r python/requirements.txt"
        ) from exc

    connection = source.get("connection") or "mysql"
    object_name = source.get("object")
    if not object_name:
        raise ValueError(f"{source.get('stg_table')}: falta object (schema.tabla)")

    schema, table = _split_object(object_name)
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
