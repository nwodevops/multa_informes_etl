# python/ — dos capas, dos entry points

Hop llama **solo** estos dos scripts. No mezclar.

| Capa | Cuándo | Entry | Carpeta | Hace | No hace |
|---|---|---|---|---|---|
| **STG / DDL** | Antes del extract Hop | `create_stg.py` | `introspect/` | Lee `inputs.yaml`, introspecta schema, `CREATE TABLE STG_*` | Extraer filas, reglas de negocio |
| **Post-staging** | Después de que Hop cargó `STG_*` | `main.py` | `python/io/` + `logica/` (raíz) | Lee H2, transforma (enrich pandas), carga Oracle flaco | Introspectar fuentes, crear STG |

```
inputs.yaml  →  create_stg.py  →  introspect/     →  H2 tablas vacías
Hop extract  →  STG_* con filas (F1 Sheets / F2 Sheets+etapas / F5 SISUD; sin MySQL)
main.py      →  io/leer_h2     →  ../logica/*.py (enrich.py)  →  io/cargar_dw (wipe+DDL+INSERT)
```

`config.py` y `h2_conn.py` son **compartidos** (variables Hop + JDBC H2). No son una tercera capa de negocio.

`logica/` no abre conexiones. `io/` no llama a `introspect/`. `introspect/` no lee filas de negocio.

Contrato de I/O: [`CONTRATO.md`](CONTRATO.md). Manual del fact: [`../docs/lineamientos/extra/manual-como-se-arma-el-fact.md`](../docs/lineamientos/extra/manual-como-se-arma-el-fact.md).
