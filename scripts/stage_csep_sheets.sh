#!/usr/bin/env bash
# Descarga unidades CSEP F2 (Google Sheets) → H2 STG_GS1_CSEP_MULTAS + STG_GS1_ETAPAS.
# Usa pl_stage_csep_sheet.hpl / pl_stage_csep_etapa.hpl + docs/inputs/f2_csep_sheets.json.
# COD_UNIDAD se asigna con UPDATE tras cada hop-run de multas.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python
HOP_RUN="${HOP_RUN:-$HOME/apps/hop/hop-run.sh}"
HOP_PROJECT="$(basename "$ROOT")"
CATALOG="$ROOT/docs/inputs/f2_csep_sheets.json"
MAX_RETRIES="${STAGE_CSEP_RETRIES:-4}"
RETRY_SLEEP="${STAGE_CSEP_RETRY_SLEEP:-8}"
export PYTHONPATH="$ROOT/python${PYTHONPATH:+:$PYTHONPATH}"

[ -f "$CATALOG" ] || { echo "FAIL: falta $CATALOG" >&2; exit 1; }
[ -f "$ROOT/client_secret.json" ] || { echo "FAIL: falta client_secret.json (service account)" >&2; exit 1; }
[ -x "$HOP_RUN" ] || { echo "FAIL: hop-run no encontrado ($HOP_RUN)" >&2; exit 1; }

echo "==> Truncate STG_GS1_CSEP_MULTAS + STG_GS1_ETAPAS"
"$PY" - <<'PY'
from config import load_vars, project_root
from h2_conn import connect_h2
root = project_root()
conn = connect_h2(root, load_vars(root))
try:
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE PUBLIC.STG_GS1_CSEP_MULTAS")
    cur.execute("TRUNCATE TABLE PUBLIC.STG_GS1_ETAPAS")
    conn.commit()
    print("TRUNCATED STG_GS1_CSEP_MULTAS, STG_GS1_ETAPAS")
finally:
    conn.close()
PY

mapfile -t UNITS < <("$PY" - <<'PY'
import json
from pathlib import Path
cat = json.loads(Path("docs/inputs/f2_csep_sheets.json").read_text(encoding="utf-8"))
for o in cat.get("unidades") or []:
    if o.get("activo", True):
        print(f"{o['cod_unidad']}|{o['spreadsheet_key']}")
PY
)

hop_with_retry() {
  local label="$1"
  local pipeline="$2"
  local params="$3"
  local attempt=1
  while true; do
    set +e
    "$HOP_RUN" -j "$HOP_PROJECT" -f "$ROOT/pipelines/$pipeline" -r local -p "$params"
    rc=$?
    set -e
    if [ "$rc" -eq 0 ]; then
      return 0
    fi
    if [ "$attempt" -ge "$MAX_RETRIES" ]; then
      echo "FAIL: $label tras $MAX_RETRIES intentos (rc=$rc)" >&2
      return "$rc"
    fi
    echo "AVISO: $label falló (rc=$rc); reintento $attempt/$MAX_RETRIES en ${RETRY_SLEEP}s"
    sleep "$RETRY_SLEEP"
    attempt=$((attempt + 1))
  done
}

n=0
for row in "${UNITS[@]}"; do
  COD="${row%%|*}"
  KEY="${row#*|}"
  n=$((n+1))
  echo "==> [$n/${#UNITS[@]}] Unidad $COD (multas)"
  hop_with_retry "CSEP $COD multas" "pl_stage_csep_sheet.hpl" "SPREADSHEET_KEY=${KEY},COD_UNIDAD=${COD}"
  COD_UNIDAD="$COD" "$PY" - <<'PY'
import os
from config import load_vars, project_root
from h2_conn import connect_h2
cod = os.environ["COD_UNIDAD"]
root = project_root()
conn = connect_h2(root, load_vars(root))
try:
    cur = conn.cursor()
    cur.execute(
        "UPDATE PUBLIC.STG_GS1_CSEP_MULTAS SET COD_UNIDAD = ? WHERE COD_UNIDAD IS NULL",
        [cod],
    )
    print(f"COD_UNIDAD={cod} filas_actualizadas={cur.rowcount}")
    conn.commit()
finally:
    conn.close()
PY
  echo "==> [$n/${#UNITS[@]}] Unidad $COD (etapas)"
  hop_with_retry "CSEP $COD etapas" "pl_stage_csep_etapa.hpl" "SPREADSHEET_KEY=${KEY}"
done
echo "==> Stage CSEP Sheets OK ($n unidades)"
