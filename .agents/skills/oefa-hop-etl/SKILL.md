---
name: oefa-hop-etl
description: >-
  Apache Hop + H2 in-memory STG_* + Python ETL archetype for OEFA. Inputs Google
  Sheets / Excel local / Oracle SISUD / MySQL; staging H2 via inputs.yaml + Python DDL; logic
  in Python (logica/ at project root); output MySQL or Excel. Use when cloning the
  archetype, adding a STG source, wiring wf_main / wf_create_stg, debugging
  Hop/H2/Python logs, writing inputs.yaml, or choosing Hop-only vs Python logic.
  Portable for Cursor, OpenCode, and agents reading AGENTS.md.
---

# OEFA Hop ETL (arquetipo)

## When to use

Working in this archetype or a clone: new source, staging H2, `inputs.yaml`, capa de lógica Python, salida MySQL/Excel, o debug de un Play de Hop.

Contrato: `python/CONTRATO.md`. Capas y controles de calidad del entregable: [`../medallion-auditable/SKILL.md`](../medallion-auditable/SKILL.md).

**Plataforma: Linux.** Hop en `~/apps/hop`, Python en `.venv/`. Los `.bat` y `switch-env.ps1` quedan solo como referencia para Windows.

## Architecture (do not mix layers)

```
Sheets / Excel local / Oracle SISUD / MySQL
    -> inputs.yaml  (declara fuentes)
    -> Python DDL   (CREATE TABLE STG_* en H2; no extrae filas)
    -> Apache Hop   (extract: TableInput / GoogleSheetsInput / ExcelInput -> TableOutput)
    -> H2 mem:csep  (landing STG_*, reset each run)
    -> Python      (logica/: un solo .py, raiz del proyecto)
    -> MySQL or Excel
```

| Capa | Hace | No hace |
|---|---|---|
| `inputs.yaml` | Declara fuentes y nombre `STG_*` | Extraer filas |
| Python DDL | Introspecta schema vivo y crea DDL H2 (`create_stg.py`) | Cargar datos ni reglas de negocio |
| Hop | Extrae y trunca/carga `STG_*` | Lógica de negocio multi-fuente |
| Python lógica | Unión, reglas, esquema ancho (`logica/`) | Abrir conexiones dentro de `logica/` |

**Salida default de ETLs nuevos:** MySQL o Excel (`output/`). Oracle REPOCSEP es **legado** (nefa/diego/multa); no copiarlo a proyectos nuevos. Oracle SISUD es **fuente**.

## When Hop alone vs when Python logic

- **Hop solo**: 1 fuente → 1 destino, mapeo 1:1.
- **Python lógica**: UNION multi-fuente, reglas de negocio, esquema ancho, `#N/A` → NA.

Un solo `.py` en `logica/` (auto-descubierto por `python/main.py`). Entrada = claves de `LECTURAS` en `python/io/leer_h2.py`. Salida = DataFrame `RESULTADO` (`SALIDA_DF` en `main.py`). En `logica/` no hay drivers, jars ni conexiones. `pandas` se inyecta como `pd`.

## Workflow to run

Dos workflows. No mezclar diseño con corrida.

**Diseño** (H2 vivo para mapear en el GUI): `workflows/wf_create_stg.hwf`

1. Completar `inputs.yaml`
2. Play `wf_create_stg`: Reset H2 + `.venv/bin/python python/create_stg.py`
3. Success: H2 sigue en 9092 con `STG_*` vacías. Pintar `pl_stage_*.hpl` (TableOutput a esas tablas).

**Corrida / smoke**: `workflows/wf_main.hwf`

1. Reset H2 clean (`h2/scripts/reset_and_create.sh` → `00_reset.sql` + `01_schema.sql`)
2. Python create STG — `sources: []` = no-op; con fuentes, recrea `STG_*` (in-memory se borra en el reset)
3. Pipeline(s) de carga → `STG_*` (demo: `pl_demo.hpl`; extract se cablea **después** de Python)
4. Run Python (`python/main.py`) → Excel y, si hay credenciales, MySQL
5. Success

