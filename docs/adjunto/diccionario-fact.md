# Diccionario — `DW_M_FACT_MULTA_COERCITIVA`

Una fila = una multa de **una** planilla. Sede central y OD se **apilan** (no se fusionan en una sola fila).

**CSEP** administra las fuentes. `ID_FUENTE` solo dice si la fila nació en sede central o en OD.

| Planilla | Libros | Hoja |
|---|---|---|
| **Sede central** | 10 (CMIN, CRES, …) | `1) Multas coercitivas` |
| **OD** | 31 oficinas | `5) Multas Coercitivas` |

Catálogos: [`../inputs/f2_csep_sheets.json`](../inputs/f2_csep_sheets.json) · [`../inputs/f1_ods_sheets.json`](../inputs/f1_ods_sheets.json).  
Lectura: [`README.md`](README.md). Etapas: [`det-etapa-mc.md`](det-etapa-mc.md). Qué no entra: [`fuera-del-fact.md`](fuera-del-fact.md).

Cómo leer la tabla:

| En sede central / OD | Significa |
|---|---|
| El mismo código que el fact | Se copia tal cual |
| Otro código (`EXP_INF_INCUMP`, …) | Se renombra a la columna del fact |
| `—` | Esa planilla **no tiene** el campo |
| `— (SISUD si match)` | No está en la planilla; SISUD lo pega si hay match (resolución + UIT). Sin match → `NULL` (texto/monto) o `-1` (FK) |
| no está en Excel | El ETL lo deriva de otras columnas del fact (resta de fechas, 0/1, UIT × monto) |

Celda vacía / `#N/A` en planilla → `NULL` en columnas de texto, fecha o monto. La fila **no se borra**. SISUD **no** pisa `N_RES_MC` ni `MONTO_UIT` / `MONTO_S` de la planilla: si hay match, esos valores SISUD van a `N_RES_SISUD` / `MONTO_UIT_SISUD`.

### Qué significa `-1` (en Oracle, no en la leyenda)

`-1` **no** es un código de planilla ni un error. Solo aparece en columnas `ID_*` que apuntan a una dimensión (FK). Cada dim tiene una fila semilla `ID = -1` llamada **NO ESPECIFICADO**. El fact apunta ahí cuando **no hay valor que resolver**.

No usar `-1` en textos (`JEFE`, `CUM`, `N_RES_MC`…): esos van `NULL`.

| | `NULL` | `-1` |
|---|---|---|
| Dónde | Texto, fecha, monto (`JEFE`, `CUM`, `F_PAGO`, `MONTO_S`…) | FK: `ID_ORGANO`, `ID_OD`, `ID_ADMINISTRADO`, `ID_TIEMPO_FIRMA`, `ID_ESTADO_*`, `ID_UIT`, `ID_MATERIA` |
| Por qué | La celda no existe o vino vacía | Hay que pegar a una dim y Oracle no deja la FK vacía (`NOT NULL`) |
| Cómo filtrar | `JEFE IS NULL` | `ID_OD = -1` |
| JOIN a la dim | no aplica | Sí: cae en la fila “NO ESPECIFICADO” / código `ND` |

Ejemplos:

- `ID_OD = -1` en sede central: esa multa **sí está**; no es una oficina desconcentrada.
- `ID_ORGANO = -1` en OD: esa multa **sí está**; OD no usa CMIN/CRES.
- `ID_ESTADO_RESOLUCION = -1`: no hubo match SISUD (o SISUD no trajo estado).
- `ID_TIEMPO_FIRMA = -1`: no hay fecha de firma (o está fuera del calendario 2015–2026).
- `ID_MATERIA = -1` **siempre**: ninguna fuente trae materia; no filtrar el tablero por aquí (usar `ID_ORGANO`).

---



## De dónde sale cada columna del fact


