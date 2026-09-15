# Qué no entra al fact

Columnas (y, en SISUD, filas) que **sí se descargan** pero **no alimentan** `DW_M_FACT_MULTA_COERCITIVA`.

Siguen en las fotos crudas `DW_M_AUD_*` para auditar. El diccionario de lo que sí entra: [`diccionario-fact.md`](diccionario-fact.md).

Tres fuentes activas: **F1** OD, **F2** sede central, **F5** SISUD.

El criterio de “fuera”: qué dato es, **qué sí entra en su lugar**, y por qué no se mezclan. Ejemplo: `DOC_SIGED` de la planilla **sí entra**, pero como `DOC_SIGED_DESCARGOS`, para no confundirlo con `SIGED` (memo de cobranza).

---

## 1. F1 — OD (hoja `5) Multas Coercitivas`)

La multa OD **sí entra** al fact. Estas columnas de la hoja **no** se copian.

| Columna en la planilla | Qué es | Por qué queda fuera |
|---|---|---|
| `N_DOC_NO_AMERIT` | N.° del oficio “no amerita MC” | El fact guarda el sí/no (`AMERITA_MC` ← `AMERIT_MC`) y el texto (`MOTIVO_NO_AMERIT`). El número y la fecha del oficio son trámite interno; no hay columnas. |
| `F_DOC_NO_AMERIT` | Fecha de ese oficio | Igual: manda el flag `AMERITA_MC` y el motivo, no el expediente del “no amerita”. |
| `RECORD_SEG` | Nota de recordatorio / seguimiento post-MC | Bitácora de la hoja. El fact no tiene “notas de seguimiento”; el seguimiento modelado es `F_VERIF_POST_MC` + `DOC_VERIF_MC`. |
| `EXP_SIGED_DOC` | Expediente SIGED del **documento de verificación** | El fact guarda el documento (`DOC_VERIF_MC`) y el SIGED de cobranza (`SIGED`). Este es un tercer identificador (expediente del doc de verificación); no hay columna. |

Foto cruda: `DW_M_AUD_F1_OD_MULTAS`.

---

## 2. F2 — sede central (hoja `1) Multas coercitivas`)

Las mismas 4 columnas de F1 que siguen fuera (`N_DOC_NO_AMERIT`, `F_DOC_NO_AMERIT`, `RECORD_SEG`, `EXP_SIGED_DOC`) también están en sede central y **tampoco** entran (misma razón).

Además, sede central tiene columnas propias que **no** van al fact:

| Columna en la planilla | Qué es | Por qué queda fuera |
|---|---|---|
| `EST_DCG` | Frase libre del estado de descargos (`NO PRESENTÓ DESCARGOS`, …) | El fact homologa el sí/no de `PRESENT_DCG_ADM` → `PRESENTO_DESCARGOS` (`S`/`N`) y el flag `FLAG_PRESENTO_DCG`. `EST_DCG` es otro texto, a menudo redundante o inconsistente; no se copia para no tener dos “estados de descargo”. |
| `AUX_FIN_MC` | Celda auxiliar de “ya finalizó” (control de la planilla) | No es un dato de negocio. Sirve a quien llena el Sheet. El estado de la multa es `ESTADO_MC` → `ID_ESTADO_MULTA` / `ESTADO_MC_TXT`. |
| `AUX_COD_MA` | Copia o fórmula de `COD_MA` | Manda la columna de negocio `COD_MA`. Usar el auxiliar como fallback duplicaría o pelearía con el código real. |
| `AUX_EST_MC` | Copia o fórmula del estado | Manda `ESTADO_MC`. El auxiliar es control de hoja. |
| `URESOL_MC` | “Última resolución” auxiliar | Manda `N_RES_MC` (el n.° que escribió el analista). SISUD **tampoco** pisa `N_RES_MC` (va a `N_RES_SISUD`). El auxiliar no entra para no tener dos resoluciones de planilla en la misma fila. |
| `FN_URESOL_MC` | Fecha de notificación de esa última resolución auxiliar | Manda `FN_RES_MC` → `F_NOTIF_RES_MC`. Misma lógica: una sola fecha de notificación en el fact. |

Foto cruda: `DW_M_AUD_F2_CSEP_MULTAS`.

### Hoja `2) Etapas` → `DW_M_DET_ETAPA_MC` (no es el fact)

La multa de sede central **sí** tiene etapas. Estas dos columnas de la hoja **no** entran al DET:

| Columna en la planilla | Qué es | Por qué queda fuera del DET |
|---|---|---|
| `COD_ETAPA_MC` | Código de etapa en la planilla | En la práctica viene `#N/A` / vacío. El DET usa `NRO_ETAPA` (`NRO_ETAPA_MC`) + `ACCION`. No hay columna `COD_ETAPA_MC` en Oracle. |
| `AUX_FIN_MC` | Auxiliar de finalizado de la fila de etapa | Control de hoja. El estado usable es `ESTADO_ETAPA` (`EST_ETAPA_MC`). |

Detalle de lo que sí entra: [`det-etapa-mc.md`](det-etapa-mc.md).

---

## 3. F5 — SISUD (`VW_MULTA_COERCITIVA`)

SISUD **no agrega filas** al fact. Si hay match (resolución + UIT) pega `CUM`, `CAM`, `NUMERO_REGISTRO` → `NUMERO_REGISTRO_SIGED`, `ESTADO_RESOLUCION` → `ID_ESTADO_RESOLUCION`, `MEDIDA_ADMINISTRATIVA`, `MONTO_MULTA_REC`, `MONTO_MULTA_TFA`, y `ADMINISTRADO` → `ID_ADMINISTRADO` **solo si** la planilla quedó `-1` (típico OD; no pisa `ADM` de sede central).

`RESOLUCION` y `MONTO_MULTA` **sí** se copian, pero como sombras `N_RES_SISUD` y `MONTO_UIT_SISUD`. **No reemplazan** `N_RES_MC` ni `MONTO_UIT` de la planilla (si Sheet dice 1.93 y SISUD 2, ambos quedan).

Sin match (o SISUD nulo en ese campo) quedan vacíos / `-1`.

El resto de la vista **no se copia** a la fila de negocio:

| Columna en SISUD | Qué es | Por qué queda fuera del fact |
|---|---|---|
| `NUMERO_EXPEDIENTE` | Expediente institucional (`0133-2023-DSIS-CRES`) | El fact ya trajo `NUMERO_EXPEDIENTE` de la planilla (`EXP_INF_INCUMP`; a menudo otro formato, p. ej. `00001332023`). SISUD **no pisa** identificadores de Sheet. Sirve para auditar, no para reemplazar. |
| `FECHA_EMISION` | Fecha de emisión en SISUD | El fact usa `F_FIRMA_RES_MC` de la planilla → `ID_TIEMPO_FIRMA`. No se mezcla con la fecha institucional. |
| `ESTADO_MULTA` | Estado de la multa en SISUD | Manda `ESTADO_MC` de la planilla → `ID_ESTADO_MULTA` / `ESTADO_MC_TXT`. El lookup SISUD pega el **estado de resolución** (`ACTIVO`/`INACTIVO`), no este. |
| `FECHA_CARGA` | Cuándo SISUD materializó la fila de la vista | El fact pone `FECHA_CARGA` = momento en que corrió **este** ETL, no el de SISUD. |

Además: si una multa **solo existe en SISUD** (sin fila en sede central ni OD), **no entra al fact**. Queda en `DW_M_AUD_F5_SISUD_VW` (~534 filas de referencia; el fact tiene ~1271 = planillas).
