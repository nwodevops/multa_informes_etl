# Sesión activa

> El líder (humano o agente principal) mantiene este archivo. Al cerrar sesión, resumir en [`history.md`](history.md).

## Feature activa

| Campo | Valor |
|---|---|
| ID | *(ninguna)* |
| Status | — |
| Criterio | — |

## Plan

1. Lineamiento Fases 1–7 + infra (staging, Windows, remote, rename `MI_`): **cerrados**.
2. Fase 8 Power BI: **fuera de alcance**.
3. Siguiente trabajo: abrir feature nueva en `feature_list.json` cuando haga falta.

## Comandos

```bash
./switch-env.sh local
./init.sh
.venv/bin/python python/verify_dw.py
```