| Fact                     | Qué es                                         | Sede central                         | OD                                       |
| ------------------------ | ---------------------------------------------- | ------------------------------------ | ---------------------------------------- |
| `ID_MC`                  | Clave de la fila en el DW                      | (asignado; estas filas van primero)  | (asignado; van después)                  |
| `ID_FUENTE`              | ¿Sede central o OD?                            | libro de unidad                      | libro de oficina                         |
| `COD_MA`                 | Código de medida administrativa                | `COD_MA`                             | `COD_MA`                                 |
| `COD_PROY_MC`            | Proyecto interno; enlace a etapas              | `COD_PROY_MC`                        | —                                        |
| `NUMERO_EXPEDIENTE`      | Expediente del incumplimiento                  | `EXP_INF_INCUMP`                     | `EXP_INF_INCUMP`                         |
| `EXP_RES_MC`             | Expediente de la resolución                    | `EXP_RES_MC`                         | `EXP_RES_MC`                             |
| `N_RES_MC`               | N.° de resolución (vacío en planilla → `NULL`) | `N_RES_MC`                           | `N_RES_MC`                               |
| `N_RES_SISUD`            | Resolución en SISUD; **no** pisa `N_RES_MC`    | — (SISUD si match)                   | — (SISUD si match)                       |
| `CUM`                    | Código único de medida (11 dígitos)            | — (SISUD si match)                   | — (SISUD si match)                       |
| `CAM`                    | Código de acto de medida                       | — (SISUD si match)                   | — (SISUD si match)                       |
| `NUMERO_REGISTRO_SIGED`  | Registro SIGED institucional                   | — (SISUD si match)                   | — (SISUD si match)                       |
| `SIGED`                  | SIGED de la planilla (memo / cobranza)         | `SIGED`                              | `SIGED`                                  |
| `DOC_SIGED_DESCARGOS`    | SIGED del escrito de descargos                 | `DOC_SIGED`                          | `DOC_SIGED`                              |
| `DOC_VERIF_MC`           | Documento de verificación posterior            | `DOC_VERIF_MC`                       | `DOC_VERIF_MC`                           |
| `MEMO_EF`                | Memo de ejecución forzosa                      | `MEMO_EF`                            | `MEMO_EF`                                |
| `ID_ADMINISTRADO`        | Administrado (`-1` si no hay)                  | `ADM` (SISUD no pisa)                | `ADM` si hay; si no, SISUD si match      |
| `ID_ORGANO`              | Unidad (CMIN, CRES, …); `-1` si no hay         | `COORD` (si vacío, unidad del libro) | —                                        |
| `ID_OD`                  | Oficina desconcentrada; `-1` en sede central   | —                                    | oficina del libro (`AMAZONAS`, `ICA`, …) |
| `ID_TIEMPO_FIRMA`        | Día de firma (`-1` si no hay fecha)            | `F_FIRMA_RES_MC`                     | `F_FIRMA_RES_MC`                         |
| `ID_ESTADO_MULTA`        | Estado de multa homologado                     | `ESTADO_MC`                          | `ESTADO_MC`                              |
| `ID_ESTADO_PAGO`         | Estado de pago homologado                      | `ESTADO_PAGO_MC`                     | —                                        |
| `ID_ESTADO_RESOLUCION`   | Estado de resolución (ACTIVO/INACTIVO)         | — (SISUD si match)                   | — (SISUD si match)                       |
| `ID_UIT`                 | UIT MEF del año de firma                       | año de `F_FIRMA_RES_MC`              | año de `F_FIRMA_RES_MC`                  |
| `ID_MATERIA`             | Materia / subsector; **siempre `-1`** (sin fuente) | —                              | —                                        |
| `ESTADO_MC_TXT`          | Estado de multa tal cual la planilla           | `ESTADO_MC`                          | `ESTADO_MC`                              |
| `ESTADO_PAGO_TXT`        | Estado de pago tal cual la planilla            | `ESTADO_PAGO_MC`                     | —                                        |
| `F_NOTIF_DCG`            | Notificación carta de descargos                | `FN_MC`                              | `FN_MC`                                  |
| `F_VENC_DCG`             | Vencimiento para descargos                     | `F_VENC_DCG`                         | `F_VENC_DCG`                             |
| `F_RPTA_ADM`             | Respuesta del administrado                     | `F_RPTA_ADM`                         | `F_RPTA_ADM`                             |
| `F_INIC_ANALISIS`        | Inicio del análisis                            | `F_INIC_ANALISIS`                    | `F_INIC_ANALISIS`                        |
| `F_FIN_ANALISIS`         | Fin del análisis                               | `F_FIN_ANALISIS`                     | `F_FIN_ANALISIS`                         |
| `F_FIRMA_RES_MC`         | Firma de la resolución                         | `F_FIRMA_RES_MC`                     | `F_FIRMA_RES_MC`                         |
| `F_NOTIF_RES_MC`         | Notificación de la resolución                  | `FN_RES_MC`                          | `FN_RES_MC`                              |
| `F_VENC_MC`              | Vencimiento para pagar                         | `F_VENC_MC`                          | `F_VENC_MC`                              |
| `F_VERIF_CAMPO`          | Verificación en campo durante el análisis      | `F_VERIF_CAMPO`                      | `F_VERIF_CAMPO`                          |
| `F_VERIF_POST_MC`        | Verificación posterior                         | `F_VERIF_POST_MC`                    | `F_VERIF_POST_MC`                        |
| `F_PAGO`                 | Fecha de pago                                  | `F_PAGO`                             | `F_PAGO`                                 |
| `F_REMISION_MEMO`        | Remisión del memo de ejecución forzosa         | `F_REMIS`                            | `F_REMIS`                                |
| `PRESENTO_DESCARGOS`     | ¿Presentó descargos? (`SI`/`NO` → `S`/`N`)     | `PRESENT_DCG_ADM`                    | `PRESENT_DCG_ADM`                        |
| `AMERITA_MC`             | ¿Amerita multa? (`SI`/`NO` → `S`/`N`)          | `AMERIT_MC`                          | `AMERIT_MC`                              |
| `REQUIERE_VERIF_CAMPO`   | ¿Requiere verificación en campo?               | `REQ_VERIF_CAMPO`                    | `REQ_VERIF_CAMPO`                        |
| `N_CARTA_DCG`            | N.° de carta de descargos                      | `N_CARTA_DCG`                        | `N_CARTA_DCG`                            |
| `MOTIVO_NO_AMERIT`       | Motivo de no ameritar MC                       | `MOTIVO_NO_AMERIT`                   | `MOTIVO_NO_AMERIT`                       |
| `FLAG_PRESENTO_DCG`      | 1 si `PRESENTO_DESCARGOS` = S                  | no está en Excel                     | no está en Excel                         |
| `FLAG_AMERITA_MC`        | 1 si `AMERITA_MC` = S                          | no está en Excel                     | no está en Excel                         |
| `FLAG_PAGADA`            | 1 si el estado de pago homologa a pagado       | no está en Excel                     | no está en Excel                         |
| `FLAG_EJECUCION_FORZOSA` | 1 si hay `MEMO_EF`                             | no está en Excel                     | no está en Excel                         |
| `FLAG_CUMPLIO_VERIF`     | 1 si hay `F_VERIF_POST_MC`                     | no está en Excel                     | no está en Excel                         |
| `MONTO_UIT`              | Multa en UIT                                   | `MULTA_UIT`                          | `MULTA_UIT`                              |
| `MONTO_UIT_SISUD`        | UIT en SISUD; **no** pisa `MONTO_UIT`          | — (SISUD si match)                   | — (SISUD si match)                       |
| `MONTO_S`                | Multa en soles (`#N/A` → `NULL`)               | `MULTA_S`                            | `MULTA_S`                                |
| `VALOR_UIT_APLICADO`     | UIT MEF del año (soles)                        | catálogo MEF                         | catálogo MEF                             |
| `MONTO_S_CALC`           | `MONTO_UIT × VALOR_UIT_APLICADO`               | no está en Excel                     | no está en Excel                         |
| `MONTO_MULTA_REC`        | Monto en reconsideración                       | — (SISUD si match)                   | — (SISUD si match)                       |
| `MONTO_MULTA_TFA`        | Monto en Tribunal (TFA)                        | — (SISUD si match)                   | — (SISUD si match)                       |
| `MEDIDA_ADMINISTRATIVA`  | Descripción institucional de la medida         | — (SISUD si match)                   | — (SISUD si match)                       |
| `JEFE`                   | Jefe de equipo                                 | `JEFE`                               | —                                        |
| `UF`                     | Unidad fiscalizable                            | `UF`                                 | —                                        |
| `N_PROY_MC`              | N.° de proyecto en la unidad                   | `N_PROY_MC`                          | —                                        |
| `ETA_REG_PROY_MC`        | Etapa de registro del proyecto                 | `ETA_REG_PROY_MC`                    | —                                        |
| `ETA_REG_MC`             | Etapa de registro de la MC                     | `ETA_REG_MC`                         | —                                        |
| `RESULT_PROY_MC`         | Resultado del proyecto                         | `RESULT_PROY_MC`                     | —                                        |
| `DIAS_NOTIF_A_RESPUESTA` | `F_RPTA_ADM − F_NOTIF_DCG`                     | no está en Excel                     | no está en Excel                         |
| `DIAS_ANALISIS`          | `F_FIN_ANALISIS − F_INIC_ANALISIS`             | no está en Excel                     | no está en Excel                         |
| `DIAS_NOTIF_A_FIRMA`     | `F_FIRMA_RES_MC − F_NOTIF_DCG`                 | no está en Excel                     | no está en Excel                         |
| `DIAS_FIRMA_A_VENC`      | `F_VENC_MC − F_FIRMA_RES_MC`                   | no está en Excel                     | no está en Excel                         |
| `DIAS_VENC_A_PAGO`       | `F_PAGO − F_VENC_MC`                           | no está en Excel                     | no está en Excel                         |
| `DIAS_RESOL_A_VERIF`     | `F_VERIF_POST_MC − F_FIRMA_RES_MC`             | no está en Excel                     | no está en Excel                         |
| `FECHA_CARGA`            | Momento en que corrió el ETL                   | no está en Excel                     | no está en Excel                         |




