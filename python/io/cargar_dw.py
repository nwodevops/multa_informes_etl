"""Carga Oracle DW canónica — invocada por python/main.py tras logica/.

Orden:
  1) wipe DW_M_*/VW_* del esquema sesión (APP local / REPOCSEP remote)
  2) DDL 01_dimensiones + 02_hechos (+ DW_M_DQ_HALLAZGO)
  3) INSERT dims + DW_M_FACT_MULTA_COERCITIVA + DET + DQ

No publica facts evidencia FACT_MC_*, DW_M_QA_*, indicadores K ni vistas VW_MC_*.
DW_M_AUD_* lo carga python/audit/cargar_aud.py después (también desde main.py).

DDL: docs/lineamientos/ddl/
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from config import load_vars, project_root, require_live_conn

# Local suele ser APP; remote Win es REPOCSEP. En runtime se alinea a USER.
ESQUEMA_DEFAULT = "APP"
ESQUEMA = ESQUEMA_DEFAULT
DDL_DIR = "docs/lineamientos/ddl"

# --- Catálogo de objetos del modelo canónico ---
TABLAS_DIM = (
    "DW_M_DIM_TIEMPO",
    "DW_M_DIM_ADMINISTRADO",
    "DW_M_DIM_ORGANO_UNIDAD",
    "DW_M_DIM_OD",
    "DW_M_DIM_FUENTE_REGISTRO",
    "DW_M_DIM_MATERIA_SUBSECTOR",
    "DW_M_DIM_ESTADO",
    "DW_M_DIM_PARAMETRO_UIT",
)
TABLAS_HECHOS = (
    "DW_M_FACT_MULTA_COERCITIVA",
    "DW_M_DET_ETAPA_MC",
)
REQUIRED_CORE = (*TABLAS_DIM, *TABLAS_HECHOS)
# Hijos primero; leftover DW_M_% (AUD, FACT_MC_* viejos, DQ, …) se dropea después.
DROP_ORDEN = (
    "DW_M_DET_ETAPA_MC",
    "DW_M_FACT_MULTA_COERCITIVA",
    *TABLAS_DIM,
)
INSERT_ORDEN = (
    *TABLAS_DIM,
    "DW_M_FACT_MULTA_COERCITIVA",
    "DW_M_DET_ETAPA_MC",
    "DW_M_DQ_HALLAZGO",
)


def _connect(root: Path):
    """Conexión oracledb al destino DW (connection id Hop: oracle_dw)."""
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
        print(f"DW: esquema sesión = {ESQUEMA} (no {ESQUEMA_DEFAULT})", flush=True)
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
    print(f"DW: destino {dest}", flush=True)
    for tabla in (
        "DW_M_FACT_MULTA_COERCITIVA",
        "DW_M_DET_ETAPA_MC",
        "DW_M_DQ_HALLAZGO",
    ):
        if tabla not in counts and not _table_exists(cur, tabla):
            continue
        cur.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.{tabla}")
        n = int(cur.fetchone()[0])
        esp = counts.get(tabla, "?")
        print(f"DW: POST-CARGA {ESQUEMA}.{tabla} = {n} filas (esperado {esp})", flush=True)


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
    print(f"DW: DROP TABLE {tabla}", flush=True)


def _drop_model(cur) -> None:
    """Wipe canónico: todas VW_MC_/VW_FCT_ y todas DW_M_* (incl. AUD/DQ/QA legacy)."""
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
            print(f"DW: DROP VIEW {nombre}", flush=True)
        except Exception as exc:
            if "ORA-00942" not in str(exc):
                raise
            print(f"AVISO: DROP VIEW {nombre}: {exc}", flush=True)

    cur.execute("SELECT table_name FROM user_tables WHERE table_name LIKE 'DW_M_%'")
    existentes = {r[0] for r in cur.fetchall()}
    for tabla in DROP_ORDEN:
        if tabla in existentes:
            _drop_table(cur, tabla)
            existentes.discard(tabla)
    for tabla in sorted(existentes):
        _drop_table(cur, tabla)


def _run_dq_hallazgo_ddl(cur, root: Path, tablespace: str | None = None) -> None:
    """Aplica solo DW_M_DQ_HALLAZGO (+ índices) desde 03_bitacora.sql; omite DW_M_QA_*."""
    path = root / DDL_DIR / "03_bitacora.sql"
    if not path.is_file():
        raise FileNotFoundError(path)
    print("DW: aplicando DW_M_DQ_HALLAZGO (03 filtrado, sin DW_M_QA_*)...", flush=True)
    for stmt in _split_sql(path.read_text(encoding="utf-8")):
        u = stmt.upper()
        if u.startswith("COMMIT") or not u.strip():
            continue
        if "DW_M_QA_AMARRE" in u:
            continue
        if "DW_M_DQ_HALLAZGO" not in u and "IX_DQ_" not in u:
            continue
        if tablespace:
            stmt = _inject_tablespace(stmt, tablespace)
        cur.execute(stmt)


def _prepare_schema(cur, root: Path) -> None:
    """Wipe total → CREATE estrella (01+02) + DW_M_DQ_HALLAZGO. Sin QA/KPIs/vistas."""
    ddl_root = root / DDL_DIR
    ts = _user_tablespace(cur)
    print(
        f"DW: wipe canónico DW_M_*/VW_* → DDL 01+02+DQ (TABLESPACE {ts})...",
        flush=True,
    )
    _drop_model(cur)
    for name in ("01_dimensiones.sql", "02_hechos.sql"):
        print(f"DW: aplicando {name}...", flush=True)
        _run_ddl_file(cur, ddl_root / name, ts)
    _run_dq_hallazgo_ddl(cur, root, ts)


def _apply_column_comments(cur, root: Path) -> None:
    if not _model_complete(cur):
        return
    path = root / DDL_DIR / "05_comentarios.sql"
    if not path.is_file():
        return
    print("DW: aplicando comentarios de tablas/columnas (05)...", flush=True)
    # 05 puede referenciar DQ/vistas; ignorar ORA de objetos inexistentes
    for stmt in _split_sql(path.read_text(encoding="utf-8")):
        if stmt.upper().startswith("COMMIT") or not stmt.strip():
            continue
        try:
            cur.execute(stmt)
        except Exception as exc:
            msg = str(exc)
            if any(x in msg for x in ("ORA-00942", "ORA-04043", "ORA-02289")):
                continue
            raise


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
    del skip_identity  # API estable; IDs vienen del DF (BY DEFAULT ON NULL).
    if df.empty:
        cur.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.{tabla}")
        return int(cur.fetchone()[0])
    meta = _column_meta(cur, tabla)
    ora_cols = list(meta.keys())
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
    """Wipe + DDL + INSERT dims/enriquecida/DET/DQ. Sin facts evidencia ni SQL 07."""
    root = root or project_root()
    if not tablas:
        print("AVISO: no hay tablas para cargar a BD_CURSOR.", flush=True)
        return {}

    # STEP 7.1: abrir Oracle y alinear el esquema con el usuario de la sesión.
    conn, cv = _connect(root)
    counts: dict[str, int] = {}
    try:
        cur = conn.cursor()
        try:
            _bind_schema(cur)
            # STEP 7.2: limpiar objetos DW_M_*/VW_* y recrear estrella + DQ.
            _prepare_schema(cur, root)
            _apply_column_comments(cur, root)
            conn.commit()

            # STEP 7.3: insertar dims, fact enriquecido, DET y DQ (orden FK).
            for tabla in INSERT_ORDEN:
                df = tablas.get(tabla)
                if df is None:
                    continue
                n_df = len(df)
                n_bd = _insert_df(cur, tabla, df, skip_identity=True)
                conn.commit()
                counts[tabla] = n_bd
                ok = "OK" if n_bd == n_df else "REVISAR"
                print(f"DW: {tabla}: {n_df} filas -> {n_bd} en BD ({ok})", flush=True)

            # STEP 7.4: comparar conteos esperados contra lo persistido en Oracle.
            _verificar_post_carga(cur, counts, cv)
            conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()
    return counts
