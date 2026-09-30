# Sesión activa — rama `windows_v3`

## Feature activa

`dual-write-mysql-dw` (`in_progress`, traída de `linux_v3`).

## Hecho reciente

- Merge de `aud-pk-oficina` sobre `windows_v3` (2 conflictos a mano: `python/main.py`, `python/CONTRATO.md`).
- `PK_OFICINA` en `DW_M_AUD_F1_OD_MULTAS` (282/282) y `DW_M_AUD_F2_CSEP_MULTAS` (994/994), derivada de `T_SEP_OFICINA.TX_DESCRIPCION`.
- `init.bat` → **HARNESS OK**, exit 0. Log `output/init_win_20260930_114519.log`.
- Pruebas 7/7 unit + 7/7 e2e contra MySQL real.
- Evidencia: `progress/impl_aud-pk-oficina.md`.

## Siguiente

1. Confirmar en el log que el espejo MySQL publicó la columna: `AUD-MYSQL:` en `output/init_win_*.log`.
2. En MySQL OUTPUT: `SELECT COUNT(*), COUNT(PK_OFICINA) FROM DW_M_AUD_F1_OD_MULTAS;` y la F2.
3. Cerrar `dual-write-mysql-dw` → `done` en `feature_list.json` cuando el espejo esté verificado.
4. Luego `fase-remote-deploy` (único `pending`).