### Qué significa `—` (detalle)

El fact es **una sola tabla** con **todas** las columnas. Cada fila es una multa de **un** libro: o sede central, o OD. No se mezclan dos planillas en la misma fila.

`—` no quiere decir “esa multa no entra”. Quiere decir: **esa planilla nunca tuvo esa columna**.

- Si la celda dice solo `—` (p. ej. `JEFE` en OD): texto/fecha/monto → `NULL`; FK (`ID_ORGANO` en OD, `ID_OD` en sede central) → `-1`.
- Si dice `— (SISUD si match)`: no está en Excel, pero **sí puede llenarse** desde SISUD. Sin match: `NULL` en CUM/medida/montos/sombras; `-1` en `ID_ESTADO_RESOLUCION` (y en `ID_ADMINISTRADO` si la planilla tampoco trajo ADM).

| Fact | Columna en SISUD (`VW_MULTA_COERCITIVA` / `DW_M_AUD_F5_SISUD_VW`) | En el fact |
|---|---|---|
| `ID_ESTADO_RESOLUCION` | `ESTADO_RESOLUCION` (ACTIVO / INACTIVO) | FK a `DW_M_DIM_ESTADO` (`TIPO_ESTADO='RESOLUCION'`). `-1` si no hubo match o SISUD venía vacío. |
| `ID_ADMINISTRADO` | `ADMINISTRADO` | Solo si la planilla quedó `-1` (típico OD). No pisa `ADM` de sede central. |
| `MEDIDA_ADMINISTRATIVA` | `MEDIDA_ADMINISTRATIVA` | Texto institucional. `NULL` si no hubo match o SISUD nulo. |
| `MONTO_MULTA_REC` | `MONTO_MULTA_REC` | Reconsideración. A menudo nulo en SISUD. |
| `MONTO_MULTA_TFA` | `MONTO_MULTA_TFA` | Tribunal (TFA). A menudo nulo en SISUD. |
| `CUM` / `CAM` / `NUMERO_REGISTRO_SIGED` | `CUM` / `CAM` / `NUMERO_REGISTRO` | Igual: solo si match y la planilla los traía vacíos. |
| `N_RES_SISUD` | `RESOLUCION` | Sombra: no reemplaza `N_RES_MC`. `NULL` sin match. |
| `MONTO_UIT_SISUD` | `MONTO_MULTA` (ya es UIT) | Sombra: no reemplaza `MONTO_UIT`. `NULL` sin match. |

