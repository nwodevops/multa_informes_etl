"""Carga Oracle DW: wipe MI_*/VW_* → DDL canónico → INSERT → enrich 07."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from config import load_vars, project_root, require_live_conn

# Local suele ser APP; remote Win es REPOCSEP. En runtime se alinea a USER.
ESQUEMA_DEFAULT = "APP"
ESQUEMA = ESQUEMA_DEFAULT
DDL_DIR = "docs/lineamientos/ddl"

TABLAS_DIM = (
    "MI_DIM_TIEMPO",
    "MI_DIM_ADMINISTRADO",
    "MI_DIM_ORGANO_UNIDAD",
    "MI_DIM_OD",
    "MI_DIM_FUENTE_REGISTRO",
    "MI_DIM_MATERIA_SUBSECTOR",
    "MI_DIM_ESTADO",
    "MI_DIM_PARAMETRO_UIT",
)
TABLAS_EVIDENCIA = (
    "MI_FACT_MC_CSEP",
    "MI_FACT_MC_OD",
    "MI_FACT_MC_SISUD",
)
TABLAS_HECHOS = (
    *TABLAS_EVIDENCIA,
    "MI_FACT_MULTA_COERCITIVA",
    "MI_DET_ETAPA_MC",
)
TABLAS_QA = (
    "MI_QA_AMARRE",
    "MI_QA_AMARRE_DETALLE",
)
REQUIRED_CORE = (*TABLAS_DIM, *TABLAS_HECHOS, "MI_DQ_HALLAZGO", *TABLAS_QA)
# Orden DROP/hijos primero (también usado si quedan MI_% sueltos).
DROP_ORDEN = (
    "MI_INDICADOR_RESULTADO",
    "MI_DET_ETAPA_MC",
    "MI_FACT_MULTA_COERCITIVA",
    *TABLAS_EVIDENCIA,
    *TABLAS_QA,
    "MI_DQ_HALLAZGO",
    *TABLAS_DIM,
)
INSERT_ORDEN = (
    *TABLAS_DIM,
    *TABLAS_EVIDENCIA,
    "MI_DET_ETAPA_MC",
    "MI_DQ_HALLAZGO",
    *TABLAS_QA,
    "MI_INDICADOR_RESULTADO",
    # MI_FACT_MULTA_COERCITIVA lo llena 07_enrich_sheets_sisud.sql
)
IDENTITY_SKIP = frozenset(
    {
        "MI_DQ_HALLAZGO",
        "MI_INDICADOR_RESULTADO",
        "MI_QA_AMARRE",
        "MI_QA_AMARRE_DETALLE",
    }
)


def _connect(root: Path):
    variables = load_vars(root)
    cv = require_live_conn("oracle_dw", variables)
    try:
        import oracledb
    except ImportError as exc:
        raise SystemExit("Falta oracledb. Instala: pip install -r python/requirements.txt") from exc
    dsn = oracledb.makedsn(cv["host"], int(cv["port"] or "1521"), service_name=cv["database"])
    conn = oracledb.connect(user=cv["username"], password=cv["password"], dsn=dsn)
    return conn, cv


def _destino_label(cv: dict[str, str]) -> str:
    return f"{cv['username']}@{cv['host']}:{cv['port']}/{cv['database']} esquema {ESQUEMA}"


def _bind_schema(cur) -> str:
    """Alinea ESQUEMA al USER de la sesión (APP local / REPOCSEP remote)."""
    global ESQUEMA
    cur.execute("SELECT USER FROM DUAL")
    ESQUEMA = str(cur.fetchone()[0])
    if ESQUEMA.upper() != ESQUEMA_DEFAULT.upper():
        print(f"DW: esquema sesión = {ESQUEMA} (no {ESQUEMA_DEFAULT})")
    return ESQUEMA


def _table_exists(cur, tabla: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) FROM user_tables WHERE table_name = :1",
        [tabla.upper()],
    )
    return int(cur.fetchone()[0]) > 0


def _model_complete(cur) -> bool:
    return all(_table_exists(cur, t) for t in REQUIRED_CORE)


def _verificar_post_carga(cur, counts: dict[str, int], cv: dict[str, str]) -> None:
    dest = _destino_label(cv)
    print(f"DW: destino {dest}")
    for tabla in (*TABLAS_EVIDENCIA, "MI_FACT_MULTA_COERCITIVA", "MI_INDICADOR_RESULTADO"):
        if tabla not in counts and not _table_exists(cur, tabla):
            continue
        cur.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.{tabla}")
        n = int(cur.fetchone()[0])
        esp = counts.get(tabla, "?")
        print(f"DW: POST-CARGA {ESQUEMA}.{tabla} = {n} filas (esperado {esp})")
    n_c = counts.get("MI_FACT_MC_CSEP", 0)
    n_o = counts.get("MI_FACT_MC_OD", 0)
    n_m = counts.get("MI_FACT_MULTA_COERCITIVA", 0)
    if (n_c + n_o) and n_m != (n_c + n_o):
        print(f"AVISO enriquecida: {n_m} != CSEP+OD ({n_c}+{n_o})")
    if "MI_INDICADOR_RESULTADO" in counts:
        cur.execute(
            f"SELECT DISTINCT COD_INDICADOR FROM {ESQUEMA}.MI_INDICADOR_RESULTADO ORDER BY 1"
        )
        codes = [r[0] for r in cur.fetchall()]
        print(f"DW: indicadores presentes: {', '.join(codes) or '(ninguno)'}")
        print(
            f"DW: verificar en SQL*Plus/SQL Developer con la MISMA conexión ({dest}): "
            f"SELECT COUNT(*) FROM {ESQUEMA}.MI_INDICADOR_RESULTADO;"
        )


def _split_sql(text: str) -> list[str]:
    stmts = []
    buf: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("--"):
            continue
        buf.append(line)
        if s.rstrip().endswith(";"):
            stmt = "\n".join(buf).rstrip().rstrip(";").strip()
            if stmt:
                stmts.append(stmt)
            buf = []
    if buf:
        stmt = "\n".join(buf).strip()
        if stmt:
            stmts.append(stmt)
    return stmts


def _user_tablespace(cur) -> str:
    cur.execute(
        """
        SELECT tablespace_name FROM user_ts_quotas
        WHERE max_bytes = -1 OR bytes > 0
        ORDER BY CASE WHEN tablespace_name = 'USERS' THEN 0 ELSE 1 END, tablespace_name
        """
    )
    rows = [r[0] for r in cur.fetchall()]
    return rows[0] if rows else "USERS"


def _inject_tablespace(stmt: str, tablespace: str) -> str:
    u = stmt.strip().upper()
    if "TABLESPACE" in u:
        return stmt
    if u.startswith(("CREATE TABLE", "CREATE UNIQUE INDEX", "CREATE INDEX")):
        s = stmt.rstrip()
        if s.endswith(";"):
            return s[:-1] + f" TABLESPACE {tablespace};"
        return s + f" TABLESPACE {tablespace}"
    return stmt


def _run_ddl_file(cur, path: Path, tablespace: str | None = None) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    for stmt in _split_sql(path.read_text(encoding="utf-8")):
        if stmt.upper().startswith("COMMIT"):
            continue
        if stmt.upper().startswith("INSERT INTO"):
            continue
        if tablespace:
            stmt = _inject_tablespace(stmt, tablespace)
        cur.execute(stmt)


def _drop_table(cur, tabla: str) -> None:
    if not _table_exists(cur, tabla):
        return
    cur.execute(f"DROP TABLE {ESQUEMA}.{tabla} CASCADE CONSTRAINTS PURGE")
    print(f"DW: DROP TABLE {tabla}")


def _drop_model(cur) -> None:
    """Borra vistas VW_MC_/VW_FCT_ y tablas MI_* del usuario actual."""
    cur.execute(
        """
        SELECT view_name FROM user_views
        WHERE view_name LIKE 'VW_MC_%' OR view_name LIKE 'VW_FCT_%'
        ORDER BY view_name
        """
    )
    for (nombre,) in cur.fetchall():
        try:
            cur.execute(f"DROP VIEW {ESQUEMA}.{nombre}")
            print(f"DW: DROP VIEW {nombre}")
        except Exception as exc:
            if "ORA-00942" not in str(exc):
                raise
            print(f"AVISO: DROP VIEW {nombre}: {exc}")

    cur.execute(
        "SELECT table_name FROM user_tables WHERE table_name LIKE 'MI_%'"
    )
    existentes = {r[0] for r in cur.fetchall()}
    for tabla in DROP_ORDEN:
        if tabla in existentes:
            _drop_table(cur, tabla)
            existentes.discard(tabla)
    for tabla in sorted(existentes):
        _drop_table(cur, tabla)


def _prepare_schema(cur, root: Path) -> None:
    """Wipe modelo → CREATE desde DDL 01–04 + vistas 06."""
    ddl_root = root / DDL_DIR
    ts = _user_tablespace(cur)
    print(f"DW: wipe modelo MI_*/VW_* y recrear DDL (TABLESPACE {ts})...")
    _drop_model(cur)
    for name in (
        "01_dimensiones.sql",
        "02_hechos.sql",
        "03_bitacora.sql",
        "04_indicadores.sql",
    ):
        print(f"DW: aplicando {name}...")
        _run_ddl_file(cur, ddl_root / name, ts)
    vistas = ddl_root / "06_vistas.sql"
    if vistas.is_file():
        print("DW: aplicando vistas VW_MC_* (06)...")
        _run_ddl_file(cur, vistas)


def _run_enrich_sheets_sisud(cur, root: Path) -> int:
    """DELETE+INSERT hecho enriquecido (07_enrich_sheets_sisud.sql)."""
    path = (root / DDL_DIR / "07_enrich_sheets_sisud.sql").resolve()
    print(f"DW: enrich busca {path}", flush=True)
    if not path.is_file():
        ddl_dir = path.parent
        listing = sorted(p.name for p in ddl_dir.glob("*")) if ddl_dir.is_dir() else []
        raise FileNotFoundError(
            f"falta {path} (en {ddl_dir}: {', '.join(listing) or 'vacío/inexistente'})"
        )
    if not all(_table_exists(cur, t) for t in TABLAS_EVIDENCIA):
        raise RuntimeError("faltan facts evidencia para enrich Sheets-SISUD")
    if not _table_exists(cur, "MI_FACT_MULTA_COERCITIVA"):
        raise RuntimeError("falta MI_FACT_MULTA_COERCITIVA")
    print("DW: aplicando enrich Sheets-SISUD (07)...", flush=True)
    try:
        for stmt in _split_sql(path.read_text(encoding="utf-8")):
            u = stmt.upper().strip()
            if u.startswith("COMMIT") or not u:
                continue
            cur.execute(stmt)
    except Exception as exc:
        print(f"ERROR enrich 07: {exc}", flush=True)
        raise RuntimeError(f"falló enrich Sheets-SISUD (07): {exc}") from exc
    cur.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.MI_FACT_MULTA_COERCITIVA")
    n = int(cur.fetchone()[0])
    cur.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.MI_FACT_MC_CSEP")
    n_c = int(cur.fetchone()[0])
    cur.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.MI_FACT_MC_OD")
    n_o = int(cur.fetchone()[0])
    print(
        f"DW: MI_FACT_MULTA_COERCITIVA (enriquecida): {n} filas "
        f"(esperado CSEP+OD={n_c}+{n_o}={n_c + n_o})",
        flush=True,
    )
    if (n_c + n_o) > 0 and n == 0:
        raise RuntimeError(
            "enrich 07 dejó MI_FACT_MULTA_COERCITIVA vacía pese a CSEP/OD con filas"
        )
    return n


def _apply_column_comments(cur, root: Path) -> None:
    if not _model_complete(cur):
        return
    path = root / DDL_DIR / "05_comentarios.sql"
    if not path.is_file():
        return
    print("DW: aplicando comentarios de tablas/columnas (05)...")
    _run_ddl_file(cur, path)


def _trunc_varchar(val: str, limit: int) -> str:
    if len(val.encode("utf-8")) <= limit:
        return val
    cut = val
    while cut and len(cut.encode("utf-8")) > limit:
        cut = cut[:-1]
    return cut


def _column_meta(cur, tabla: str) -> dict[str, tuple[str, int | None]]:
    cur.execute(
        """
        SELECT column_name, data_type, data_length
        FROM user_tab_columns
        WHERE table_name = :1
        ORDER BY column_id
        """,
        [tabla.upper()],
    )
    return {r[0]: (r[1], int(r[2]) if r[2] is not None else None) for r in cur.fetchall()}


def _coerce_for_oracle(v, data_type: str, varchar_limit: int | None):
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(v, pd.Timestamp):
        v = v.to_pydatetime()
    if isinstance(v, datetime):
        return v
    if data_type == "VARCHAR2":
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if isinstance(v, float) and v == int(v):
                v = int(v)
            s = str(v)
        elif not isinstance(v, (str, bytes)):
            s = str(v)
        else:
            s = v.decode("utf-8", errors="replace") if isinstance(v, bytes) else str(v)
        if varchar_limit is not None:
            s = _trunc_varchar(s, varchar_limit)
        return s[:4000]
    if data_type == "NUMBER":
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return None if pd.isna(v) else v
        if isinstance(v, str) and v.strip() == "":
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None
    if data_type == "DATE":
        if hasattr(v, "to_pydatetime"):
            try:
                return v.to_pydatetime()
            except Exception:
                pass
        if isinstance(v, datetime):
            return v
        try:
            ts = pd.Timestamp(v)
            if pd.isna(ts):
                return None
            return ts.to_pydatetime()
        except Exception:
            return None
    return v


def _insert_df(cur, tabla: str, df: pd.DataFrame, skip_identity: bool = True) -> int:
    if df.empty and tabla != "MI_DQ_HALLAZGO":
        cur.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.{tabla}")
        return int(cur.fetchone()[0])
    meta = _column_meta(cur, tabla)
    ora_cols = list(meta.keys())
    if skip_identity:
        ora_cols = [
            c
            for c in ora_cols
            if c not in ("ID_HALLAZGO", "ID_RESULTADO", "ID_AMARRE", "ID_DETALLE")
        ]
    df_cols = []
    for oc in ora_cols:
        match = None
        for dc in df.columns:
            if dc.upper() == oc:
                match = dc
                break
        df_cols.append(match)
    use_cols = [c for c, dc in zip(ora_cols, df_cols) if dc is not None]
    use_df_cols = [dc for dc in df_cols if dc is not None]
    if not use_cols:
        return 0
    binds = ", ".join(f":{i + 1}" for i in range(len(use_cols)))
    col_list = ", ".join(use_cols)
    rows = []
    for row in df[use_df_cols].itertuples(index=False, name=None):
        cells = []
        for v, col in zip(row, use_cols):
            dtype, vlen = meta[col]
            lim = vlen if dtype == "VARCHAR2" else None
            cells.append(_coerce_for_oracle(v, dtype, lim))
        rows.append(tuple(cells))
    if rows:
        cur.executemany(
            f"INSERT INTO {ESQUEMA}.{tabla} ({col_list}) VALUES ({binds})",
            rows,
        )
    cur.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.{tabla}")
    return int(cur.fetchone()[0])


def cargar_dw(tablas: dict[str, pd.DataFrame], root: Path | None = None) -> dict[str, int]:
    """Wipe + DDL + INSERT del modelo lineamiento. Devuelve COUNT por tabla."""
    root = root or project_root()
    if not tablas:
        print("AVISO: no hay tablas para cargar a BD_CURSOR.")
        return {}

    conn, cv = _connect(root)
    counts: dict[str, int] = {}
    try:
        cur = conn.cursor()
        try:
            _bind_schema(cur)
            _prepare_schema(cur, root)
            _apply_column_comments(cur, root)
            conn.commit()

            for tabla in INSERT_ORDEN:
                df = tablas.get(tabla)
                if df is None:
                    continue
                n_df = len(df)
                n_bd = _insert_df(
                    cur,
                    tabla,
                    df,
                    skip_identity=(tabla in IDENTITY_SKIP),
                )
                conn.commit()
                counts[tabla] = n_bd
                ok = "OK" if n_bd == n_df or (tabla == "MI_DQ_HALLAZGO" and n_bd >= n_df) else "REVISAR"
                print(f"DW: {tabla}: {n_df} filas -> {n_bd} en BD ({ok})")

            n_enriq = _run_enrich_sheets_sisud(cur, root)
            counts["MI_FACT_MULTA_COERCITIVA"] = n_enriq
            conn.commit()

            _verificar_post_carga(cur, counts, cv)
            conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()
    return counts
