# AGENTS.md — mapa para agentes

ETL **Apache Hop + H2 in-memory + Python** (OEFA). Requerimiento: [`docs/TDR REQ 3629-2026.pdf`](docs/TDR%20REQ%203629-2026.pdf).

| Doc | Para qué |
|---|---|
| [`docs/README.md`](docs/README.md) | Índice de toda la carpeta docs |
| [`docs/vista-general.md`](docs/vista-general.md) | Mermaid alto nivel: fuentes → STG → Python → DW |
| [`docs/modelo-kimball.md`](docs/modelo-kimball.md) | Estrella `MI_DIM_*` / `MI_FACT_*` |
| [`docs/arquitectura.md`](docs/arquitectura.md) | Detalle Hop + H2 + Python |
| [`docs/fases/status.md`](docs/fases/status.md) | Semáforo fases 1–7 |
| [`docs/verification.md`](docs/verification.md) | Cómo demostrar HARNESS OK |

> **Arquetipo base:** plantilla mínima en [`archetype/README.md`](archetype/README.md) (regenerar con `./scripts/sync_archetype.sh`). Este repo es la implementación de referencia consultoría.

**Verificación:** Linux [`./init.sh`](init.sh) o Windows `init.bat` / Hop `wf_main_win.hwf` → **`HARNESS OK`**. Criterios: [`CHECKPOINTS.md`](CHECKPOINTS.md).

**Rama activa Win:** `windows` (ver [`feature_list.json`](feature_list.json)).

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

Lineamiento canónico: [`docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md`](docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md).

## Inicio rápido

```bash
# Linux
./switch-env.sh local    # o remote
./init.sh                # → HARNESS OK
~/apps/hop/hop-gui.sh    # wf_main.hwf
```

```powershell
# Windows (rama windows)
.\switch-env.ps1 remote
# Hop: D:\Eder\hop → proyecto multa_informes_etl → wf_main_win.hwf
# o: init.bat  (log en output\init_win_*.log)
# Hop path típico: D:\Eder\hop\hop-run.bat ; Python: .venv\Scripts\python.exe
```

Flujo datos: `inputs.yaml` → Hop `STG_*` → `python/main.py` → `logica/` → Oracle DW (`cargar_dw.py`) si `DB_ORA_DW_*` configurado.

**DW schema:** `cargar_dw.py` usa el **USER Oracle de la sesión** (`APP` local, `REPOCSEP` remote). No forzar `APP.` si el login es otro usuario.

## Reglas críticas

1. **Un solo `.py`** en `logica/` (auto-descubierto por `main.py`).
2. **Sin secretos** en git (`project-config.json`, `environments/`). Ref humana: [`docs/credenciales/`](docs/credenciales/).
3. **Sin `${VAR}` literal** en logs = variable Hop mal definida.
4. **Rama por fase / entorno** (`fase-1`, `windows`, …); ver skill `auditable-soft-quarantine`.
5. CodeGraph (Python/YAML): skill global `~/.agents/skills/codegraph/SKILL.md`.

Más detalle de plataforma, H2 gotchas y conexiones → [`docs/harness/platform.md`](docs/harness/platform.md).