`ID_MATERIA` **no** entra en este lookup: sigue `-1` (SISUD no trae materia).

Ejemplo con dos multas reales del mismo fact:


|               | Fila sede central (p. ej. CMIN)                     | Fila OD (p. ej. Ica)                            |
| ------------- | --------------------------------------------------- | ----------------------------------------------- |
| `ID_FUENTE`   | Sede central                                        | OD                                              |
| `N_RES_MC`    | `0153-2026-OEFA/DSEM` (viene de `N_RES_MC`)         | `0041-2024-OEFA/OD-ICA` (viene de `N_RES_MC`)   |
| `JEFE`        | `PEÑA, AGUSTÍN` (la hoja de unidad sí tiene `JEFE`) | `NULL` — la hoja OD **no tiene** columna `JEFE` |
| `UF`          | texto de la unidad fiscalizable                     | `NULL` — OD no registra UF                      |
| `COD_PROY_MC` | código de proyecto (sirve para etapas)              | `NULL` — OD no tiene proyectos/etapas           |
| `ID_ORGANO`   | CMIN (de `COORD`)                                   | `-1` — OD no usa unidades CMIN/CRES             |
| `ID_OD`       | `-1` — no es una oficina desconcentrada             | Ica (oficina del libro)                         |


Las ~990 filas de sede central y las ~281 de OD **están todas** en `DW_M_FACT_MULTA_COERCITIVA`. Al filtrar `JEFE IS NULL` vas a ver sobre todo OD (y sede central que dejó la celda vacía). Al filtrar `ID_OD = -1` ves sede central.

Al revés: `ID_OD` tiene `—` en sede central. Esas multas también están; solo no tienen oficina desconcentrada.

---



## Columnas de las planillas que **no** entran al fact

Listado por fuente (F1 OD, F2 sede central, F5 SISUD): [`fuera-del-fact.md`](fuera-del-fact.md).