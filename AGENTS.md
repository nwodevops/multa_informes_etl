# AGENTS.md — mapa para agentes (rama `windows`)

ETL **Apache Hop + H2 in-memory + Python** (OEFA) — **esta rama es exclusiva Windows**.

Requerimiento: [`docs/TDR REQ 3629-2026.pdf`](docs/TDR%20REQ%203629-2026.pdf).

| Doc | Para qué |
|---|---|
| [`docs/README.md`](docs/README.md) | Índice docs |
| [`docs/vista-general.md`](docs/vista-general.md) | Fuentes → STG → Python → DW |
| [`docs/modelo-kimball.md`](docs/modelo-kimball.md) | Estrella `MI_DIM_*` / `MI_FACT_*` |
| [`docs/arquitectura.md`](docs/arquitectura.md) | Detalle Hop + H2 + Python |
| [`docs/fases/status.md`](docs/fases/status.md) | Semáforo fases 1–7 |
| [`docs/verification.md`](docs/verification.md) | Cómo demostrar que funciona |

> **Arquetipo base:** plantilla mínima `archetype/` (no versionado; regenerar con `./scripts/sync_archetype.sh`). Este repo es la implementación de referencia consultoría.

> Linux / harness genérico: rama `main`. Aquí no mezclar flujos `init.sh` / `wf_main.hwf` como camino primario.

**Verificación Win:** `.\switch-env.ps1 remote` + `init.bat` **o** Hop `wf_main_win.hwf` → Success / **HARNESS OK**. Criterios: [`CHECKPOINTS.md`](CHECKPOINTS.md).

## Harness

| Archivo | Propósito |
|---|---|
| [`feature_list.json`](feature_list.json) | Alcance; **una** `in_progress` |
| [`progress/current.md`](progress/current.md) | Plan sesión |
| [`progress/history.md`](progress/history.md) | Bitácora |
| [`docs/harness/workflow.md`](docs/harness/workflow.md) | Roles |
| [`docs/harness/platform.md`](docs/harness/platform.md) | Hop, H2, variables |

## Skills

- [`.agents/skills/hop-python-etl/SKILL.md`](.agents/skills/hop-python-etl/SKILL.md)
- [`.agents/skills/phased-dwh-lineamiento/SKILL.md`](.agents/skills/phased-dwh-lineamiento/SKILL.md)
- [`.agents/skills/auditable-soft-quarantine/SKILL.md`](.agents/skills/auditable-soft-quarantine/SKILL.md)
- [`.agents/skills/oracle-cargar-dw/SKILL.md`](.agents/skills/oracle-cargar-dw/SKILL.md)

Lineamiento canónico: [`docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md`](docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md). Status: [`docs/fases/status.md`](docs/fases/status.md). DDL DW: [`docs/lineamientos/ddl/`](docs/lineamientos/ddl/).

## Inicio rápido (Windows)

```powershell
cd D:\Eder\workspace_etl_oefa\multa_informes_etl
git checkout windows
git pull
.\switch-env.ps1 remote

# Opción A — harness
init.bat
# log: output\init_win_YYYYMMDD_HHMMSS.log

# Opción B — Hop GUI
# Hop en D:\Eder\hop → proyecto multa_informes_etl → wf_main_win.hwf → Play
```

Prerrequisitos Win:

- Java en PATH (H2)
- `.venv` + `pip install -r python\requirements.txt`
- `input_excel\*.xlsx`
- Hop: `D:\Eder\hop\hop-run.bat` (o `set HOP_RUN=...`)
- Red/VPN a Oracle SISUD, MySQL GAPP, Oracle DW (`REPOCSEP` @ `10.6.0.15`)

Flujo: `inputs.yaml` → Hop `STG_*` → `python/main.py` → `logica/ejecutar.py` (auto-descubierto) → `logica/dwh/pipeline.py` (fases 2–7) → `cargar_dw.py` (TRUNCATE+INSERT, esquema = **USER** Oracle, p.ej. `REPOCSEP`).

## Python (esta rama)

```text
python/
  create_stg.py / main.py / verify_dw.py
  config.py / h2_conn.py / plantilla_logica.py
  introspect/     # DDL STG
  io/leer_h2.py   # entrada
  io/cargar_dw.py # salida DW
```

Sin escritores legacy (`escribir_*`). Contrato: [`python/CONTRATO.md`](python/CONTRATO.md).

## Reglas críticas

1. **Un solo `.py`** en `logica/` (auto-descubierto por `main.py`); subpaquete `logica/dwh/` es el pipeline real.
2. **Credenciales:** `project-config.json` es generado y gitignored — nunca se commitea. `environments/*.json` son versionados pero SOLO con credenciales dev locales; jamás credenciales de producción/remoto reales (usar placeholder `<...>`).
3. **Sin `${VAR}` literal** en logs = variable Hop mal definida.
4. **Rama por fase de servicio** (`fase-1`, `fase-2`, …); esta rama = **solo Windows**; no portar aquí como default el flujo Linux.
5. **CodeGraph** para entender/locar código: `.codegraph/` es índice local por máquina (gitignored); indexar con `codegraph init` y consultar vía MCP `codegraph_explore` (config global opencode) o CLI `codegraph explore "…"`.

Plataforma / H2: [`docs/harness/platform.md`](docs/harness/platform.md).