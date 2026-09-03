# Sesión activa

> El líder (humano o agente principal) mantiene este archivo. Al cerrar sesión, resumir en [`history.md`](history.md).

## Feature activa

| Campo | Valor |
|---|---|
| ID | *(ninguna `in_progress`; `dw-solo-multas` cerrada)* |
| Status | — |
| Criterio | [`CHECKPOINTS.md`](../CHECKPOINTS.md) |

## Plan

1. Elegir siguiente feature `pending` en [`feature_list.json`](../feature_list.json) si aplica.
2. `./init.sh` → HARNESS OK.

## Comandos

```bash
./switch-env.sh local
./init.sh
.venv/bin/python python/verify_dw.py
```
