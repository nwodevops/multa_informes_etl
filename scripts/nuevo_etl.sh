#!/usr/bin/env bash
# Copia el cascarón Hop+H2+Python a un directorio nuevo (vacío) y deja .venv usable.
# Uso: ./scripts/nuevo_etl.sh /ruta/mi_etl
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-}"

if [[ -z "$DEST" ]]; then
  echo "Uso: $0 /ruta/mi_etl" >&2
  exit 1
fi
DEST="$(python3 -c "import os,sys; print(os.path.abspath(os.path.expanduser(sys.argv[1])))" "$DEST")"
cd "$ROOT"
if [[ -e "$DEST" ]]; then
  echo "ERROR: ya existe $DEST" >&2
  exit 1
fi

"$ROOT/scripts/sync_archetype.sh"
mkdir -p "$(dirname "$DEST")"
cp -a "$ROOT/archetype" "$DEST"
chmod +x "$DEST/init.sh" "$DEST/switch-env.sh" "$DEST/h2/scripts/"*.sh 2>/dev/null || true
(cd "$DEST" && ./switch-env.sh local)

bootstrap_venv() {
  local dest="$1"
  echo "==> .venv (sin ensurepip del sistema; Ubuntu típico)"
  python3 -m venv --without-pip "$dest/.venv"
  local ver dest_sp parent_sp
  ver="$("$dest/.venv/bin/python" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")"
  dest_sp="$dest/.venv/lib/python${ver}/site-packages"
  parent_sp="$ROOT/.venv/lib/python${ver}/site-packages"
  mkdir -p "$dest_sp"
  if [[ -d "$parent_sp/pip" ]]; then
    # Copiar pip del repo padre: python3-venv no trae ensurepip en este Ubuntu.
    shopt -s nullglob
    cp -a "$parent_sp/pip" "$parent_sp"/pip-*.dist-info "$dest_sp/"
    shopt -u nullglob
  fi
  if ! "$dest/.venv/bin/python" -m pip --version >/dev/null 2>&1; then
    echo "==> pip vía get-pip.py"
    curl -fsSL https://bootstrap.pypa.io/get-pip.py | "$dest/.venv/bin/python"
  fi
  (cd "$dest" && .venv/bin/python -m pip install -q -r python/requirements.txt)
  "$dest/.venv/bin/python" -c "import yaml, pandas" >/dev/null
}

bootstrap_venv "$DEST"

cat <<EOF
Cascarón listo: $DEST

cd $DEST
./init.sh

Después: inputs.yaml + pl_stage_*.hpl + LECTURAS + logica/<tu>.py
(reemplaza logica/demo.py; un solo .py en logica/).
EOF
