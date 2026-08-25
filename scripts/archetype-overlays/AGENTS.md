# AGENTS.md — mapa para agentes (arquetipo mínimo)

ETL **Apache Hop + H2 in-memory + Python**. Arquitectura: [`docs/arquitectura.md`](docs/arquitectura.md).

**Verificación:** [`./init.sh`](init.sh) debe terminar en **`HARNESS OK`**. Criterios: [`CHECKPOINTS.md`](CHECKPOINTS.md).

## Harness

| Archivo | Propósito |
|---|---|
| [`feature_list.json`](feature_list.json) | Alcance; **una** `in_progress` a la vez |
| [`progress/current.md`](progress/current.md) | Plan de sesión activa |
| [`progress/history.md`](progress/history.md) | Bitácora append-only |
| [`docs/harness/workflow.md`](docs/harness/workflow.md) | Roles líder / implementador / revisor |
| [`docs/harness/platform.md`](docs/harness/platform.md) | Hop, H2, variables |

## Skill

- [`.agents/skills/hop-python-etl/SKILL.md`](.agents/skills/hop-python-etl/SKILL.md)

## Inicio rápido

```bash
./init.sh
./switch-env.sh local
~/apps/hop/hop-gui.sh   # → wf_main.hwf
```

## Reglas críticas

1. **Un solo `.py`** en `logica/`.
2. **Sin secretos** en git (`project-config.json`, `environments/`).
3. **Sin `${VAR}` literal** en logs Hop = variable mal definida.

Detalle plataforma → [`docs/harness/platform.md`](docs/harness/platform.md).

## Consultoría avanzada

Para DW Oracle, cuarentena blanda e indicadores: extender desde repo OEFA (`etl_phyton_cursor`). Ver [`README.md`](README.md) sección «Extender a consultoría OEFA».
