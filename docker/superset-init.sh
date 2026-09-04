#!/usr/bin/env bash
# Primera corrida: migra DB interna de Superset y crea usuario admin.
set -euo pipefail

superset db upgrade

# Idempotente: si el usuario ya existe, no falla el contenedor
superset fab create-admin \
  --username "${SUPERSET_ADMIN_USER:-admin}" \
  --firstname Admin \
  --lastname User \
  --email "${SUPERSET_ADMIN_EMAIL:-admin@localhost}" \
  --password "${SUPERSET_ADMIN_PASSWORD:-admin}" \
  || true

superset init
