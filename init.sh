#!/usr/bin/env bash
# Harness — verificación e inicialización del ETL (capa Python + staging Excel).
# Inspirado en https://github.com/nwoswo/ejemplo-harness-subagentes
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

fail() { echo -e "${RED}FAIL:${NC} $*" >&2; exit 1; }
warn() { echo -e "${YELLOW}AVISO:${NC} $*"; }
step() { echo -e "${GREEN}==>${NC} $*"; }

PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python

HOP_RUN="${HOP_RUN:-$HOME/apps/hop/hop-run.sh}"
HOP_PROJECT="$(basename "$ROOT")"
LOG="$(mktemp)"
trap 'rm -f "$LOG"' EXIT

step "Validando feature_list.json (máx. una in_progress)"
"$PY" - <<'PY'
import json
import sys
from pathlib import Path

path = Path("feature_list.json")
if not path.is_file():
    sys.exit("feature_list.json no encontrado")
data = json.loads(path.read_text(encoding="utf-8"))
active = [f for f in data.get("features", []) if f.get("status") == "in_progress"]
if len(active) > 1:
    names = ", ".join(f["id"] for f in active)
    sys.exit(f"más de una feature in_progress: {names}")
print(f"features: {len(data.get('features', []))}, in_progress: {len(active)}")
PY

step "Prerrequisitos (java, venv, inputs)"
command -v java >/dev/null 2>&1 || fail "java no está en PATH (requerido para H2)"
[ -f inputs.yaml ] || fail "inputs.yaml no encontrado"
[ ! -f pipelines/pl_stage_informes.hpl ] || fail "pl_stage_informes.hpl no debe existir (F3 fuera de alcance)"
[ -f h2/lib/h2-2.4.240.jar ] || fail "jar H2 no encontrado en h2/lib/"
if [ ! -x .venv/bin/python ]; then
  warn "venv ausente; crear con: python3 -m venv --without-pip .venv && pip install -r python/requirements.txt"
fi

step "Reset H2 + DDL STG"
./h2/scripts/reset_and_create.sh

step "Python create STG (inputs.yaml -> tablas STG_*)"
"$PY" python/create_stg.py

step "Staging Excel local DIC (Hop pl_stage_excel, legacy CAGR)"
if [ -x "$HOP_RUN" ]; then
  "$HOP_RUN" -j "$HOP_PROJECT" -f "$ROOT/pipelines/pl_stage_excel.hpl" -r local
else
  warn "hop-run no encontrado ($HOP_RUN); STG Excel DIC puede quedar vacío"
fi

step "Staging F2 CSEP Google Sheets (unidades activas)"
if [ -x "$HOP_RUN" ]; then
  ./scripts/stage_csep_sheets.sh
else
  warn "hop-run no encontrado ($HOP_RUN); STG CSEP Sheets puede quedar vacío"
fi

step "Staging F1 ODs Google Sheets (31 oficinas)"
if [ -x "$HOP_RUN" ]; then
  ./scripts/stage_ods_sheets.sh
else
  warn "hop-run no encontrado ($HOP_RUN); STG ODs Sheets puede quedar vacío"
fi

step "Staging Oracle SISUD (Hop directo)"
if [ -x "$HOP_RUN" ]; then
  "$HOP_RUN" -j "$HOP_PROJECT" -f "$ROOT/pipelines/pl_stage_oracle.hpl" -r local
else
  fail "hop-run no encontrado ($HOP_RUN); requerido para staging Oracle"
fi

step "Python main (logica Fases 2-7 + carga DW)"
set +e
"$PY" python/main.py 2>&1 | tee "$LOG"
MAIN_RC=${PIPESTATUS[0]}
set -e
[ "$MAIN_RC" -eq 0 ] || fail "python/main.py terminó con código $MAIN_RC"

step "Comprobando salidas mínimas en log"
grep -q "Salida PROF_" "$LOG" || fail "no hay salida PROF_* en el log"
grep -q "Salida MI_DIM_" "$LOG" || fail "no hay salida MI_DIM_* en el log"
grep -q "Salida MI_FACT_MC_CSEP" "$LOG" || fail "no hay salida MI_FACT_MC_CSEP en el log"
grep -q "Salida MI_FACT_MC_OD" "$LOG" || fail "no hay salida MI_FACT_MC_OD en el log"
grep -q "Salida MI_FACT_MC_SISUD" "$LOG" || fail "no hay salida MI_FACT_MC_SISUD en el log"
grep -q "Salida MI_DQ_HALLAZGO" "$LOG" || fail "no hay salida MI_DQ_HALLAZGO en el log"
grep -q "Salida MI_INDICADOR_RESULTADO" "$LOG" || fail "no hay MI_INDICADOR_RESULTADO en el log (memoria de corrida)"
if grep -q "Salida DF_INFORMES" "$LOG"; then
  fail "log contiene DF_INFORMES (F3 fuera de alcance)"
