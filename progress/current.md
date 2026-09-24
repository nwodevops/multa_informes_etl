# Sesión activa — rama `linux_v3`

## Feature activa

`dual-write-mysql-dw` (`in_progress`).

## Hecho reciente

- Rama `linux_v3` desde `linux_v2`.
- Espejo MySQL DW: `DB_MYSQL_DW_*` + `cargar_dw_mysql` / `cargar_aud_mysql` (soft-fail).

## Siguiente

1. `./switch-env.sh local` (regenera `project-config.json` con `DB_MYSQL_DW_*`).
2. Corrida `wf_main` / `./init.sh` → ver `DW-MYSQL:` y `AUD-MYSQL:` en log.
3. En MySQL `localhost:3307/gappsdb`: `SELECT COUNT(*) FROM DW_M_FACT_MULTA_COERCITIVA`.
