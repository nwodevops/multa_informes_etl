# AGENTS.md

Proyecto ETL en **Apache Hop** (OEFA), copia del arquetipo (original fuera del repo: `~/Documents/desarrollo/workspace_oefa/archetype`). No hay build/test/lint: la verificación es ejecutar el workflow en el GUI de Hop y revisar el log.

Requerimiento del proyecto: [`docs/TDR REQ 3629-2026.pdf`](docs/TDR%20REQ%203629-2026.pdf) — consolidar y validar informes de supervisión y multas coercitivas, con controles de calidad, trazabilidad entre capas e indicadores de efectividad.

Vista general con diagramas y qué hace la capa de lógica: [`docs/arquitectura.md`](docs/arquitectura.md).

**Skills del proyecto:**
- [`.agents/skills/oefa-hop-etl/SKILL.md`](.agents/skills/oefa-hop-etl/SKILL.md) — arquetipo Hop + H2 + Python (cómo cablear, extender y debuggear).
- [`.agents/skills/medallion-auditable/SKILL.md`](.agents/skills/medallion-auditable/SKILL.md) — capas `STG_`/`INT_`/`FCT_`/`VW_`/`IND_`/`QA_`, cuarentena blanda, efectividad por embudo y **una rama por fase**.

Patrón canónico de ETLs nuevos: inputs Sheets / Excel local / Oracle SISUD / MySQL → `inputs.yaml` + Python DDL → Hop extract → H2 `STG_*` → Python (`logica/` en la raíz) → **MySQL o Excel**. Oracle REPOCSEP es legado (no default).

## Fases del servicio

Cada entregable del TDR se trabaja en su propia rama git, no en carpetas por fase: `fase-1` (actividades a, b, c), `fase-2` (d, e, f) y `fase-3` (g, h). `fase-2` sale de `fase-1`, no de `master`. Reglas y qué capas toca cada fase: la skill `medallion-auditable`.

Hoy el repo **todavía no tiene git**; el arquetipo se inicializa al arrancar el ETL. Antes del primer commit, revisar que `project-config.json` y `environments/*.json` no lleven passwords reales.

## Plataforma: Linux

Este proyecto está portado a Linux. Los `.bat` y `switch-env.ps1` quedan solo como referencia para Windows; los workflows llaman a los `.sh`.

- Apache Hop 2.19.0 en `~/apps/hop` (GUI: `~/apps/hop/hop-gui.sh`). Proyecto `etl_cursor` ya registrado en `~/apps/hop/config/hop-config.json`.
- Java 21 en PATH. R **no** se usa en esta rama (`capa-python`); la lógica corre con el venv.
- Python: venv del proyecto en `.venv/` (el sistema es *externally managed*, PEP 668). Crear con `python3 -m venv --without-pip .venv` + `get-pip.py`, luego `.venv/bin/python -m pip install -r python/requirements.txt`. Los workflows usan `.venv/bin/python` si existe, si no `python3`.
- Fuentes locales de prueba (Oracle XE + MySQL 8): `../data_for_etl/docker-compose.yml`.

## Ejecución y flujo

- **Diseño:** `workflows/wf_create_stg.hwf`. Cadena: `Reset H2 clean` → `Python create STG` → `Success`. Deja H2 vivo (9092) para mapear `STG_*` en el GUI.
- **Corrida / smoke:** `workflows/wf_main.hwf`. Cadena: `Reset H2 clean` → `Python create STG` → `Stage Excel` → `Stage Oracle VW` → `Stage Informes` → `Stage MySQL` → `Pipeline demo` → `Run Python`.
- Cada corrida de cualquiera de los dos **resetea la BD H2** (stop + start + DDL) vía `h2/scripts/reset_and_create.sh`.
- Staging STG: `inputs.yaml` + `.venv/bin/python python/create_stg.py` (opción B: DDL JDBC **después** del reset). Excel local en `input_excel/` (`type: excel`, todo VARCHAR).
- Smoke test sin Hop: `./h2/scripts/reset_and_create.sh && .venv/bin/python python/create_stg.py && .venv/bin/python python/main.py`.
- Archivos `.hpl`/`.hwf` son XML con variables `${PROJECT_HOME}`.

## Capa de lógica (Python, aislada)

