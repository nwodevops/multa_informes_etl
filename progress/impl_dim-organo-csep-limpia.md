# impl — dim-organo-csep-limpia

## Cambio

`DW_M_DIM_ORGANO_UNIDAD` deja de incorporar siglas derivadas de `NUMERO_EXPEDIENTE` / valores libres de `COORD` fuera de catálogo.

- Semilla: 10 `cod_unidad` activos de `docs/inputs/f2_csep_sheets.json` + ND.
- Hecho: `ID_ORGANO` por `COORD` → `COD_UNIDAD` → último token de expediente **solo si** es CSEP conocida; si no, `-1`.

## Archivos

- `logica/dwh/dimensional.py`
- `docs/modelo-kimball.md`
- `docs/adjuntos/modelo-kimball.md`
- `docs/lineamientos/ANEXO_MAPEO_CAMPOS.md`
- `feature_list.json`

## Verificación

`./init.sh` → HARNESS OK; `COUNT(*)` de `DW_M_DIM_ORGANO_UNIDAD` ≈ 11.
