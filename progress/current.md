# Sesión — atributos operativos Sheet (P0)

## Feature activa

| ID | Status |
|---|---|
| `fact-attrs-operativos-sheet` | in_progress |

## Diseño

Passthrough F2 → facts (mismo shape CSEP/OD/SISUD + enriquecida):

`JEFE`, `UF`, `N_PROY_MC`, `ETA_REG_PROY_MC`, `ETA_REG_MC`, `RESULT_PROY_MC`, `ESTADO_MC_TXT`, `ESTADO_PAGO_TXT`.

Sin refactor del enrich Maggi (07). OD/SISUD: NULL donde no aplica.

## Criterio

`ID_MC` caso `0153-2026` → `JEFE = MEJIA, HOMERO`; `./init.sh` HARNESS OK.
