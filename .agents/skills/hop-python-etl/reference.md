# Referencia — staging H2 y tipos

Ver [SKILL.md](SKILL.md) para arquitectura. Detalle de introspección y pipelines.

## Introspección (`python/create_stg.py`)

Opción **B**: Reset H2 primero; Python lee `inputs.yaml`, introspecta, escribe `h2/sql/02_stg.sql` (gitignore) y aplica JDBC.

| type | Conexión | object |
|---|---|---|
| oracle | `DB_ORA_SISUD_*` | `OWNER.NOMBRE` |
| mysql | `DB_MYSQL_*` | `schema.tabla` |
| sheets | `client_secret.json` | `spreadsheet_key` + `worksheet` |
| excel | path relativo | `worksheet` + `header_row` (1-based) |

Sheets/Excel: **todos VARCHAR** (gotcha `#N/A`). Landing: nullable, sin PK.

## Convención `STG_*`

| Origen | Prefijo |
|---|---|
| Oracle | `STG_ORA_` |
| MySQL | `STG_MYSQL_` |
| Sheets libro N | `STG_GSN_` |
| Excel | `STG_GSN_` o prefijo acordado |

Una fuente = una tabla STG. No UNION en H2.

## Orden wf_main

```
Reset H2 → Python create STG → pl_stage_* → Run Python → Success
```

Python create STG va **antes** de los pipelines de extract (in-memory se borra en reset).

## Capa post-staging

- Lectura: `python/io/leer_h2.py` → `LECTURAS`
- Escritura Oracle DW: `python/io/cargar_dw.py` (formal DDL + TRUNCATE+INSERT)
- Escritura Excel smoke: `output/resultado.xlsx`
- `python/io/escribir_dw.py` legacy VARCHAR — no usar para `DIM_`/`FACT_`

## Debug rápido

| Síntoma | Revisar |
|---|---|
| STG en 0 filas | Hop staging omitido (credenciales `<...>`) o pipeline no cableado |
| Lógica no ve tabla | Falta clave en `LECTURAS` |
| `Value too long` en H2 | VARCHAR con longitud; quitar longitud en DDL |
| Python lento | Normal con miles de filas de multa; Oracle insert es el cuello |
