# Sesión activa

> El líder (humano o agente principal) mantiene este archivo. Al cerrar sesión, resumir en [`history.md`](history.md).

## Feature activa

| Campo | Valor |
|---|---|
| ID | **fase-rename-dw** |
| Status | in_progress |
| Criterio | Prefijo `MI_` en 11 tablas DW; `init.bat` / `./init.sh` → HARNESS OK |

## Plan

1. Cerrar `fase-rename-dw` cuando rename + smoke estén verificados.
2. Lineamiento Fases 1–7 + infra staging: **cerrados**.
3. Fase 8 Power BI: **fuera de alcance** (no se realizará).

## Comandos

```bash
.venv/bin/python python/verify_dw.py
./init.sh
```