fi
if grep -q "Salida MI_FACT_INFORME" "$LOG"; then
  fail "log contiene MI_FACT_INFORME (F3 fuera de alcance)"
fi

if grep -q "DW:" "$LOG"; then
  if grep "DW:.*REVISAR" "$LOG"; then
    fail "carga DW con tablas en REVISAR (conteo Oracle != DataFrame)"
  fi
  grep "DW:.*(OK)" "$LOG" || warn "carga DW sin líneas (OK); revisar credenciales oracle_dw"
  grep -q "DW: POST-CARGA .*MI_DQ_HALLAZGO" "$LOG" || grep -q "MI_DQ_HALLAZGO:" "$LOG" \
    || warn "no se vio POST-CARGA/INSERT de MI_DQ_HALLAZGO en log"
  grep -q "AUD:" "$LOG" || warn "no se vieron líneas AUD: (foto cruda MI_AUD_*)"
else
  fail "sin líneas DW: en log (carga Oracle obligatoria)"
fi

if grep -q '\${[A-Za-z0-9_]\+}' "$LOG"; then
  fail "log contiene variables Hop sin resolver (\${VAR})"
fi

step "Verificación Oracle canónica (estrella + DQ + AUD; sin VW/QA/K)"
"$PY" - <<'PY'
import sys
from pathlib import Path

ROOT = Path(".")
sys.path.insert(0, str(ROOT / "python"))
from config import require_live_conn, load_vars  # noqa: E402

cv = require_live_conn("oracle_dw", load_vars(ROOT))

import oracledb  # noqa: E402

try:
    oracledb.init_oracle_client()
except Exception:
    pass

