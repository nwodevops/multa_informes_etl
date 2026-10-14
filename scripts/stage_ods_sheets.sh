#!/usr/bin/env bash
# Descarga las 31 ODs F1 (Google Sheets) → H2 STG_GS2_OD_MULTAS.
# Usa pipelines/pl_stage_od_sheet.hpl + docs/inputs/f1_ods_sheets.json.
# COD_OD se asigna con UPDATE tras cada hop-run (Constant no resuelve params de forma fiable).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python
HOP_RUN="${HOP_RUN:-$HOME/apps/hop/hop-run.sh}"
HOP_PROJECT="$(basename "$ROOT")"
CATALOG="$ROOT/docs/inputs/f1_ods_sheets.json"
MAX_RETRIES="${STAGE_ODS_RETRIES:-4}"
RETRY_SLEEP="${STAGE_ODS_RETRY_SLEEP:-8}"
export PYTHONPATH="$ROOT/python${PYTHONPATH:+:$PYTHONPATH}"

[ -f "$CATALOG" ] || { echo "FAIL: falta $CATALOG" >&2; exit 1; }
[ -f "$ROOT/client_secret.json" ] || { echo "FAIL: falta client_secret.json (service account)" >&2; exit 1; }
[ -x "$HOP_RUN" ] || { echo "FAIL: hop-run no encontrado ($HOP_RUN)" >&2; exit 1; }

echo "==> Truncate STG_GS2_OD_MULTAS"
"$PY" - <<'PY'
from config import load_vars, project_root
from h2_conn import connect_h2
root = project_root()
conn = connect_h2(root, load_vars(root))
try:
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE PUBLIC.STG_GS2_OD_MULTAS")
    conn.commit()
    print("TRUNCATED STG_GS2_OD_MULTAS")
finally:
    conn.close()
PY

mapfile -t ODS < <("$PY" - <<'PY'
import json
from pathlib import Path
cat = json.loads(Path("docs/inputs/f1_ods_sheets.json").read_text(encoding="utf-8"))
for o in cat.get("ods") or []:
    if o.get("activo", True):
        print(f"{o['cod_od']}|{o['spreadsheet_key']}")
PY
)

n=0
for row in "${ODS[@]}"; do
  COD="${row%%|*}"
  KEY="${row#*|}"
  n=$((n+1))
  echo "==> [$n/${#ODS[@]}] OD $COD"
  attempt=1
  while true; do
    set +e
    "$HOP_RUN" -j "$HOP_PROJECT" -f "$ROOT/pipelines/pl_stage_od_sheet.hpl" -r local \
      -p "SPREADSHEET_KEY=${KEY},COD_OD=${COD}"
    rc=$?
    set -e
    if [ "$rc" -eq 0 ]; then
      break
    fi
    if [ "$attempt" -ge "$MAX_RETRIES" ]; then
      echo "FAIL: OD $COD tras $MAX_RETRIES intentos (rc=$rc)" >&2
      exit "$rc"
    fi
    echo "AVISO: OD $COD falló (rc=$rc); reintento $attempt/$MAX_RETRIES en ${RETRY_SLEEP}s"
    sleep "$RETRY_SLEEP"
    attempt=$((attempt + 1))
  done
  COD_OD="$COD" "$PY" - <<'PY'
import os
from config import load_vars, project_root
from h2_conn import connect_h2
cod = os.environ["COD_OD"]
root = project_root()
conn = connect_h2(root, load_vars(root))
try:
    cur = conn.cursor()
    cur.execute(
        "UPDATE PUBLIC.STG_GS2_OD_MULTAS SET COD_OD = ? WHERE COD_OD IS NULL",
        [cod],
    )
    print(f"COD_OD={cod} filas_actualizadas={cur.rowcount}")
    conn.commit()
finally:
    conn.close()
PY
done
echo "==> Stage ODs Sheets OK ($n oficinas)"
