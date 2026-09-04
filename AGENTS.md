# AGENTS.md — mapa para agentes

ETL **Apache Hop + H2 in-memory + Python** (OEFA). Requerimiento: [`docs/TDR REQ 3629-2026.pdf`](docs/TDR%20REQ%203629-2026.pdf). Arquitectura: [`docs/arquitectura.md`](docs/arquitectura.md).

> **Arquetipo base:** plantilla mínima `archetype/` (no versionado; regenerar con `./scripts/sync_archetype.sh`). Este repo es la implementación de referencia consultoría.

**Verificación:** [`./init.sh`](init.sh) (o [`init.bat`](init.bat) en Windows) debe terminar en **`HARNESS OK`**. Criterios: [`CHECKPOINTS.md`](CHECKPOINTS.md). Detalle: [`docs/verification.md`](docs/verification.md).

## Harness (orquestación)

| Archivo | Propósito |
|---|---|
| [`feature_list.json`](feature_list.json) | Alcance por fase; **una** `in_progress` a la vez |
| [`progress/current.md`](progress/current.md) | Plan de sesión activa |
| [`progress/history.md`](progress/history.md) | Bitácora append-only |
| [`docs/harness/workflow.md`](docs/harness/workflow.md) | Roles líder / implementador / revisor |
| [`docs/harness/platform.md`](docs/harness/platform.md) | Hop, H2, variables, conexiones (detalle) |

Patrón: [ejemplo-harness-subagentes](https://github.com/nwoswo/ejemplo-harness-subagentes) — estado en disco, no en chat.

## Skills (dominio ETL)

- [`.agents/skills/hop-python-etl/SKILL.md`](.agents/skills/hop-python-etl/SKILL.md) — arquetipo Hop + H2 + Python
- [`.agents/skills/phased-dwh-lineamiento/SKILL.md`](.agents/skills/phased-dwh-lineamiento/SKILL.md) — fases 2–7, `logica/dwh/`
- [`.agents/skills/auditable-soft-quarantine/SKILL.md`](.agents/skills/auditable-soft-quarantine/SKILL.md) — cuarentena blanda, DQ, amarre H9
- [`.agents/skills/oracle-cargar-dw/SKILL.md`](.agents/skills/oracle-cargar-dw/SKILL.md) — TRUNCATE+INSERT, DDL, gotchas Oracle

Lineamiento canónico: [`docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md`](docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md). Status: [`docs/fase1-3/status.md`](docs/fase1-3/status.md). DDL DW: [`docs/lineamientos/ddl/`](docs/lineamientos/ddl/).

## Inicio rápido

```bash
./init.sh                                    # smoke harness (termina en HARNESS OK)
./switch-env.sh local                        # entorno → regenera project-config.json
~/apps/hop/hop-gui.sh                        # Hop GUI → wf_main.hwf (win: wf_main_win.hwf)
```

Flujo datos: `inputs.yaml` → Hop `STG_*` (H2 `mem:csep`, puerto 9092) → `python/main.py` → `logica/ejecutar.py` (auto-descubierto) → `logica/dwh/pipeline.py` (fases 2–7) → `python/io/cargar_dw.py` (TRUNCATE+INSERT, esquema `MULTA_COERCITIVA_*`) si `DB_ORA_DW_*` configurado.

## Reglas críticas

1. **Un solo `.py`** en `logica/` (auto-descubierto por `main.py`); subpaquete `logica/dwh/` es el pipeline real.
2. **Credenciales:** `project-config.json` es generado y gitignored — nunca se commitea. `environments/*.json` son versionados pero SOLO con credenciales dev locales; jamás credenciales de producción/remoto reales (usar placeholder `<...>`).
3. **Sin `${VAR}` literal** en logs = variable Hop mal definida.
4. **Rama por fase de servicio** (`fase-1`, `fase-2`, …); ver skill `auditable-soft-quarantine`. Rama portátil base: `linux`/`main`.
5. **CodeGraph** para entender/locar código: `.codegraph/` es índice local por máquina (gitignored); indexar con `codegraph init` y consultar vía MCP `codegraph_explore` (config global opencode) o CLI `codegraph explore "…"`.

Más detalle de plataforma, H2 gotchas y conexiones → [`docs/harness/platform.md`](docs/harness/platform.md).