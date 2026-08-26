# python/io/ — I/O post-staging

Hop ya cargó `STG_*`. Aquí solo lectura H2 y carga Oracle DW.

| Archivo | Rol |
|---|---|
| `leer_h2.py` | ENTRADA: `LECTURAS` → DataFrames para `logica/` |
| `cargar_dw.py` | SALIDA: DDL formal + TRUNCATE+INSERT `MI_*` → Oracle (`DB_ORA_DW_*`) |

No crear `STG_*`. No introspectar fuentes. Eso es `python/introspect/` vía `create_stg.py`.

No `import io` (choca con stdlib). `main.py` carga estos módulos por ruta.

Escritores legacy (`escribir_excel` / `escribir_mysql` / `escribir_oracle` / `escribir_dw` VARCHAR) **eliminados** — no los usa este proyecto.
