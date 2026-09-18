#!/usr/bin/env bash
# Regenera archetype/ (cascarón Hop + H2 + Python) desde este repo.
# Uso: ./scripts/sync_archetype.sh
# Nuevo proyecto: ./scripts/nuevo_etl.sh /ruta/mi_etl
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

echo "==> Copiando infraestructura (H2, Hop, Python STG)"
copy_tree "$ROOT/h2/lib" "$ARCH/h2/lib"
copy_tree "$ROOT/h2/scripts" "$ARCH/h2/scripts"
copy_tree "$ROOT/h2/sql" "$ARCH/h2/sql"
copy_tree "$ROOT/metadata" "$ARCH/metadata"
copy_tree "$ROOT/switch-env.sh" "$ARCH/switch-env.sh"
copy_tree "$ROOT/switch-env.ps1" "$ARCH/switch-env.ps1"
copy_tree "$ROOT/workflows/wf_create_stg.hwf" "$ARCH/workflows/wf_create_stg.hwf"
copy_tree "$ROOT/pipelines/pl_demo.hpl" "$ARCH/pipelines/pl_demo.hpl"
copy_tree "$ROOT/.agents/skills/hop-python-etl" "$ARCH/.agents/skills/hop-python-etl"
copy_tree "$ROOT/docs/harness" "$ARCH/docs/harness"

mkdir -p "$ARCH/python/introspect" "$ARCH/python/io" "$ARCH/logica" \
  "$ARCH/input_excel" "$ARCH/output" "$ARCH/progress" "$ARCH/pipelines" "$ARCH/workflows"

for f in config.py h2_conn.py create_stg.py requirements.txt plantilla_logica.py; do
  cp -a "$ROOT/python/$f" "$ARCH/python/$f"
done
cp -a "$ROOT/python/introspect/." "$ARCH/python/introspect/"

echo "==> Aplicando overlays (cascarón: Excel demo, sin lógica de multa)"
OVERLAY_FILES=(
  README.md .gitignore AGENTS.md CHECKPOINTS.md feature_list.json init.sh
  inputs.yaml ESTRUCTURA.md
  docs/arquitectura.md docs/verification.md docs/harness/platform.md
  progress/current.md progress/history.md
  logica/demo.py logica/LEEME.md
  python/main.py python/CONTRATO.md python/LEEME.md
  python/io/leer_h2.py python/io/LEEME.md python/io/escribir_excel.py
  workflows/wf_main.hwf
  environments/local.json environments/remote.json
  input_excel/README.md
  .agents/skills/hop-python-etl/SKILL.md
  .agents/skills/hop-python-etl/reference.md
  .agents/skills/hop-python-etl/inputs.example.yaml
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

chmod +x "$ARCH/init.sh" "$ARCH/switch-env.sh" "$ARCH/h2/scripts/"*.sh 2>/dev/null || true

echo "==> project-config.json desde environments/local.json"
(cd "$ARCH" && ./switch-env.sh local)

echo "==> archetype/ listo en $ARCH"
echo "    Nuevo proyecto: ./scripts/nuevo_etl.sh /ruta/mi_etl"
echo "    Smoke aquí:     cd archetype && ./init.sh"
