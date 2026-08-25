#!/usr/bin/env bash
# Regenera archetype/ (plantilla mínima) desde el repo padre.
# Uso: ./scripts/sync_archetype.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARCH="$ROOT/archetype"
OVER="$ROOT/scripts/archetype-overlays"

echo "==> Limpiando $ARCH"
rm -rf "$ARCH"
mkdir -p "$ARCH"

copy_tree() {
  local src="$1" dst="$2"
  mkdir -p "$(dirname "$dst")"
  cp -a "$src" "$dst"
}

echo "==> Copiando infraestructura"
copy_tree "$ROOT/h2/lib" "$ARCH/h2/lib"
copy_tree "$ROOT/h2/scripts" "$ARCH/h2/scripts"
copy_tree "$ROOT/h2/sql" "$ARCH/h2/sql"
copy_tree "$ROOT/metadata" "$ARCH/metadata"
copy_tree "$ROOT/switch-env.sh" "$ARCH/switch-env.sh"
copy_tree "$ROOT/workflows/wf_create_stg.hwf" "$ARCH/workflows/wf_create_stg.hwf"
copy_tree "$ROOT/pipelines/pl_demo.hpl" "$ARCH/pipelines/pl_demo.hpl"
copy_tree "$ROOT/.agents/skills/hop-python-etl" "$ARCH/.agents/skills/hop-python-etl"
copy_tree "$ROOT/docs/harness" "$ARCH/docs/harness"

mkdir -p "$ARCH/python/introspect" "$ARCH/python/io" "$ARCH/logica" "$ARCH/input_excel" "$ARCH/output" "$ARCH/progress" "$ARCH/pipelines" "$ARCH/workflows"

for f in config.py h2_conn.py create_stg.py requirements.txt LEEME.md plantilla_logica.py; do
  cp -a "$ROOT/python/$f" "$ARCH/python/$f"
done
cp -a "$ROOT/python/introspect/." "$ARCH/python/introspect/"
cp -a "$ROOT/python/io/escribir_excel.py" "$ARCH/python/io/escribir_excel.py"
cp -a "$ROOT/python/io/LEEME.md" "$ARCH/python/io/LEEME.md"

echo "==> Aplicando overlays (versiones demo del arquetipo)"
OVERLAY_FILES=(
  README.md .gitignore AGENTS.md CHECKPOINTS.md feature_list.json init.sh
  inputs.yaml ESTRUCTURA.md
  docs/arquitectura.md docs/verification.md
  progress/current.md progress/history.md
  logica/demo.py logica/LEEME.md
  python/main.py python/CONTRATO.md python/io/leer_h2.py
  workflows/wf_main.hwf
  environments/local.json environments/remote.json
  project-config.json
  input_excel/README.md
)
for rel in "${OVERLAY_FILES[@]}"; do
  src="$OVER/$rel"
  dst="$ARCH/$rel"
  if [ ! -f "$src" ]; then
    echo "ERROR: falta overlay $src" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$dst")"
  cp -a "$src" "$dst"
done

chmod +x "$ARCH/init.sh" "$ARCH/h2/scripts/"*.sh 2>/dev/null || true

echo "==> archetype/ listo en $ARCH"
echo "    Probar: TEST=\$(mktemp -d) && cp -r archetype/ \"\$TEST/mi_etl\" && cd \"\$TEST/mi_etl\" && ./init.sh"
