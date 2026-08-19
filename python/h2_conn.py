"""JDBC a H2 mem:csep. Compartido: capa STG (CREATE) y capa lógica (SELECT).

No hay reglas de negocio ni introspección aquí.
"""

from __future__ import annotations

from pathlib import Path

H2_DRIVER = "org.h2.Driver"


def find_h2_jar(root: Path) -> Path:
    lib = root / "h2" / "lib"
    jars = sorted(lib.glob("h2-*.jar"))
    if jars:
        return jars[0]
    fallback = lib / "h2.jar"
    if fallback.is_file():
        return fallback
    raise FileNotFoundError(f"No se encuentra h2-*.jar en {lib}")


def connect_h2(root: Path, variables: dict[str, str]):
    """Conexión JDBC a H2 mem:csep. El caller cierra el conn."""
    try:
        import jaydebeapi
    except ImportError as exc:
        raise SystemExit(
            "Falta jaydebeapi. Instala: pip install -r python/requirements.txt"
        ) from exc

    url = variables.get("DB_H2_URL") or ""
    user = variables.get("DB_H2_USERNAME") or "sa"
    password = variables.get("DB_H2_PASSWORD") or "csep"
    if not url:
        raise ValueError("DB_H2_URL vacía en project-config.json")

    jar = str(find_h2_jar(root))
    return jaydebeapi.connect(H2_DRIVER, url, [user, password], jar)
