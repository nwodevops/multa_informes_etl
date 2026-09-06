"""Fase 6–7 — carga TRUNCATE+INSERT del modelo dimensional e indicadores a Oracle BD_CURSOR."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from config import load_vars, project_root, require_live_conn

ESQUEMA = "APP"
DDL_DIR = "docs/lineamientos/ddl"
VISTAS_LEGACY = (
    "VW_FCT_INFORMES_VALIDADA",
    "VW_FCT_MC_ETAPAS_VALIDADA",
    "VW_FCT_MC_EXCEL_VALIDADA",
    "VW_FCT_MC_GAPP_VALIDADA",
    "VW_FCT_MC_SISUD_VALIDADA",
)
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
TABLAS_HECHOS = (
    "MI_FACT_MULTA_COERCITIVA",
    "MI_DET_ETAPA_MC",
)
REQUIRED_CORE = (*TABLAS_DIM, *TABLAS_HECHOS, "MI_DQ_HALLAZGO")
REQUIRED_TABLES = (*REQUIRED_CORE, "MI_INDICADOR_RESULTADO")
# Tablas pre-rename (sin prefijo MI_). Sus constraints chocan con el DDL nuevo (ORA-02264).
TABLAS_LEGACY = (
    "INDICADOR_RESULTADO",
    "DET_ETAPA_MC",
    "FACT_MULTA_COERCITIVA",
    "FACT_INFORME_SUPERVISION",
    "DIM_TIEMPO",
    "DIM_ADMINISTRADO",
    "DIM_ORGANO_UNIDAD",
    "DIM_MATERIA_SUBSECTOR",
    "DIM_ESTADO",
    "DIM_PARAMETRO_UIT",
    "DQ_HALLAZGO",
)
TRUNCATE_ORDEN = (
    "MI_INDICADOR_RESULTADO",
    "MI_DET_ETAPA_MC",
    "MI_FACT_MULTA_COERCITIVA",
    *TABLAS_DIM,
    "MI_DQ_HALLAZGO",
)
INSERT_ORDEN = (
    *TABLAS_DIM,
    "MI_FACT_MULTA_COERCITIVA",
    "MI_DET_ETAPA_MC",
    "MI_DQ_HALLAZGO",
    "MI_INDICADOR_RESULTADO",
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


def _verificar_post_carga(cur, counts: dict[str, int], cv: dict[str, str]) -> None:
    """Log explícito para cruzar con el cliente SQL (evita falso 'tabla vacía')."""
    dest = _destino_label(cv)
    print(f"DW: destino {dest}")
    for tabla in ("MI_FACT_MULTA_COERCITIVA", "MI_INDICADOR_RESULTADO"):
        if tabla not in counts:
            continue
        cur.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.{tabla}")
        n = int(cur.fetchone()[0])
        print(f"DW: POST-CARGA {ESQUEMA}.{tabla} = {n} filas (esperado {counts[tabla]})")
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
    """Tablespace con cuota (APP local suele tener USERS, no SYSTEM)."""
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
        try:
            cur.execute(stmt)
        except Exception as exc:
            msg = str(exc)
            if "ORA-00955" in msg or "ORA-01430" in msg or "ORA-02264" in msg:
                continue
            raise


def _model_complete(cur) -> bool:
    return all(_table_exists(cur, t) for t in REQUIRED_CORE)


def _indicadores_ready(cur) -> bool:
    return _table_exists(cur, "MI_INDICADOR_RESULTADO")


def _drop_table(cur, tabla: str) -> None:
    if not _table_exists(cur, tabla):
        return
    cur.execute(f"DROP TABLE {ESQUEMA}.{tabla} CASCADE CONSTRAINTS PURGE")
    print(f"DW: DROP TABLE {tabla}")


def _drop_model_tables(cur) -> None:
    for tabla in TRUNCATE_ORDEN:
        _drop_table(cur, tabla)


def _drop_legacy_tables(cur) -> None:
    """Elimina modelo sin prefijo MI_ (rename). Evita ORA-02264 por constraints reutilizados."""
    dropped = False
    for tabla in TABLAS_LEGACY:
        if _table_exists(cur, tabla):
            _drop_table(cur, tabla)
            dropped = True
    if dropped:
        print("DW: tablas legacy (sin MI_) eliminadas")


def _table_exists(cur, tabla: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) FROM user_tables WHERE table_name = :1",
        [tabla.upper()],
    )
    return int(cur.fetchone()[0]) > 0


def _column_exists(cur, tabla: str, columna: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) FROM user_tab_columns WHERE table_name = :1 AND column_name = :2",
        [tabla.upper(), columna.upper()],
    )
    return int(cur.fetchone()[0]) > 0


def _constraint_exists(cur, tabla: str, constraint: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) FROM user_constraints WHERE table_name = :1 AND constraint_name = :2",
        [tabla.upper(), constraint.upper()],
    )
    return int(cur.fetchone()[0]) > 0


def _index_exists(cur, index: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) FROM user_indexes WHERE index_name = :1",
        [index.upper()],
    )
    return int(cur.fetchone()[0]) > 0


def _strip_informe_residuo(cur) -> None:
    """Quita rastro F3 (informes) del DW: tabla, FK, índice y columna ID_INFORME."""
    if _constraint_exists(cur, "MI_FACT_MULTA_COERCITIVA", "FK_MI_FMC_INFORME"):
        cur.execute(f"ALTER TABLE {ESQUEMA}.MI_FACT_MULTA_COERCITIVA DROP CONSTRAINT FK_MI_FMC_INFORME")
        print("DW: DROP CONSTRAINT FK_MI_FMC_INFORME")
    _drop_table(cur, "MI_FACT_INFORME_SUPERVISION")
    if _table_exists(cur, "MI_FACT_MULTA_COERCITIVA") and _column_exists(
        cur, "MI_FACT_MULTA_COERCITIVA", "ID_INFORME"
    ):
        if _index_exists(cur, "IX_FMC_INFORME"):
            cur.execute(f"DROP INDEX {ESQUEMA}.IX_FMC_INFORME")
            print("DW: DROP INDEX IX_FMC_INFORME")
        cur.execute(f"ALTER TABLE {ESQUEMA}.MI_FACT_MULTA_COERCITIVA DROP COLUMN ID_INFORME")
        print("DW: DROP COLUMN MI_FACT_MULTA_COERCITIVA.ID_INFORME")


def _ensure_dim_od(cur, tablespace: str | None = None) -> None:
    """Crea MI_DIM_OD si el esquema ya existía sin esa dimensión."""
    if _table_exists(cur, "MI_DIM_OD"):
        return
    stmt = """
        CREATE TABLE MI_DIM_OD (
            ID_OD                 NUMBER         GENERATED BY DEFAULT ON NULL AS IDENTITY
                                                  (START WITH 1 INCREMENT BY 1),
            COD_OD                VARCHAR2(30)   NOT NULL,
            NOMBRE                VARCHAR2(100)  NOT NULL,
            TIPO                  VARCHAR2(20)   NOT NULL,
            ORDEN                 NUMBER(3),
            FECHA_ACTUALIZACION   DATE           DEFAULT SYSDATE,
            CONSTRAINT PK_MI_DIM_OD PRIMARY KEY (ID_OD),
            CONSTRAINT UQ_MI_DIM_OD_COD UNIQUE (COD_OD),
            CONSTRAINT CK_MI_DIM_OD_TIPO CHECK (TIPO IN ('OD','ODES','UNIDAD','NO ESPECIFICADO'))
        )
    """
    if tablespace:
        stmt = _inject_tablespace(stmt, tablespace)
    cur.execute(stmt)
    cur.execute(
        """
        INSERT INTO MI_DIM_OD (ID_OD, COD_OD, NOMBRE, TIPO, ORDEN)
        VALUES (-1, 'ND', 'NO ESPECIFICADO', 'NO ESPECIFICADO', NULL)
        """
    )
    print("DW: CREATE TABLE MI_DIM_OD")


def _ensure_fact_id_od(cur) -> None:
    """Añade ID_OD + FK al hecho si falta (esquema previo a familia OD)."""
    if not _table_exists(cur, "MI_FACT_MULTA_COERCITIVA"):
        return
    if not _column_exists(cur, "MI_FACT_MULTA_COERCITIVA", "ID_OD"):
        cur.execute(
            f"ALTER TABLE {ESQUEMA}.MI_FACT_MULTA_COERCITIVA "
            "ADD ID_OD NUMBER DEFAULT -1 NOT NULL"
        )
        print("DW: ADD COLUMN MI_FACT_MULTA_COERCITIVA.ID_OD")
    if _table_exists(cur, "MI_DIM_OD") and not _constraint_exists(
        cur, "MI_FACT_MULTA_COERCITIVA", "FK_MI_FMC_OD"
    ):
        cur.execute(
            f"ALTER TABLE {ESQUEMA}.MI_FACT_MULTA_COERCITIVA "
            f"ADD CONSTRAINT FK_MI_FMC_OD FOREIGN KEY (ID_OD) "
            f"REFERENCES {ESQUEMA}.MI_DIM_OD (ID_OD)"
        )
        print("DW: ADD CONSTRAINT FK_MI_FMC_OD")
    if not _index_exists(cur, "IX_FMC_OD"):
        cur.execute(f"CREATE INDEX {ESQUEMA}.IX_FMC_OD ON {ESQUEMA}.MI_FACT_MULTA_COERCITIVA (ID_OD)")
        print("DW: CREATE INDEX IX_FMC_OD")


def _ensure_fuente_ck_od_sheets(cur) -> None:
    """Alinea CK de FUENTE_REGISTRO a OD_SHEETS (migra OD_EXCEL/LAM_OD)."""
    if not _table_exists(cur, "MI_FACT_MULTA_COERCITIVA"):
        return
    if _constraint_exists(cur, "MI_FACT_MULTA_COERCITIVA", "CK_MI_FMC_FUENTE"):
        cur.execute(
            f"ALTER TABLE {ESQUEMA}.MI_FACT_MULTA_COERCITIVA DROP CONSTRAINT CK_MI_FMC_FUENTE"
        )
    cur.execute(
        f"UPDATE {ESQUEMA}.MI_FACT_MULTA_COERCITIVA "
        "SET FUENTE_REGISTRO = 'OD_SHEETS' "
        "WHERE FUENTE_REGISTRO IN ('LAM_OD','OD_EXCEL')"
    )
    cur.execute(
        f"""
        ALTER TABLE {ESQUEMA}.MI_FACT_MULTA_COERCITIVA
        ADD CONSTRAINT CK_MI_FMC_FUENTE
        CHECK (FUENTE_REGISTRO IN ('OD_SHEETS','OD_EXCEL','CAGR','GAPPS','SISUD_VW'))
        """
    )
    print("DW: CK_MI_FMC_FUENTE -> OD_SHEETS")


def _ensure_dim_organo_descripcion(cur) -> None:
    """Añade DESCRIPCION a MI_DIM_ORGANO_UNIDAD si el esquema es anterior a F2 CSEP."""
    if not _table_exists(cur, "MI_DIM_ORGANO_UNIDAD"):
        return
    if not _column_exists(cur, "MI_DIM_ORGANO_UNIDAD", "DESCRIPCION"):
        cur.execute(
            f"ALTER TABLE {ESQUEMA}.MI_DIM_ORGANO_UNIDAD "
            "ADD DESCRIPCION VARCHAR2(200)"
        )
        print("DW: ADD COLUMN MI_DIM_ORGANO_UNIDAD.DESCRIPCION")


def _ensure_dim_fuente(cur, tablespace: str | None = None) -> None:
    """Crea MI_DIM_FUENTE_REGISTRO si el esquema ya existía sin esa dimensión."""
    if _table_exists(cur, "MI_DIM_FUENTE_REGISTRO"):
        return
    stmt = """
        CREATE TABLE MI_DIM_FUENTE_REGISTRO (
            ID_FUENTE             NUMBER         GENERATED BY DEFAULT ON NULL AS IDENTITY
                                                  (START WITH 1 INCREMENT BY 1),
            CODIGO                VARCHAR2(20)   NOT NULL,
            NOMBRE                VARCHAR2(100)  NOT NULL,
            FAMILIA_TDR           VARCHAR2(10),
            DESCRIPCION           VARCHAR2(300),
            FECHA_ACTUALIZACION   DATE           DEFAULT SYSDATE,
            CONSTRAINT PK_MI_DIM_FUENTE PRIMARY KEY (ID_FUENTE),
            CONSTRAINT UQ_MI_DIM_FUENTE_COD UNIQUE (CODIGO)
        )
    """
    if tablespace:
        stmt = _inject_tablespace(stmt, tablespace)
    cur.execute(stmt)
    seeds = (
        (-1, "ND", "NO ESPECIFICADO", "ND", "NO ESPECIFICADO"),
        (1, "OD_SHEETS", "Sheets OD", "F1", "31 Google Sheets OD → STG_GS2_OD_MULTAS"),
        (2, "CAGR", "Sheets CSEP", "F2", "10 Google Sheets CSEP → STG_GS1_CSEP_MULTAS / ETAPAS"),
        (3, "GAPPS", "MySQL GAPP", "F4", "gappsdb.T_MVC_MULTACOERCITIVA_MC → STG_MYSQL_*"),
        (4, "SISUD_VW", "Oracle SISUD", "F5", "SISUD.VW_MULTA_COERCITIVA → STG_ORA_*"),
        (5, "OD_EXCEL", "Excel OD (legacy)", "F1", "Alias histórico; el ETL normaliza a OD_SHEETS"),
    )
    for row in seeds:
        cur.execute(
            f"""
            INSERT INTO {ESQUEMA}.MI_DIM_FUENTE_REGISTRO
                (ID_FUENTE, CODIGO, NOMBRE, FAMILIA_TDR, DESCRIPCION)
            VALUES (:1, :2, :3, :4, :5)
            """,
            row,
        )
    print("DW: CREATE TABLE MI_DIM_FUENTE_REGISTRO")


def _ensure_fact_id_fuente(cur) -> None:
    """Añade ID_FUENTE + FK al hecho y al detalle etapas si faltan."""
    if _table_exists(cur, "MI_FACT_MULTA_COERCITIVA"):
        if not _column_exists(cur, "MI_FACT_MULTA_COERCITIVA", "ID_FUENTE"):
            cur.execute(
                f"ALTER TABLE {ESQUEMA}.MI_FACT_MULTA_COERCITIVA "
                "ADD ID_FUENTE NUMBER DEFAULT -1 NOT NULL"
            )
            print("DW: ADD COLUMN MI_FACT_MULTA_COERCITIVA.ID_FUENTE")
        if _table_exists(cur, "MI_DIM_FUENTE_REGISTRO") and not _constraint_exists(
            cur, "MI_FACT_MULTA_COERCITIVA", "FK_MI_FMC_FUENTE"
        ):
            cur.execute(
                f"ALTER TABLE {ESQUEMA}.MI_FACT_MULTA_COERCITIVA "
                f"ADD CONSTRAINT FK_MI_FMC_FUENTE FOREIGN KEY (ID_FUENTE) "
                f"REFERENCES {ESQUEMA}.MI_DIM_FUENTE_REGISTRO (ID_FUENTE)"
            )
            print("DW: ADD CONSTRAINT FK_MI_FMC_FUENTE")
        if not _index_exists(cur, "IX_FMC_FUENTE"):
            cur.execute(
                f"CREATE INDEX {ESQUEMA}.IX_FMC_FUENTE "
                f"ON {ESQUEMA}.MI_FACT_MULTA_COERCITIVA (ID_FUENTE)"
            )
            print("DW: CREATE INDEX IX_FMC_FUENTE")

    if _table_exists(cur, "MI_DET_ETAPA_MC"):
        if not _column_exists(cur, "MI_DET_ETAPA_MC", "ID_FUENTE"):
            cur.execute(
                f"ALTER TABLE {ESQUEMA}.MI_DET_ETAPA_MC "
                "ADD ID_FUENTE NUMBER DEFAULT 2 NOT NULL"
            )
            print("DW: ADD COLUMN MI_DET_ETAPA_MC.ID_FUENTE")
        if _table_exists(cur, "MI_DIM_FUENTE_REGISTRO") and not _constraint_exists(
            cur, "MI_DET_ETAPA_MC", "FK_MI_DETAPA_FUENTE"
        ):
            cur.execute(
                f"ALTER TABLE {ESQUEMA}.MI_DET_ETAPA_MC "
                f"ADD CONSTRAINT FK_MI_DETAPA_FUENTE FOREIGN KEY (ID_FUENTE) "
                f"REFERENCES {ESQUEMA}.MI_DIM_FUENTE_REGISTRO (ID_FUENTE)"
            )
            print("DW: ADD CONSTRAINT FK_MI_DETAPA_FUENTE")
        if not _index_exists(cur, "IX_DETAPA_FUENTE"):
            cur.execute(
                f"CREATE INDEX {ESQUEMA}.IX_DETAPA_FUENTE "
                f"ON {ESQUEMA}.MI_DET_ETAPA_MC (ID_FUENTE)"
            )
            print("DW: CREATE INDEX IX_DETAPA_FUENTE")


def _prepare_schema(cur, root: Path) -> None:
    for v in VISTAS_LEGACY:
        try:
            cur.execute(f"DROP VIEW {ESQUEMA}.{v}")
            print(f"DW: DROP VIEW {v}")
        except Exception as exc:
            if "ORA-00942" not in str(exc):
                print(f"AVISO: DROP VIEW {v}: {exc}")

    _strip_informe_residuo(cur)

    ddl_root = root / DDL_DIR
    ts = _user_tablespace(cur)
    _ensure_dim_od(cur, ts)
    _ensure_fact_id_od(cur)
    _ensure_fuente_ck_od_sheets(cur)
    _ensure_dim_organo_descripcion(cur)
    _ensure_dim_fuente(cur, ts)
    _ensure_fact_id_fuente(cur)

    if not _model_complete(cur):
        _drop_legacy_tables(cur)
        if any(_table_exists(cur, t) for t in REQUIRED_CORE):
            print("DW: esquema incompleto -> eliminar tablas parciales")
            _drop_model_tables(cur)
        print(f"DW: aplicando DDL formal (01, 02, 03, 04) en TABLESPACE {ts}...")
        _run_ddl_file(cur, ddl_root / "01_dimensiones.sql", ts)
        _run_ddl_file(cur, ddl_root / "02_hechos.sql", ts)
        _run_ddl_file(cur, ddl_root / "03_bitacora.sql", ts)
        _run_ddl_file(cur, ddl_root / "04_indicadores.sql", ts)
    elif _table_exists(cur, "MI_DQ_HALLAZGO") and not _column_exists(cur, "MI_DQ_HALLAZGO", "ID_HALLAZGO"):
        print("DW: DROP MI_DQ_HALLAZGO (esquema legacy VARCHAR) -> recrear")
        cur.execute(f"DROP TABLE {ESQUEMA}.MI_DQ_HALLAZGO PURGE")
        _run_ddl_file(cur, ddl_root / "03_bitacora.sql", ts)
        if not _indicadores_ready(cur):
            _run_ddl_file(cur, ddl_root / "04_indicadores.sql", ts)
    elif not _table_exists(cur, "MI_DQ_HALLAZGO"):
        _run_ddl_file(cur, ddl_root / "03_bitacora.sql", ts)
        if not _indicadores_ready(cur):
            _run_ddl_file(cur, ddl_root / "04_indicadores.sql", ts)
    elif not _indicadores_ready(cur):
        print("DW: aplicando DDL indicadores (04)...")
        _run_ddl_file(cur, ddl_root / "04_indicadores.sql", ts)


def _apply_column_comments(cur, root: Path) -> None:
    """COMMENT ON TABLE/COLUMN (05). Idempotente; aplica en APP o REPOCSEP según USER."""
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


def _table_columns(cur, tabla: str) -> list[str]:
    return list(_column_meta(cur, tabla).keys())


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
        return v if data_type == "DATE" else v
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


def _cell(v, data_type: str = "VARCHAR2", varchar_limit: int | None = None):
    return _coerce_for_oracle(v, data_type, varchar_limit)


def _insert_df(cur, tabla: str, df: pd.DataFrame, skip_identity: bool = True) -> int:
    if df.empty and tabla != "MI_DQ_HALLAZGO":
        cur.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.{tabla}")
        return int(cur.fetchone()[0])
    meta = _column_meta(cur, tabla)
    ora_cols = list(meta.keys())
    if skip_identity:
        ora_cols = [c for c in ora_cols if c not in ("ID_HALLAZGO", "ID_RESULTADO")]
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
            cells.append(_cell(v, dtype, lim))
        rows.append(tuple(cells))
    if rows:
        cur.executemany(
            f"INSERT INTO {ESQUEMA}.{tabla} ({col_list}) VALUES ({binds})",
            rows,
        )
    cur.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.{tabla}")
    return int(cur.fetchone()[0])


def cargar_dw(tablas: dict[str, pd.DataFrame], root: Path | None = None) -> dict[str, int]:
    """TRUNCATE + INSERT del modelo lineamiento. Devuelve COUNT por tabla."""
    root = root or project_root()
    if not tablas:
        print("AVISO: no hay tablas para cargar a BD_CURSOR.")
        return {}

    conn, cv = _connect(root)

    counts: dict[str, int] = {}
    try:
        cur = conn.cursor()
        try:
            _prepare_schema(cur, root)
            _apply_column_comments(cur, root)
            conn.commit()

            for tabla in TRUNCATE_ORDEN:
                if _table_exists(cur, tabla):
                    cur.execute(f"TRUNCATE TABLE {ESQUEMA}.{tabla}")
                    print(f"DW: TRUNCATE {tabla}")

            for tabla in INSERT_ORDEN:
                df = tablas.get(tabla)
                if df is None:
                    continue
                n_df = len(df)
                n_bd = _insert_df(
                    cur,
                    tabla,
                    df,
                    skip_identity=(tabla in ("MI_DQ_HALLAZGO", "MI_INDICADOR_RESULTADO")),
                )
                conn.commit()
                counts[tabla] = n_bd
                ok = "OK" if n_bd == n_df or (tabla == "MI_DQ_HALLAZGO" and n_bd >= n_df) else "REVISAR"
                print(f"DW: {tabla}: {n_df} filas -> {n_bd} en BD ({ok})")
            _verificar_post_carga(cur, counts, cv)
            conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()
    return counts
