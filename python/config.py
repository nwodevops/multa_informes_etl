"""Lee project-config.json (variables Hop) + inputs.yaml."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

VAR_RE = re.compile(r"\$\{([A-Za-z0-9_]+)\}")

CONNECTION_PREFIX = {
    "oracle_sisud": "DB_ORA_SISUD",
    "oracle_repocsep": "DB_ORA_REPO",
    "mysql": "DB_MYSQL",
    "h2": "DB_H2",
}


def project_root(start: Path | None = None) -> Path:
    here = (start or Path(__file__).resolve()).parent
    if here.name == "python":
        return here.parent
    return here


def load_vars(root: Path) -> dict[str, str]:
    cfg_path = root / "project-config.json"
    if not cfg_path.is_file():
        raise FileNotFoundError(f"No se encuentra: {cfg_path}")
    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for item in data.get("config", {}).get("variables", []):
        name = item.get("name")
        if name:
            out[name] = "" if item.get("value") is None else str(item["value"])
    return out


def resolve_vars(text: str, variables: dict[str, str]) -> str:
    if not isinstance(text, str):
        return text

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in variables:
            raise KeyError(f"Variable ${{{key}}} no definida en project-config.json")
        return variables[key]

    return VAR_RE.sub(repl, text)


def is_placeholder(value: str | None) -> bool:
    if value is None or str(value).strip() == "":
        return True
    v = str(value).strip()
    return v.startswith("<") or v.endswith(">") and v.count("<") >= 1


def conn_vars(connection: str, variables: dict[str, str]) -> dict[str, str]:
    prefix = CONNECTION_PREFIX.get(connection)
    if not prefix:
        raise ValueError(
            f"connection desconocida: {connection!r}. "
            f"Usa: {', '.join(CONNECTION_PREFIX)}"
        )
    return {
        "url": variables.get(f"{prefix}_URL", ""),
        "host": variables.get(f"{prefix}_HOST", ""),
        "port": variables.get(f"{prefix}_PORT", ""),
        "database": variables.get(f"{prefix}_DATABASE", ""),
        "username": variables.get(f"{prefix}_USERNAME", ""),
        "password": variables.get(f"{prefix}_PASSWORD", ""),
    }


def require_live_conn(connection: str, variables: dict[str, str]) -> dict[str, str]:
    cv = conn_vars(connection, variables)
    if is_placeholder(cv["host"]) or is_placeholder(cv["username"]) or is_placeholder(cv["password"]):
        raise ValueError(
            f"Credenciales placeholder para {connection}. "
            "Completa project-config.json / environments/."
        )
    return cv


def load_sources(root: Path, variables: dict[str, str]) -> list[dict]:
    path = root / "inputs.yaml"
    if not path.is_file():
        raise FileNotFoundError(
            f"No se encuentra {path}. Copia .agents/skills/oefa-hop-etl/inputs.example.yaml"
        )
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    sources = raw.get("sources") or []
    if not isinstance(sources, list):
        raise ValueError("inputs.yaml: 'sources' debe ser una lista")

    resolved: list[dict] = []
    for i, src in enumerate(sources):
        if not isinstance(src, dict):
            raise ValueError(f"inputs.yaml sources[{i}] no es un mapa")
        item = dict(src)
        for key, val in list(item.items()):
            if isinstance(val, str):
                item[key] = resolve_vars(val, variables)
        stg = item.get("stg_table")
        typ = item.get("type")
        if not stg or not typ:
            raise ValueError(f"inputs.yaml sources[{i}]: faltan stg_table y/o type")
        item["type"] = str(typ).lower().strip()
        item["stg_table"] = str(stg).strip().upper()
        resolved.append(item)
    return resolved
