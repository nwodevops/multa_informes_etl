#!/usr/bin/env bash
# Mata el server H2 si existe. Equivalente Linux de stop_h2.bat.
# Al parar el server, la BD in-memory mem:csep se limpia sola.
set -uo pipefail

echo "Deteniendo H2 Server si existe..."

pids="$(pgrep -f org.h2.tools.Server || true)"

if [ -z "$pids" ]; then
  echo "Stop H2 listo (no habia server corriendo)"
  exit 0
fi

for pid in $pids; do
  echo "Kill PID $pid"
  kill "$pid" 2>/dev/null || true
done

for _ in $(seq 1 10); do
  pgrep -f org.h2.tools.Server >/dev/null 2>&1 || break
  sleep 1
done

# Sobrevivientes al TERM: SIGKILL.
for pid in $(pgrep -f org.h2.tools.Server || true); do
  echo "Kill -9 PID $pid"
  kill -9 "$pid" 2>/dev/null || true
done

sleep 1
echo "Stop H2 listo"
exit 0
