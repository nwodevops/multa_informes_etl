#!/usr/bin/env bash
# Ejecuta un pipeline Hop solo si la conexión en project-config no es placeholder.
# Uso (desde raíz del proyecto):
#   h2/scripts/stage_if_configured.sh oracle_sisud pipelines/pl_stage_oracle.hpl

set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
CONN="${1:?connection}"
HPL="${2:?pipeline.hpl}"
PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python
HOP_RUN="${HOP_RUN:-$HOME/apps/hop/hop-run.sh}"
# Nombre del proyecto Hop = carpeta del repo (evita HOP_PROJECT=etl_cursor del GUI).
HOP_PROJECT="$(basename "$ROOT")"

if ! "$PY" python/should_stage_external.py "$CONN"; then
  echo "AVISO: ${HPL} omitido (credenciales placeholder ${CONN})"
  exit 0
fi

if [ ! -x "$HOP_RUN" ]; then
  echo "ERROR: no se encuentra hop-run: $HOP_RUN" >&2
  exit 1
fi

"$HOP_RUN" -j "$HOP_PROJECT" -f "$ROOT/$HPL" -r local