- La lógica de negocio vive en `logica/` (raíz del proyecto, **fuera** de `python/`): **zona de pegado** con un solo `.py` (auto-descubierto por `python/main.py`; error si hay 0 o más de 1). Copy-paste ahí y corre.
- Entrada: DataFrames ya cargados con los nombres de `LECTURAS` en `python/io/leer_h2.py`. Salida: DataFrame `RESULTADO` (`SALIDA_DF` configurable en `main.py`). Ver `python/CONTRATO.md`.
- Aislamiento: en `logica/` no hay conexiones ni jars ni drivers; el I/O vive en `python/io/`. `pandas` se inyecta como `pd`.
- `python/create_stg.py` + `python/introspect/`: **capa STG/DDL** (schema, no filas). `python/main.py` + `python/io/` + `logica/`: **capa post-staging**. Ver `python/LEEME.md`.
- Smoke: escribe `output/resultado.xlsx`. MySQL y Oracle se omiten si las credenciales son placeholders `<...>`.

## H2 (server local, in-memory)

- BD **in-memory** `mem:csep` (`jdbc:h2:tcp://localhost:9092/mem:csep;...MODE=Oracle...`). Se limpia sola al parar el server.
- El DDL se aplica por TCP **después** del start: `h2/scripts/reset_and_create.sh` → `h2/sql/00_reset.sql` (DROP ALL) + `h2/sql/01_schema.sql` (DDL del proyecto).
- Requiere `java` en PATH; jar `h2/lib/h2-2.4.240.jar`. Log del server: `h2/h2_server.log` (gitignore).
- Si el workflow se queda pegado en `Reset H2 clean`, revisar procesos java/H2 huérfanos (`h2/scripts/stop_h2.sh`).
- **Gotcha**: el `java ... org.h2.tools.Server` de `h2/scripts/start_h2.sh` debe ir con `nohup`, en background y con stdout/stderr redirigidos al log; si hereda los descriptores, la acción SHELL de Hop espera para siempre.

## Variables (crítico)

- **Fuente única**: `project-config.json` → `config.variables`. Un `${VAR}` literal en el log = variable no definida o proyecto activo equivocado.
- Cambio de entorno: `./switch-env.sh local|remote` copia `environments/<env>.json` → `project-config.json`.
- El proyecto activo se elige en `~/apps/hop/config/hop-config.json` (fuera del repo): debe ser `etl_cursor`. No editar ese config a mano; usar `~/apps/hop/hop-conf.sh --project-create ... --project-keep-config-file` (sin ese flag, Hop sobrescribe `project-config.json` y te borra las variables).

## Conexiones

- `metadata/rdbms/*.json` referencian variables:
  - `h2` (`DB_H2_*`), lista por defecto.
  - `oracle_sisud` (`DB_ORA_SISUD_*`): Oracle **oefabd** (SISUD, fuente).
  - `oracle_repocsep` (`DB_ORA_REPO_*`): Oracle **REPOCSEP** (destino).
  - `mysql` (`DB_MYSQL_*`).
  - Completar los placeholders `<...>` en `project-config.json` o `environments/`.

## Credenciales y secretos

- Passwords en texto plano dentro del repo (`project-config.json`, `environments/*.json`): no commitear ni propagar.
- Si se usa Google Sheets, `client_secret.json` (service account) va en la raíz y está en `.gitignore`.

## CodeGraph (knowledge graph del código)

- **Skill** (global, fuera del repo): `~/.agents/skills/codegraph/SKILL.md`.
- MCP instalado globalmente (`@colbymchenry/codegraph`), registrado en `~/.cursor/mcp.json` (Cursor) y `~/.config/opencode/opencode.json` (OpenCode). Los 8 tools se habilitan con `CODEGRAPH_MCP_TOOLS`: `explore`, `search`, `node`, `callers`, `callees`, `impact`, `files`, `status`.
- Indexado: `.codegraph/` en la raíz (16 archivos, 95 nodes, 178 edges; gitignore). Re-indexar con `codegraph index` (full) o `codegraph sync` (delta).
- **Solo indexa Python y YAML.** Los `.hpl`/`.hwf` de Hop, los `.sql` y los `.sh` **no** están en el grafo: para esos hay que usar grep/lectura directa.
- Re-indexar después de cambios grandes en `python/`.
