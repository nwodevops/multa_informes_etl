### Anexo A — Matriz de correspondencia de fuentes (extracto)

| Concepto | F1 Excel OD Lamb. | F2 Excel CAGR | F4 gappsdb | F5 Vista Oracle | Modelo (`dm`) |
|---|---|---|---|---|---|
| Medida administrativa | `COD_MA` | `COD_MA` / `AUX_COD_MA` | — | (en `MEDIDA_ADMINISTRATIVA`) | `COD_MA` |
| Código CUM | — | — | `TX_IDCUM` | `CUM` | `CUM` (normalizado) |
| Código CAM | — | — | `TX_IDCAM` | `CAM` | `CAM` (normalizado) |
| Expediente supervisión | `EXP_INF_INCUMP` | `EXP_INF_INCUMP` | — | `NUMERO_EXPEDIENTE` | `NUMERO_EXPEDIENTE` |
| Resolución MC | `N_RES_MC` | `N_RES_MC` | — | `RESOLUCION` | `N_RES_MC` |
| Monto UIT | `MULTA_UIT` | `MULTA_UIT` | `NU_MONTOMCUIT` | `MONTO_MULTA` | `MONTO_UIT` (conciliado R07) |
| Monto S/ | `MULTA_S` | `MULTA_S` | `NU_MONTOMCS` | — | `MONTO_S` |
| Estado multa | `ESTADO_MC` | `ESTADO_MC` / `AUX_EST_MC` | `FG_ESTADOMULTA` | `ESTADO_MULTA` | `ID_ESTADO_MULTA` (homologado) |
| Verificación post-MC | `F_VERIF_POST_MC`, `DOC_VERIF_MC` | `F_VERIF_POST_MC`, `DOC_VERIF_MC` | `FE_F_VERIF_POST_MC`, `TX_DOC_VERIF_MC` | — | `F_VERIF_POST_MC`, `DOC_VERIF_MC` |
| SIGED | `SIGED` | `SIGED`, `EXP_SIGED_DOC` | `TX_EXP_SIGED_DOC` | `NUMERO_REGISTRO` | `SIGED` |