Verificación = Hop GUI Play + log. No hay suite de tests.

## Staging (opción B: Python después del reset)

No reescribir `h2/sql/01_schema.sql`. Orden:

1. Declarar fuentes en `inputs.yaml` (raíz). Contrato: [inputs.example.yaml](inputs.example.yaml).
2. Play `wf_create_stg` (diseño) o el paso Python de `wf_main` (corrida): introspecta, escribe `h2/sql/02_stg.sql` (gitignore) y aplica `CREATE TABLE STG_*` por JDBC. Detalle: [reference.md](reference.md).
3. Hop extrae hacia esas tablas (truncate + insert).
4. Cablear `pl_stage_*.hpl` en `wf_main.hwf` **después** de Python.
5. Añadir clave en `python/io/leer_h2.py` → `LECTURAS`.

Deps: `.venv/bin/python -m pip install -r python/requirements.txt`. `create_stg.py` **solo crea DDL**. Hop extrae. Sheets/Excel: todos VARCHAR (`#N/A`). `sources: []` = exit 0.

Convención de nombre: `STG_<ORIGEN>_<ENTIDAD>` (`STG_ORA_*`, `STG_MYSQL_*`, `STG_GS1_*`). Landing: todo nullable, VARCHAR sin longitud.

## Extending a new source (checklist)

1. Mapear columnas del objeto vivo. Los dumps de `../data_for_etl/input_examples/` (fuera del repo) son **mapeo**, no extractos de producción.
2. Añadir entrada en `inputs.yaml`.
3. Play `wf_create_stg` (H2 vivo) y crear `pipelines/pl_stage_*.hpl` (TableInput o GoogleSheetsInput → H2 TableOutput truncate).
4. Wire action + hops en `wf_main.hwf` **después** de Python create STG.
5. Extender `LECTURAS` + el único `.py` de `logica/`.
6. Salida: `python/io/escribir_mysql.py` o `escribir_excel.py` hacia `output/`. Oracle write = legado (`escribir_oracle.py`).
7. Actualizar `AGENTS.md`.

## Connections (variables only)

Fuente única: `project-config.json` → `config.variables`. Entorno: `./switch-env.sh local|remote`.

- `h2` → `DB_H2_*` (`jdbc:h2:tcp://localhost:9092/mem:csep;...MODE=Oracle...`, user `sa` / password `csep`)
- `oracle_sisud` → `DB_ORA_SISUD_*` (oefabd / SISUD, **fuente**)
- `mysql` → `DB_MYSQL_*` (fuente y/o **destino**)
- `oracle_repocsep` → `DB_ORA_REPO_*` (**legado**, no default)

Un `${VAR}` literal en el log = variable no definida o proyecto Hop activo equivocado.

Nunca commitear secretos: los passwords están en texto plano en `project-config.json` y `environments/*.json`. `client_secret.json` está en `.gitignore`.

## Hop gotchas already learned

- Sheets `#N/A` → String en Hop; VARCHAR en H2 (incl. montos).
- Workflow XML: escapar `&` como `&amp;` (ej. `2>&amp;1`, `&amp;&amp;`).
- Las acciones SHELL con `insertScript` corren en `sh`, no en bash: escribir POSIX y abrir con `set -e`.
- Reset H2 SHELL debe lanzar el server con `nohup`, en background y con stdout/stderr al log, o Hop se cuelga esperando los descriptores.
- No llamar al paquete `python/io` con `import io`: choca con la stdlib. `main.py` carga esos módulos por ruta.
- H2 in-memory: vacía si el server se reinició sin una corrida de staging.
- Registrar el proyecto con `hop-conf.sh --project-create` **sin** `--project-keep-config-file` sobrescribe `project-config.json` y borra las variables.

## Additional resources

- Tipos STG, introspección por fuente, flujo Python: [reference.md](reference.md)
- Contrato del manifiesto: [inputs.example.yaml](inputs.example.yaml)
- Capas, QA y trazabilidad del entregable: [`../medallion-auditable/SKILL.md`](../medallion-auditable/SKILL.md)