dsn = oracledb.makedsn(cv["host"], int(cv["port"] or "1521"), service_name=cv["database"])
with oracledb.connect(user=cv["username"], password=cv["password"], dsn=dsn) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT USER FROM DUAL")
        esq = str(cur.fetchone()[0])
        print(f"Esquema sesión: {esq}")

        def exists_table(name: str) -> bool:
            cur.execute(
                "SELECT COUNT(*) FROM user_tables WHERE table_name = :1",
                [name.upper()],
            )
            return int(cur.fetchone()[0]) > 0

        def exists_view(name: str) -> bool:
            cur.execute(
                "SELECT COUNT(*) FROM user_views WHERE view_name = :1",
                [name.upper()],
            )
            return int(cur.fetchone()[0]) > 0

        def count(name: str) -> int:
            cur.execute(f"SELECT COUNT(*) FROM {esq}.{name}")
            return int(cur.fetchone()[0])

        # F3 fuera de alcance
        if exists_table("MI_FACT_INFORME_SUPERVISION"):
            sys.exit("MI_FACT_INFORME_SUPERVISION aún existe (F3 debe estar droppeada)")
        print("MI_FACT_INFORME_SUPERVISION: inexistente")

        cur.execute(
            """
            SELECT COUNT(*) FROM user_tab_columns
            WHERE table_name = 'MI_FACT_MULTA_COERCITIVA'
              AND column_name = 'ID_INFORME'
            """
        )
        if cur.fetchone()[0]:
            sys.exit("MI_FACT_MULTA_COERCITIVA.ID_INFORME aún existe (F3 debe estar droppeada)")
        print("ID_INFORME: inexistente en MI_FACT_MULTA_COERCITIVA")

        cur.execute(
            """
            SELECT COUNT(*) FROM user_tab_columns
            WHERE table_name = 'MI_FACT_MULTA_COERCITIVA'
              AND column_name = 'FUENTE_REGISTRO'
            """
        )
        if cur.fetchone()[0]:
            sys.exit("MI_FACT_MULTA_COERCITIVA.FUENTE_REGISTRO aún existe (debe deprecarse)")
        print("FUENTE_REGISTRO VARCHAR: inexistente")

        cur.execute(
            """
            SELECT COUNT(*) FROM user_tab_columns
            WHERE table_name = 'MI_FACT_MULTA_COERCITIVA'
              AND column_name = 'ID_TIEMPO_FIRMA'
            """
        )
        if not cur.fetchone()[0]:
            sys.exit("falta MI_FACT_MULTA_COERCITIVA.ID_TIEMPO_FIRMA")
        print("ID_TIEMPO_FIRMA: presente")

        # Canónico publicado
        for t in (
            "MI_FACT_MC_CSEP",
            "MI_FACT_MC_OD",
            "MI_FACT_MC_SISUD",
            "MI_FACT_MULTA_COERCITIVA",
            "MI_DET_ETAPA_MC",
            "MI_DQ_HALLAZGO",
            "MI_AUD_F1_OD_MULTAS",
            "MI_AUD_F2_CSEP_MULTAS",
            "MI_AUD_F2_CSEP_ETAPAS",
            "MI_AUD_F5_SISUD_VW",
        ):
            if not exists_table(t):
                sys.exit(f"falta tabla canónica {t}")
        print("Tablas canónicas (facts/DET/DQ/AUD): OK")

        # Prohibidas en destino
        for t in ("MI_QA_AMARRE", "MI_QA_AMARRE_DETALLE", "MI_INDICADOR_RESULTADO"):
            if exists_table(t):
                sys.exit(f"{t} no debe publicarse en Oracle (solo memoria de corrida)")
        print("QA/K en Oracle: ausentes (OK)")

        cur.execute(
            """
            SELECT view_name FROM user_views
            WHERE view_name LIKE 'VW_MC_%' OR view_name LIKE 'VW_FCT_%'
            ORDER BY 1
            """
        )
        vistas = [r[0] for r in cur.fetchall()]
        if vistas:
            sys.exit(f"vistas VW_* no deben existir tras wipe: {', '.join(vistas)}")
        print("Vistas VW_MC_/VW_FCT_: ninguna (OK)")

        by_tbl = {
            "CSEP": count("MI_FACT_MC_CSEP"),
            "OD": count("MI_FACT_MC_OD"),
            "SISUD": count("MI_FACT_MC_SISUD"),
            "ENRIQUECIDA": count("MI_FACT_MULTA_COERCITIVA"),
            "DET": count("MI_DET_ETAPA_MC"),
            "DQ": count("MI_DQ_HALLAZGO"),
            "AUD_F1": count("MI_AUD_F1_OD_MULTAS"),
            "AUD_F2": count("MI_AUD_F2_CSEP_MULTAS"),
            "AUD_ET": count("MI_AUD_F2_CSEP_ETAPAS"),
            "AUD_F5": count("MI_AUD_F5_SISUD_VW"),
        }
        print(f"Conteos canónicos: {by_tbl}")
        expected_min = {"CSEP": 200, "OD": 50, "SISUD": 50}
        for cod, mn in expected_min.items():
            n = by_tbl.get(cod, 0)
            if n < mn:
                sys.exit(f"conteo {cod}={n} bajo mínimo esperado {mn} (posible fallo de staging)")
        n_enriq = by_tbl["ENRIQUECIDA"]
        n_sheets = by_tbl["CSEP"] + by_tbl["OD"]
        if n_enriq != n_sheets:
            sys.exit(f"enriquecida={n_enriq} debe igualar CSEP+OD={n_sheets}")
        if by_tbl["AUD_F2"] != by_tbl["CSEP"]:
            sys.exit(f"AUD_F2={by_tbl['AUD_F2']} debe igualar CSEP={by_tbl['CSEP']}")
        if by_tbl["AUD_F1"] != by_tbl["OD"]:
            sys.exit(f"AUD_F1={by_tbl['AUD_F1']} debe igualar OD={by_tbl['OD']}")
        if by_tbl["AUD_F5"] != by_tbl["SISUD"]:
            sys.exit(f"AUD_F5={by_tbl['AUD_F5']} debe igualar SISUD={by_tbl['SISUD']}")
        print(f"MI_DQ_HALLAZGO: {by_tbl['DQ']} filas (R01–R05; 0 es válido si no hay hallazgos)")

        cur.execute(
            """
            SELECT COUNT(*),
                   SUM(CASE WHEN CUM IS NOT NULL AND CAM IS NOT NULL THEN 1 ELSE 0 END)
            FROM {esq}.MI_FACT_MULTA_COERCITIVA
            WHERE REGEXP_REPLACE(UPPER(REPLACE(TRIM(N_RES_MC), ' ', '')), '^0+([0-9]+)', '\\1')
                  LIKE '153-2026-OEFA/DSEM'
              AND MONTO_UIT = 64
            """.format(esq=esq)
        )
        n0153, n_con_cum = cur.fetchone()
        n0153 = int(n0153 or 0)
        n_con_cum = int(n_con_cum or 0)
        print(f"Caso 0153/64: {n0153} filas enriquecida, {n_con_cum} con CUM+CAM")
        if n0153 < 2:
            sys.exit(f"caso 0153/64: esperado >=2 filas enriquecida, hay {n0153}")

        n_org = count("MI_DIM_ORGANO_UNIDAD")
        if n_org > 20:
            sys.exit(f"MI_DIM_ORGANO_UNIDAD={n_org} (esperado ~11 CSEP+ND)")
        print(f"MI_DIM_ORGANO_UNIDAD: {n_org}")
PY

echo ""
echo -e "${GREEN}HARNESS OK${NC} — ver CHECKPOINTS.md y docs/verification.md"
exit 0
