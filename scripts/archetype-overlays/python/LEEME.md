# python/ — dos capas, dos entry points

Hop llama **solo** estos dos scripts. No mezclar.

| Capa | Cuándo | Entry | Carpeta | Hace | No hace |
|---|---|---|---|---|---|
| **STG / DDL** | Antes del extract Hop | `create_stg.py` | `introspect/` | Lee `inputs.yaml`, `CREATE TABLE STG_*` | Extraer filas, reglas |
| **Post-staging** | Después de que Hop cargó STG / demo | `main.py` | `python/io/` + `logica/` | Lee H2, transforma, escribe Excel | Introspectar fuentes |

```
inputs.yaml  →  create_stg.py  →  introspect/     →  H2 tablas vacías
Hop extract  →  STG_* con filas (si hay fuentes)
main.py      →  io/leer_h2     →  logica/*.py     →  io/escribir_excel
```

Smoke del cascarón: `sources: []` → solo `DEMO_TABLA_EJEMPLO` (DDL en `h2/sql/01_schema.sql`).

`config.py` y `h2_conn.py` son compartidos (variables Hop + JDBC H2).

`logica/` no abre conexiones. `io/` no llama a `introspect/`.

Contrato: [`CONTRATO.md`](CONTRATO.md).
