#!/usr/bin/env python3
"""Exit 0 si la conexión está configurada (no placeholder); exit 1 si debe omitirse.

Uso: .venv/bin/python python/should_stage_external.py oracle_sisud
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from config import conn_vars, is_placeholder, load_vars, project_root  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("Uso: should_stage_external.py <oracle_sisud|mysql>", file=sys.stderr)
        return 2
    conn = args[0]
    cv = conn_vars(conn, load_vars(project_root()))
    for key in ("host", "port", "username", "password"):
        if is_placeholder(cv.get(key, "")):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
