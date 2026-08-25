# Sesión activa

> El líder (humano o agente principal) mantiene este archivo. Al cerrar sesión, resumir en [`history.md`](history.md).

## Feature activa

| Campo | Valor |
|---|---|
| ID | *(ninguna — siguiente: **fase-8-powerbi**)* |
| Status | — |
| Criterio | [`CHECKPOINTS.md#fase-8`](../CHECKPOINTS.md#fase-8) |

## Plan

1. Poner `fase-8-powerbi` en `in_progress` cuando arranques Power BI.
2. Conectar `.pbix` a `app@localhost:1524/BD_CURSOR` (esquema APP).
3. Documentar en `progress/impl_fase-8-powerbi.md`.

## Comandos

```bash
.venv/bin/python python/verify_dw.py
./init.sh
```
