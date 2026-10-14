### Anexo A — Matriz de correspondencia de fuentes (extracto)

Inventario runtime: [`docs/inputs/README.md`](../../../inputs/README.md).

> **F4 gappsdb es histórico** (fuera de ingestión; solo semilla `GAPPS` en dim). Fuentes activas: F1, F2, F5. Lookup negocio: Sheet←SISUD.

| Concepto | F1 Sheets OD (31) | F2 Sheets CSEP (10) | F4 gappsdb (hist.) | F5 Vista Oracle | Modelo (`DW_M_*`) |
|---|---|---|---|---|---|
| Medida administrativa | `COD_MA` | `COD_MA` / `AUX_COD_MA` | — | (en `MEDIDA_ADMINISTRATIVA`) | `COD_MA` |
| Código CUM | — | — | `TX_IDCUM` | `CUM` | `CUM` (enrich desde SISUD) |
| Código CAM | — | — | `TX_IDCAM` | `CAM` | `CAM` (enrich desde SISUD) |
| Expediente supervisión | `EXP_INF_INCUMP` | `EXP_INF_INCUMP` | — | `NUMERO_EXPEDIENTE` | `NUMERO_EXPEDIENTE` |
| Resolución MC | `N_RES_MC` | `N_RES_MC` | — | `RESOLUCION` | `N_RES_MC` (+ clave lookup) |
| Monto UIT | `MULTA_UIT` | `MULTA_UIT` | `NU_MONTOMCUIT` | `MONTO_MULTA` | `MONTO_UIT` (+ clave lookup) |
| Monto S/ | `MULTA_S` | `MULTA_S` | `NU_MONTOMCS` | — | `MONTO_S` |
| Estado multa | `ESTADO_MC` | `ESTADO_MC` / `AUX_EST_MC` | `FG_ESTADOMULTA` | `ESTADO_MULTA` | `ID_ESTADO_MULTA` (homologado) |
| Verificación post-MC | `F_VERIF_POST_MC`, `DOC_VERIF_MC` | `F_VERIF_POST_MC`, `DOC_VERIF_MC` | `FE_F_VERIF_POST_MC`, `TX_DOC_VERIF_MC` | — | `F_VERIF_POST_MC`, `DOC_VERIF_MC` |
| SIGED | `SIGED` | `SIGED`, `EXP_SIGED_DOC` | `TX_EXP_SIGED_DOC` | `NUMERO_REGISTRO` | `SIGED` |
| Territorio / unidad | `COD_OD` → `DW_M_DIM_OD` | `COORD`/`COD_UNIDAD` → `DW_M_DIM_ORGANO_UNIDAD` (`DESCRIPCION`) | — | — | dims |
| Universo de origen | `OD_SHEETS` | `CAGR` | `GAPPS` (semilla) | `SISUD_VW` | `ID_FUENTE` → `DW_M_DIM_FUENTE_REGISTRO` (vistas `VW_MC_*`) |
