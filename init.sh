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

step "Staging Excel local (Hop pl_stage_excel)"
if [ -x "$HOP_RUN" ]; then
  "$HOP_RUN" -j "$HOP_PROJECT" -f "$ROOT/pipelines/pl_stage_excel.hpl" -r local
else
  warn "hop-run no encontrado ($HOP_RUN); STG Excel puede quedar vacío"
fi

step "Staging Oracle / MySQL (Hop directo)"
if [ -x "$HOP_RUN" ]; then
  "$HOP_RUN" -j "$HOP_PROJECT" -f "$ROOT/pipelines/pl_stage_oracle.hpl" -r local
  "$HOP_RUN" -j "$HOP_PROJECT" -f "$ROOT/pipelines/pl_stage_mysql.hpl" -r local
else
  fail "hop-run no encontrado ($HOP_RUN); requerido para staging Oracle/MySQL"
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
grep -q "Salida MI_FACT_MULTA_COERCITIVA" "$LOG" || fail "no hay salida MI_FACT_MULTA_COERCITIVA en el log"
grep -q "Salida MI_INDICADOR_RESULTADO" "$LOG" || fail "no hay MI_INDICADOR_RESULTADO en el log"
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
else
  fail "sin líneas DW: en log (carga Oracle obligatoria)"
fi

if grep -q '\${[A-Za-z0-9_]\+}' "$LOG"; then
  fail "log contiene variables Hop sin resolver (\${VAR})"
fi

step "Verificación Oracle opcional (K1–K5)"
"$PY" - <<'PY'
import sys
from pathlib import Path

ROOT = Path(".")
sys.path.insert(0, str(ROOT / "python"))
from config import require_live_conn, load_vars  # noqa: E402

cv = require_live_conn("oracle_dw", load_vars(ROOT))

import oracledb  # noqa: E402

dsn = oracledb.makedsn(cv["host"], int(cv["port"] or "1521"), service_name=cv["database"])
with oracledb.connect(user=cv["username"], password=cv["password"], dsn=dsn) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM APP.MI_INDICADOR_RESULTADO")
        n, = cur.fetchone()
        print(f"MI_INDICADOR_RESULTADO: {n} filas en Oracle")
        cur.execute(
            "SELECT DISTINCT COD_INDICADOR FROM APP.MI_INDICADOR_RESULTADO ORDER BY 1"
        )
        codes = {r[0] for r in cur.fetchall()}
        missing = sorted({"K1", "K2", "K3", "K4", "K5"} - codes)
        if missing:
            sys.exit(f"faltan indicadores en Oracle: {missing}")
        print("Indicadores K1–K5 presentes")
        cur.execute(
            """
            SELECT COUNT(*) FROM all_tables
            WHERE owner = 'APP' AND table_name = 'MI_FACT_INFORME_SUPERVISION'
            """
        )
        n_inf, = cur.fetchone()
        if n_inf:
            sys.exit("APP.MI_FACT_INFORME_SUPERVISION aún existe (F3 debe estar droppeada)")
        print("MI_FACT_INFORME_SUPERVISION: inexistente")
        cur.execute(
            """
            SELECT COUNT(*) FROM all_tab_columns
            WHERE owner = 'APP' AND table_name = 'MI_FACT_MULTA_COERCITIVA'
              AND column_name = 'ID_INFORME'
            """
        )
        n_col, = cur.fetchone()
        if n_col:
            sys.exit("MI_FACT_MULTA_COERCITIVA.ID_INFORME aún existe (F3 debe estar droppeada)")
        print("ID_INFORME: inexistente en MI_FACT_MULTA_COERCITIVA")
PY

echo ""
echo -e "${GREEN}HARNESS OK${NC} — ver CHECKPOINTS.md y docs/verification.md"
exit 0
