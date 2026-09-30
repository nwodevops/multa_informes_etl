# dual-write-mysql-dw

## Qué

Tras la carga Oracle (`DB_ORA_DW_*`), el mismo canónico (dims + `DW_M_FACT_MULTA_COERCITIVA` + DET + DQ + `DW_M_AUD_*`) se publica en MySQL OUTPUT (`DB_MYSQL_DW_*`).

## Separación de conexiones

| Prefijo | Uso |
|---|---|
| `DB_MYSQL_*` | INPUT F4 (Hop `pl_stage_mysql`) |
| `DB_MYSQL_DW_*` | OUTPUT espejo DW |

Local OUTPUT: `localhost:3307/gappsdb`. Remote OUTPUT: `10.1.1.217:3306/gappsdb`.

## Código

- `python/io/cargar_dw_mysql.py` — wipe `DW_M_%` + DDL inferido + INSERT
- `python/audit/cargar_aud_mysql.py` — AUD VARCHAR
- `python/main.py` — Oracle primero; MySQL soft-fail

No se tocan tablas `T_MVC_*` ni facts evidencia `DW_M_FACT_MC_*`.

## Verificación

Log: `DW-MYSQL: … OK` y `AUD-MYSQL: …`. Si MySQL DW cae: `AVISO` y Success igual (Oracle intacto).
