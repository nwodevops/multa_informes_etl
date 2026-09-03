# Plataforma y ejecución (detalle)

Divulgación progresiva desde [`AGENTS.md`](../../AGENTS.md). Requerimiento: [`docs/TDR REQ 3629-2026.pdf`](../TDR%20REQ%203629-2026.pdf).

## Linux

- Apache Hop 2.19.0 en `~/apps/hop` (GUI: `~/apps/hop/hop-gui.sh`).
- Java 21 en PATH.
- Python: venv en `.venv/` (PEP 668). Instalar deps: `python/requirements.txt`.
- Fuentes locales de prueba: `../data_for_etl/docker-compose.yml` (Oracle XE + MySQL 8).

## Workflows

| Workflow | Uso |
|---|---|
| `workflows/wf_create_stg.hwf` | Diseño: Reset H2 → Python STG → H2 vivo en 9092 |
| `workflows/wf_main.hwf` | Corrida: Reset → STG → stage Excel/Oracle/MySQL → Python |

Smoke sin Hop: [`./init.sh`](../../init.sh) o manualmente:

```bash
./h2/scripts/reset_and_create.sh && .venv/bin/python python/create_stg.py && .venv/bin/python python/main.py
```

## Capa de lógica

- Un solo `.py` en `logica/` (hoy: `ejecutar.py`).
- Entrada: DataFrames `LECTURAS` (`python/io/leer_h2.py`).
- Contrato: [`python/CONTRATO.md`](../../python/CONTRATO.md).
- Lógica DW: `logica/dwh/` (orquestada por `pipeline.py`).

## H2

- BD in-memory `mem:csep`, TCP `9092`, modo Oracle.
- Reset: `h2/scripts/reset_and_create.sh` → `00_reset.sql` + `01_schema.sql`.
- **Gotcha:** `start_h2.sh` debe usar `nohup` y redirigir stdout; si no, Hop se queda colgado en Reset.

## Variables

- Fuente única: `project-config.json` → `config.variables`.
- Entorno: `./switch-env.sh local|remote`.
- Proyecto Hop activo en `~/apps/hop/config/hop-config.json` (fuera del repo).

## Conexiones

| Metadata | Variables | Uso |
|---|---|---|
| `h2` | `DB_H2_*` | Staging |
| `oracle_sisud` | `DB_ORA_SISUD_*` | Fuente SISUD (solo F5 `VW_MULTA_COERCITIVA`; sandbox local: `localhost:1525/CSEP`) |
| `oracle_dw` | `DB_ORA_DW_*` | Destino DW (carga Fase 6–7; local: `localhost:1524/BD_CURSOR`) |
| `oracle_BD_CURSOR` | `DB_ORA_REPO_*` | Legado |
| `mysql` | `DB_MYSQL_*` | Fuente GAPP |

## Secretos

No commitear passwords reales. `client_secret.json` (Sheets) en raíz, gitignore.

## CodeGraph

Skill global: `~/.agents/skills/codegraph/SKILL.md`. Indexa Python y YAML; no `.hpl`/`.hwf`/`.sql`.
