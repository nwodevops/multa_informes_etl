# Qué no entra al fact

Columnas (y, en SISUD, filas) que **sí se descargan** pero **no alimentan** `DW_M_FACT_MULTA_COERCITIVA`.

Siguen en las fotos crudas `DW_M_AUD_*` para auditar. El diccionario de lo que sí entra: [`diccionario-fact.md`](diccionario-fact.md).

Tres fuentes activas: **F1** OD, **F2** sede central, **F5** SISUD.

---

## 1. F1 — OD (hoja `5) Multas Coercitivas`)

La multa OD **sí entra** al fact. Estas columnas de la hoja **no** se copian.

| Columna en la planilla | Qué es | Por qué queda fuera |
|---|---|---|
| `N_CARTA_DCG` | N.° de carta de descargos | No está en el molde del fact |
| `DOC_SIGED` | Documento SIGED de los descargos | Distinto de `SIGED` (cobranza), que sí entra |
| `F_VERIF_CAMPO` | Fecha de verificación **en campo** (durante el análisis) | El fact solo guarda `F_VERIF_POST_MC` (posterior a la multa) |
| `N_DOC_NO_AMERIT` | N.° de documento “no amerita MC” | Detalle operativo; el fact sí tiene `AMERITA_MC` (`AMERIT_MC`) |
| `F_DOC_NO_AMERIT` | Fecha de ese documento | Igual |
| `MOTIVO_NO_AMERIT` | Motivo de no ameritar | Igual |
| `RECORD_SEG` | Recordatorio / seguimiento posterior | Texto libre; no hay columna en el fact |
| `EXP_SIGED_DOC` | Expediente SIGED del documento de verificación | El fact guarda `DOC_VERIF_MC` y `SIGED`, no este expediente |

Foto cruda: `DW_M_AUD_F1_OD_MULTAS`.

---

## 2. F2 — sede central (hoja `1) Multas coercitivas`)

Las mismas 8 columnas de F1 también están en sede central y **tampoco** entran.

Además, sede central tiene columnas propias que **no** van al fact:

| Columna en la planilla | Qué es | Por qué queda fuera |
|---|---|---|
| `EST_DCG` | Estado de descargos (texto) | El fact usa `PRESENTO_DESCARGOS` (`PRESENT_DCG_ADM`), no este texto |
| `AUX_FIN_MC` | Auxiliar de “finalizado” | Columna de control de la planilla, no de negocio |
| `AUX_COD_MA` | `COD_MA` auxiliar | No se usa como fallback; manda `COD_MA` |
| `AUX_EST_MC` | Estado auxiliar de la MC | Manda `ESTADO_MC` |
| `URESOL_MC` | Última resolución (auxiliar) | Manda `N_RES_MC` |
| `FN_URESOL_MC` | Fecha de notificación de esa última resolución | Manda `FN_RES_MC` → `F_NOTIF_RES_MC` |

Foto cruda: `DW_M_AUD_F2_CSEP_MULTAS`.

En la hoja **`2) Etapas`**, `COD_ETAPA_MC` y `AUX_FIN_MC` no entran a `DW_M_DET_ETAPA_MC`.

---

## 3. F5 — SISUD (`VW_MULTA_COERCITIVA`)

SISUD **no agrega filas** al fact. Si hay match (resolución + UIT) pega `CUM`, `CAM`, `NUMERO_REGISTRO` → `NUMERO_REGISTRO_SIGED`, y también `ESTADO_RESOLUCION` → `ID_ESTADO_RESOLUCION`, `MEDIDA_ADMINISTRATIVA`, `MONTO_MULTA_REC`, `MONTO_MULTA_TFA`. Sin match (o SISUD nulo en ese campo) quedan vacíos / `-1`.

El resto de la vista **no se copia** a la fila de negocio:

| Columna en SISUD | Qué es | Por qué queda fuera del fact |
|---|---|---|
| `NUMERO_EXPEDIENTE` | Expediente institucional | El fact ya trae el expediente de la planilla (`EXP_INF_INCUMP`). SISUD no lo pisa. |
| `ADMINISTRADO` | Razón social | No se usa en el lookup. OD no trae `ADM`; este nombre SISUD **tampoco** se pega hoy. |
| `RESOLUCION` | N.° de resolución | Solo sirve para **buscar** el match. No reemplaza `N_RES_MC` de la planilla. |
| `FECHA_EMISION` | Fecha de emisión | El fact usa `F_FIRMA_RES_MC` de la planilla. |
| `ESTADO_MULTA` | Estado en SISUD | Manda `ESTADO_MC` de la planilla. |
| `MONTO_MULTA` | UIT en SISUD | Solo entra en la **clave** del match. No pisa `MONTO_UIT` de la planilla. |

Además: si una multa **solo existe en SISUD** (sin fila en sede central ni OD), **no entra al fact**. Queda en `DW_M_AUD_F5_SISUD_VW` (~534 filas de referencia; el fact tiene ~1271 = planillas).
