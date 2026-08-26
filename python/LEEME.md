# python/ — dos capas, dos entry points

Hop llama **solo** estos scripts. No mezclar capas.

| Capa | Cuándo | Entry | Carpeta | Hace | No hace |
|---|---|---|---|---|---|
| **STG / DDL** | Antes del extract Hop | `create_stg.py` | `introspect/` | `inputs.yaml` → schema → `CREATE TABLE STG_*` | Filas, negocio |
| **Post-staging** | Tras Hop cargar `STG_*` | `main.py` | `io/` + `logica/` | Leer H2 → lógica → Oracle DW | Introspect / crear STG |
| **Verify** | Manual / smoke | `verify_dw.py` | — | COUNT en Oracle DW | Correr ETL |

```
inputs.yaml  →  create_stg.py  →  introspect/     →  H2 tablas vacías
Hop extract  →  STG_* con filas
main.py      →  io/leer_h2     →  ../logica/*.py  →  io/cargar_dw
verify_dw.py →  COUNT MI_* en Oracle (misma conexión DW)
```

## Estructura

```text
python/
  create_stg.py      # entry STG
  main.py            # entry lógica + carga DW
  verify_dw.py       # conteos Oracle post-carga
  config.py          # project-config.json + inputs.yaml
  h2_conn.py         # JDBC H2
  plantilla_logica.py  # plantilla para logica/ (no ejecutar aquí)
  CONTRATO.md
  LEEME.md
  requirements.txt
  introspect/        # schema vivo → DDL (excel, oracle, mysql, sheets)
  io/
    leer_h2.py       # ENTRADA
    cargar_dw.py     # SALIDA Oracle dimensional
    LEEME.md
```

`config.py` y `h2_conn.py` son **compartidos**. `logica/` no abre conexiones. `io/` no llama a `introspect/`.
