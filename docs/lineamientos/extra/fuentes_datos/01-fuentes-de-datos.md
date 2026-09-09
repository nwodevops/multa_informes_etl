> **Alcance vigente del ETL:** el DW carga Multas desde **F1 + F2 (+etapas) + F5**. **F3 OUT**. **F4 MySQL fuera de ingestión** (semilla histórica `GAPPS` en dim fuente). F3 (informes) es inventario histórico del diagnóstico; **no se extrae ni se modela**.
>
> **Inputs vigentes (runtime):** [`docs/inputs/README.md`](../../../inputs/README.md) · catálogos [`f1_ods_sheets.json`](../../../inputs/f1_ods_sheets.json) / [`f2_csep_sheets.json`](../../../inputs/f2_csep_sheets.json) · manifiesto [`inputs.yaml`](../../../../inputs.yaml).

# 01 · Fuentes de Datos — Inventario Detallado

> **Proyecto:** Data Warehouse OEFA — Estrategias de promoción del cumplimiento
> **Referencia:** TDR REQ N.° 3629-2026 · Área usuaria: CSEP — DPEF
> **Contenido:** inventario campo por campo de las fuentes (F1/F2/F5 activas; F3/F4 históricas), con tipos, descripciones,
> dominios observados y hallazgos de calidad **verificados sobre los archivos / sheets reales**.

---

## 1. Resumen de fuentes

| ID | Fuente (vigente) | Tipo / Motor | Contenido | STG Hop / notas |
|---|---|---|---|---|
| **F1** | **31 Google Sheets** OD (catálogo `f1_ods_sheets.json`) | Google Sheets + SA | Multas coercitivas por oficina desconcentrada | `STG_GS2_OD_MULTAS` (+ `COD_OD`); hoja `5) Multas Coercitivas` (32 cols, header fila 3). Excel OD → `input_excel/medidas_administrativas/legacy/` |
| **F2** | **10 Google Sheets** CSEP (catálogo `f2_csep_sheets.json`) | Google Sheets + SA | Multas + etapas por unidad/coordinación (CMIN…UFSAVC) | `STG_GS1_CSEP_MULTAS` (+ `COD_UNIDAD`); hoja `1) Multas coercitivas` (48 cols). Etapas → `STG_GS1_ETAPAS`. DIC → Excel legacy `input_excel/legacy/CAGR_…xlsx` |
| **F3** | `CSEP_INFORMES_VIEW` | Oracle `SISUD` | Informes de supervisión | **Fuera de alcance** del ETL |
| **F4** | `gappsdb.T_MVC_MULTACOERCITIVA_MC` | MySQL GAPP | Tabla transaccional MC | **Fuera de ingestión** (solo semilla `GAPPS` en dim) |
| **F5** | `SISUD.VW_MULTA_COERCITIVA` | Oracle SISUD | Vista institucional MC | `STG_ORA_VW_MULTA_COERCITIVA` |

> **Linaje en DW:** `ID_FUENTE` → `MI_DIM_FUENTE_REGISTRO.CODIGO` (F1=`OD_SHEETS`, F2=`CAGR`, F5=`SISUD_VW`; `GAPPS` = semilla histórica F4). El VARCHAR `FUENTE_REGISTRO` ya no existe en el hecho. Reportes: vistas `VW_MC_CSEP` / `_OD` / `_SISUD` / `VW_MC_ENRIQUECIDA`.  
> Unidad F2: `COORD` / `MI_DIM_ORGANO_UNIDAD.SIGLA` + `DESCRIPCION` desde catálogo (solo 10 CSEP + ND).  
> **Auth Google:** `client_secret.json` (gitignored); cada spreadsheet compartido con el service account.

> **Nota de volumen:** conteos de referencia actuales ≈ CSEP~990, OD~281, SISUD~534, enriquecido~1271 (varían con sheets vivos).

---

## 2. F1 — Familia OD (Google Sheets)

Antes: un Excel por OD (p. ej. Lambayeque). **Hoy:** 31 spreadsheets catalogados; Hop `pl_stage_od_sheet.hpl` + `scripts/stage_ods_sheets.sh`.

Convención de hoja: fila 1 = sección, fila 2 = descripción, **fila 3 = códigos** (`COD_MA`…); datos desde fila 4. Rango Hop: `'5) Multas Coercitivas'!A3:AF`.

### 2.1 Hoja `5) Multas Coercitivas` (32 columnas)

| # | Código | Sección | Tipo | Descripción | Dominio / observación real |
|---|---|---|---|---|---|
| 1 | `COD_MA` | CÓDIGO | Texto | Código de la medida administrativa (clave natural del registro) | `0067-2022-0050-2022-1-CRES` (expediente UF + acta + correlativo + OD) |
| 2 | `EXP_INF_INCUMP` | DESCARGOS | Texto | Expediente con el informe de declaración del incumplimiento | `0067-2022-DSIS-CRES` — **clave de amarre con F5/F3** |
| 3 | `N_CARTA_DCG` | DESCARGOS | Texto | N.° de carta que requiere descargos | |
| 4 | `FN_MC` | DESCARGOS | Fecha | Fecha de notificación de la carta de descargos | |
| 5 | `F_VENC_DCG` | DESCARGOS | Fecha | Vencimiento para presentar descargos | En Sheets se calculaba con `WORKDAY.INTL` + `M_FERIADO` |
| 6 | `PRESENT_DCG_ADM` | DESCARGOS | Texto | ¿Presentó descargos el administrado? | `SI`/`NO` (observado: 16 NO, 1 SI de 17 con dato) |
| 7 | `F_RPTA_ADM` | DESCARGOS | Fecha | Fecha de respuesta del administrado | |
| 8 | `DOC_SIGED` | DESCARGOS | Texto | Documento SIGED de los descargos | |
| 9 | `F_INIC_ANALISIS` | ANÁLISIS | Fecha | Fecha de inicio de análisis | |
| 10 | `REQ_VERIF_CAMPO` | ANÁLISIS | Texto | ¿Requiere verificación en campo? | `SI`/`NO` |
| 11 | `F_VERIF_CAMPO` | ANÁLISIS | Fecha | Fecha de verificación en campo | |
| 12 | `F_FIN_ANALISIS` | ANÁLISIS | Fecha | Fecha fin de análisis | |
| 13 | `AMERIT_MC` | ANÁLISIS | Texto | ¿Amerita multa coercitiva? | `SI`/`NO` (observado: 21 SI) |
| 14 | `N_DOC_NO_AMERIT` | ANÁLISIS | Texto | N.° de documento que indica que no amerita | |
| 15 | `F_DOC_NO_AMERIT` | ANÁLISIS | Fecha | Fecha del documento que indica que no amerita | |
| 16 | `MOTIVO_NO_AMERIT` | ANÁLISIS | Texto | Motivo por el cual no amerita MC | |
| 17 | `EXP_RES_MC` | IMPOSICIÓN | Texto | Expediente con la resolución de MC | `0067-2022-DSIS-CRES` |
| 18 | `N_RES_MC` | IMPOSICIÓN | Texto | N.° de resolución de MC | `0031-2022-OEFA/DSIS` |
| 19 | `F_FIRMA_RES_MC` | IMPOSICIÓN | Fecha | Fecha de firma de la resolución de MC | |
| 20 | `FN_RES_MC` | IMPOSICIÓN | Fecha | Fecha de notificación de la resolución de MC | |
| 21 | `F_VENC_MC` | IMPOSICIÓN | Fecha | Fecha de vencimiento de la multa | |
| 22 | `MULTA_UIT` | IMPOSICIÓN | Decimal | Multa en UIT | Observado: 1.5 · 1.6 · 2 · 2.6 · 4 · 5 · 6.15 · 6.56 · 10 |
| 23 | `MULTA_S` | IMPOSICIÓN | Decimal | Multa en soles | **Validado:** = `MULTA_UIT × UIT(año)` (5 UIT × 4 600 = 23 000 en 2022 ✓) |
| 24 | `RECORD_SEG` | SEGUIMIENTO | Texto | Recordatorio / nuevo seguimiento post MC | |
| 25 | `F_VERIF_POST_MC` | SEGUIMIENTO | Fecha | Fecha de verificación post multa coercitiva | |
| 26 | `DOC_VERIF_MC` | SEGUIMIENTO | Texto | Documento de verificación de multa | |
| 27 | `EXP_SIGED_DOC` | SEGUIMIENTO | Texto | Expediente SIGED del documento | |
| 28 | `ESTADO_MC` | COBRANZA | Texto | Estado de la multa | `INCUMPLIDO`/`PAGADO` (observado: 21 INCUMPLIDO) |
| 29 | `F_PAGO` | COBRANZA | Fecha | Fecha de pago | |
| 30 | `MEMO_EF` | COBRANZA | Texto | Memorando de traslado a ejecución forzosa | `0351-2022-OEFA/DSIS` |
| 31 | `F_REMIS` | COBRANZA | Fecha | Fecha de remisión del memorando | |
| 32 | `SIGED` | COBRANZA | Texto | N.° SIGED del memorando | `2022-I01-028773` |

### 2.2 Catálogos auxiliares en la plantilla OD (histórico / no stageados)

Las hojas `M_FERIADO`, `M_UBIGEO`, `M_PARAMETROS` existían en el Excel de diagnóstico (a menudo con `IMPORTRANGE` roto). **El ETL F1 vigente no las carga**; la UIT se siembra desde catálogo MEF en Python (`MI_DIM_PARAMETRO_UIT`). Territorio OD se resuelve con `MI_DIM_OD` + `COD_OD` del catálogo JSON.

---

## 3. F2 — Unidades CSEP (Google Sheets)

Antes: un Excel CAGR (Agricultura). **Hoy:** 10 spreadsheets sectoriales (`f2_csep_sheets.json`); Hop `pl_stage_csep_sheet.hpl` / `pl_stage_csep_etapa.hpl` + `scripts/stage_csep_sheets.sh`.

| # | `cod_unidad` | Nombre (`DESCRIPCION` en dim) |
|---|---|---|
| 1 | CMIN | Minería |
| 2 | CHID | Hidrocarburos |
| 3 | CELE | Electricidad |
| 4 | CIND | Industria |
| 5 | CPES | Pesca |
| 6 | CAGR | Agricultura |
| 7 | CRES | Residuos Sólidos |
| 8 | CCAM | Consultoras Ambientales |
| 9 | UFED | UF educación |
| 10 | UFSAVC | UF vivienda |

Misma convención de encabezados que F1 (fila 3 = códigos). Rango Hop multas: `'1) Multas coercitivas'!A3:AV`. Etapas: `'2) Etapas'!A2:L` (header fila 2).

`COD_UNIDAD` se inyecta post-carga en STG; `COORD` del sheet alimenta `MI_DIM_ORGANO_UNIDAD` (`SIGLA` + `DESCRIPCION` desde el catálogo).

### 3.1 Hoja `1) Multas coercitivas` (48 columnas)

Contiene las 32 columnas de F1 (mismos códigos) **más** las siguientes:

| Código | Sección | Tipo | Descripción | Dominio observado |
|---|---|---|---|---|
| `COD_PROY_MC` | CÓDIGOS | Texto | Código de proyecto de MC | `MULTA COERCITIVA - 1/CÓDIGO DE EXPEDIENTE INVÁLIDO` ⚠ |
| `JEFE` | ESTADO | Texto | Jefe de equipo responsable | `PEÑA, AGUSTÍN` (6), `RIMACHI, LUIS` (1) |
| `ETA_REG_PROY_MC` | ESTADO | Texto | Etapa de registro del proyecto | `EN ETAPA DE COBRANZA` (7) |
| `N_PROY_MC` | — | Entero | N.° de proyecto | 1..5 |
| `COORD` | INF. GENERAL | Texto | Coordinación / unidad | En sheets vivos: `CMIN`, `CHID`, `CRES`, … (alineado a `cod_unidad`) |
| `ADM` | INF. GENERAL | Texto | Administrado | Texto libre |
| `UF` | INF. GENERAL | Texto | Unidad fiscalizable | Texto libre |
| `EST_DCG` | DESCARGOS | Texto | Estado de descargos | p. ej. `NO PRESENTÓ DESCARGOS` |
| `RESULT_PROY_MC` | RESULTADO | Texto | Resultado del proyecto | |
| `ETA_REG_MC` | ETAPAS REG. | Texto | Etapas de registro de la MC | |
| `ESTADO_PAGO_MC` | COBRANZA | Texto | Estado del pago de la multa | |
| `AUX_FIN_MC` | AUXILIARES | Entero | Auxiliar de finalizado | |
| `AUX_COD_MA` | AUXILIARES | Texto | COD_MA auxiliar | |
| `AUX_EST_MC` | AUXILIARES | Texto | Estado auxiliar de MC | |
| `URESOL_MC` | AUXILIARES | Texto | Última resolución de MC | |
| `FN_URESOL_MC` | AUXILIARES | Fecha | Fecha de notificación de la última resolución | |

> **Nota:** la muestra TDR (Excel CAGR, 7 filas) tenía fórmulas rotas (`#N/A`, `#VALUE!`). En Google Sheets vivos F2 el volumen y la calidad son distintos; `MONTO_S` se recalcula en DWH como `MULTA_UIT × UIT(año)` cuando hace falta.

### 3.2 Hoja `2) Etapas` (12 columnas; encabezados en fila 2)

| Código | Tipo | Descripción | Dominio observado |
|---|---|---|---|
| `COD_PROY_MC` | Texto | Proyecto de MC al que pertenece la etapa | `MULTA COERCITIVA - 1/CAGR` |
| `NRO_ETAPA_MC` | Entero | Número de etapa (secuencial) | 1..6 |
| `PERF_ENCARG_MC` | Texto | Perfil del encargado | ⚠ `#N/A` en la muestra |
| `ACCION_MC` | Texto | Acción de la etapa | `ELABORACION DE PROYECTO` (2), `REVISION` (3), `CALCULO` (1), `FIRMA` (1) |
| `ENCARGADO_MC` | Texto | Responsable asignado | `ASCON, ALEX` · `LAVERIANO, BETSABE` · `SEERANO, CRISTIAN` · `PEÑA, AGUSTÍN` · `DSAP` |
| `F_ASIG_MC` | Fecha | Fecha de asignación | |
| `EST_ETAPA_MC` | Texto | Estado de la etapa | `TERMINADO` (7) |
| `CONFORMIDAD_MC` | Texto | Conformidad de la revisión | `CONFORME (SIN CORRECIONES)` (3), `NO APLICA` (4) |
| `F_ENT_DEV_MC` | Fecha | Fecha de entrega o devolución | |
| `T_ELAB_MC` | Entero | Tiempo de elaboración (días hábiles, calculado con feriados) | 1, 2, 3, 4, 12 |
| `COD_ETAPA_MC` | Texto | Código de etapa | ⚠ `#N/A` |
| `AUX_FIN_MC` | Entero | Auxiliar de finalizado | 0 |

### 3.3 Hojas de gobierno y apoyo

| Hoja | Uso en ETL vigente |
|---|---|
| `2) Etapas` | Stage desde las 10 sheets → `STG_GS1_ETAPAS` |
| `DIC_TABLAS` / `DIC_VARIABLES` | Desde **Excel legacy** CAGR (`pl_stage_excel.hpl`) → `STG_GS1_DIC_*` |
| `Equipo`, `PARAMETROS`, `MA_INDIVIDUALES` | Presentes en sheets; **no** stageados al DW |

El Excel original CAGR está en `input_excel/legacy/` solo para DIC (y referencia).

---

## 4. F3 — Oracle SISUD · `CSEP_INFORMES_VIEW` (informes de supervisión)

Respaldo con literales `TIMESTAMP'YYYY-MM-DD HH24:MI:SS'` propios de Oracle. Grano:
**una actividad/informe de supervisión**. Las fechas llegan como texto con el prefijo
`TIMESTAMP'...'` y se parsean en la capa ODS.

### 4.1 Identificadores y clasificadores

| Campo | Tipo | Descripción | Observación real |
|---|---|---|---|
| `IDACTIVIDAD` | Número | Identificador de la actividad de supervisión | 30355 … 380979 |
| `TXMES` | Texto | Mes programado | `AGOSTO`, `JUNIO`, `ABRIL`… |
| `TXNUMEXP` | Texto | Número de expediente | ⚠ nulo en toda la muestra |
| `TXCUC` | Texto | Código único de caso (CUC) | `0055-7-2015-13` — **clave de amarre** |
| `TXESTADO` | Texto | Estado de la actividad | `EN CUSTODIA` (10) |
| `TXTIPSUP` | Texto | Tipo de supervisión | `ESPECIAL` / `REGULAR` |
| `TXFUENTE` | Texto | Fuente de programación | `PLANEFA` / nulo |
| `TXOTRAFUENTE`, `TXACCION`, `TXMUESTREO` | Texto | Otra fuente, acción, muestreo | mayormente nulos |
| `TXNVL_CMPLJ`, `TXNVL_CMPLJ_1..3` | Texto | Niveles de complejidad | nulos en muestra |
| `TXSUBSECTOR_UND` | Texto | Subsector de la unidad fiscalizable | `HIDROCARBUROS` (8), `PESQUERÍA` (1) |

### 4.2 Administrado y unidad fiscalizable

| Campo | Tipo | Descripción | Observación |
|---|---|---|---|
| `IDADMINISTRADO` | Texto | Código del administrado | `ADM13002` — clave natural de `MI_DIM_ADMINISTRADO` |
| `TXADMINISTRADO` | Texto | Razón social | `MAPLE GAS CORPORATION DEL PERU S.R.L.` |
| `IDSUBUNIDAD` | Texto | Código de la subunidad (UF) | `SUR22764` — clave natural de `DIM_UNIDAD_FISCALIZABLE` |
| `IDUF_SIG` | Texto | Código UF en SIG | `UF0002810` |
| `TXSUBUNIDAD` | Texto | Nombre de la UF | `LOTE 31-E` |
| `TXCOORDINACION` | Texto | Coordinación / dirección responsable | `HIDROCARBUROS`, `PESQUERÍA` |

### 4.3 Responsables (dato personal — controlado por el diccionario)

`TXNOMBRE_RESP_COMISION`, `TXNOMBRE_RESP_MONITOREO`, `TXNOMBRE_ANAL_LEGAL`,
`TXNOMBRE_JEFE_ACTIVIDAD` — nombres de funcionarios. Se conservan en ODS pero
**no se publican** (flags de publicabilidad en `gov.VARIABLE`, Ley N.° 29733).

### 4.4 Ciclo del informe y flujo de aprobación

| Campo | Tipo | Descripción | Observación |
|---|---|---|---|
| `FEINICIO`, `FEFIN` | Timestamp | Inicio y fin de la supervisión en campo | |
| `FEINI_ELAB_INF_ACT`, `FEINI_ELAB_INF` | Timestamp | Inicio de elaboración del informe | |
| `TXNIVELES_REVISION` | Texto | Niveles de revisión con fechas | `Abogado Revisor (22/02/2016), Coordinador (23/02/2016)` |
| `IDEJECFILE_PRY_INF_MIN/MAX`, `IDEJECFILE_INF_MAX`, `IDTIPOEJEFILE_PRY`, `IDGRUPO_REVISION`, `IDEJECFILE_DOC_PREVIO_MAX` | Número | Identificadores internos del flujo de archivos | |
| `FEPRY_REG_INICIAL` | Timestamp | Registro inicial del proyecto | |
| `TXPRY_NIVEL` | Texto | Nivel actual del proyecto | `Coordinador`, `Técnico Revisor` |
| `TXPRY_ESTADO` | Texto | Estado del proyecto de informe | `APROBADO` (4), `EN REVISIÓN` (6) |
| `FEPRY_REG`, `FEPRY_MOD_ESTADO_ESPERADO`, `FEPRY_MOD_ESTADO_REAL` | Timestamp | Hitos del flujo de estado | |
| `TXINFORME` | Texto | N.° de informe emitido | `610-2016-OEFA/DS-HID` |
| `FEINFORME_ESPERADO`, `FEINFORME`, `FEREG_INFORME` | Timestamp | Fecha esperada, real y de registro del informe → base del KPI de oportunidad | |
| `TXRECOMENDACION` | Texto largo | Recomendación del informe | |

### 4.5 Derivación y documento previo

`TX_DOC_DERIVACION`, `TX_NUM_DOC_DERIVACION`, `FE_APROB_DOC_DERIVACION`,
`FE_DERIV_DOC_DERIVACION`, `TXAREADESTINO_MEMO_DERIVACION` (derivación a otras áreas);
`TX_DOCUMENTO_PREVIO`, `TX_NUMERO_DOCUMENTO_PREVIO`, `FE_DOCUMENTO_PREVIO`,
`FE_REGISTRO_DOCUMENTO_PREVIO`, `TX_OTRO_DOCUMENTO_PREVIO` (documento previo).
Nulos en la muestra; se conservan por trazabilidad del ciclo completo.

---

## 5. F4 — MySQL gappsdb · `T_MVC_MULTACOERCITIVA_MC` (**fuera de ingestión**)

Inventario histórico del diagnóstico. **No se stagea ni se carga** en el ETL vigente; solo permanece la semilla `GAPPS` en `MI_DIM_FUENTE_REGISTRO`. Fechas como cadena
`YYYY-MM-DD [HH:MM:SS]`. Grano (histórico): **un registro de MC en la app** (con auditoría).

| Campo | Tipo | Descripción | Observación real |
|---|---|---|---|
| `NU_MONTOMCUIT` | Decimal | Monto de la MC en UIT | 6, 11 |
| `NU_MONTOMCS` | Decimal | Monto de la MC en soles | 2 575, 154 000 |
| `TX_IDCUM` | Texto | Código CUM | `00017333712` (11 dígitos) |
| `TX_IDCAM` | Texto | Código CAM | `20260400002` |
| `TX_RECORD_SEG` | Texto | Recordatorio de seguimiento | `recordatorio rr` ⚠ texto libre |
| `FE_F_VERIF_POST_MC` | Fecha | Fecha de verificación post MC | |
| `TX_DOC_VERIF_MC` | Texto | Documento de verificación | |
| `TX_EXP_SIGED_DOC` | Texto | Expediente SIGED del documento | `78-2026` |
| `FG_ESTADOMULTA` | Flag | Estado de la multa | `1` (flag textual) |
| `NU_IDVERIFICACIONMA`, `NU_IDINFORMACIONMC` | Número | FKs internas de la app | |
| `FE_FECHA_CREACION`, `TX_USUARIO_CREACION`, `FE_FECHA_MODIFICACION`, `TX_USUARIO_MODIFICACION` | Auditoría | Trazabilidad de la app | |
| `TX_ESTADOREGISTRO` | Flag | Estado del registro (borrado lógico) | `1` |
| `TX_PASOACTUAL` | Texto | Paso actual del flujo en la app | `1` |

> ⚠ **Hallazgo H1 confirmado:** 2 de las 4 filas de muestra llegan **casi vacías** (solo
> auditoría, sin montos ni claves) → regla de completitud + tabla de rechazos.

---

## 6. F5 — Oracle SISUD · `VW_MULTA_COERCITIVA`

Vista institucional consolidada de MC. Grano: **una medida administrativa dentro de una
resolución de MC** (un expediente puede repetirse con varias medidas y CUM).

| Campo | Tipo | Descripción | Observación real |
|---|---|---|---|
| `NUMERO_EXPEDIENTE` | Texto | Expediente de origen | `0209-2023-DSIS-CRES` — formato `NNNN-AAAA-SIGLA` |
| `ADMINISTRADO` | Texto | Razón social | ⚠ **nulo en 5 de 10 filas** (H1) |
| `RESOLUCION` | Texto | N.° de resolución | `00004-2025-OEFA/DSIS` |
| `FECHA_EMISION` | Fecha | Fecha de emisión de la resolución | |
| `NUMERO_REGISTRO` | Texto | N.° de registro SIGED | `2025-I01-009335` |
| `ESTADO_RESOLUCION` | Texto | Estado de la resolución | `ACTIVO` / `INACTIVO` |
| `MEDIDA_ADMINISTRATIVA` | Texto largo | Descripción de la medida | ⚠ con **saltos de línea embebidos** (H3) |
| `CUM` | Texto | Código Único de Medida | 11 dígitos: `00000032512` |
| `CAM` | Texto | Código asociado | ⚠ **11 y 13 dígitos** en la misma columna: `20250300003` vs `2025020000005` (H2) |
| `MONTO_MULTA` | Decimal | Monto de la multa en UIT | 1.44 · 1.5 · 2.88 · 32 · 75 · 100 · 128 |
| `MONTO_MULTA_REC` | Decimal | Monto en recurso de reconsideración | nulo en muestra |
| `MONTO_MULTA_TFA` | Decimal | Monto en Tribunal (TFA) | nulo en muestra |
| `ESTADO_MULTA` | Texto | Estado de la multa | `ACTIVO` / `INACTIVO` |

---

## 7. Matriz de correspondencia entre fuentes

> F4 es **histórico** (fuera de ingestión). Lookup vigente: Sheet←SISUD por `norm(N_RES_MC)+MONTO_UIT`.

| Concepto | F1 Sheets OD (31) | F2 Sheets CSEP (10) | F4 gappsdb (hist.) | F5 Vista Oracle | F3 Informes | Modelo DWH |
|---|---|---|---|---|---|---|
| Medida administrativa | `COD_MA` | `COD_MA`/`AUX_COD_MA` | — | (en `MEDIDA_ADMINISTRATIVA`) | — | `COD_MA` |
| Código CUM | — | — | `TX_IDCUM` | `CUM` | — | `CUM` (desde SISUD en enrich) |
| Código CAM | — | — | `TX_IDCAM` | `CAM` | — | `CAM` (desde SISUD en enrich) |
| Expediente supervisión | `EXP_INF_INCUMP` | `EXP_INF_INCUMP` | — | `NUMERO_EXPEDIENTE` | `TXCUC` / `TXNUMEXP` | `NUMERO_EXPEDIENTE` |
| Resolución MC | `N_RES_MC` | `N_RES_MC` | — | `RESOLUCION` | — | `N_RES_MC` (+ clave lookup) |
| Monto UIT | `MULTA_UIT` | `MULTA_UIT` | `NU_MONTOMCUIT` | `MONTO_MULTA` | — | `MONTO_UIT` (+ clave lookup) |
| Monto S/ | `MULTA_S` | `MULTA_S` | `NU_MONTOMCS` | — | — | `MONTO_S` + `MONTO_S_CALC` |
| Estado multa | `ESTADO_MC` | `ESTADO_MC`/`AUX_EST_MC` | `FG_ESTADOMULTA` | `ESTADO_MULTA` | — | `ID_ESTADO_MULTA` |
| Verificación post-MC | `F_VERIF_POST_MC`, `DOC_VERIF_MC` | idem | `FE_F_VERIF_POST_MC`, `TX_DOC_VERIF_MC` | — | — | `F_VERIF_POST_MC`, `DOC_VERIF_MC` |
| SIGED | `SIGED` | `SIGED`, `EXP_SIGED_DOC` | `TX_EXP_SIGED_DOC` | `NUMERO_REGISTRO` | — | `SIGED` |
| Proyecto / etapas | — | `COD_PROY_MC`, hoja `2) Etapas` | `TX_PASOACTUAL` | — | — | `MI_DET_ETAPA_MC` |
| Territorio / unidad | `COD_OD` (inyectado) → `MI_DIM_OD` | `COORD` / `COD_UNIDAD` → `MI_DIM_ORGANO_UNIDAD` (+ `DESCRIPCION`) | — | — | — | dims órgano / OD |
| Universo (`CODIGO`) | `OD_SHEETS` | `CAGR` | `GAPPS` (semilla) | `SISUD_VW` | — | `ID_FUENTE` → dims / `VW_MC_*` |

---

## 8. Hallazgos de calidad confirmados (insumo de las reglas DQ)

| # | Hallazgo | Evidencia verificada | Tratamiento |
|---|---|---|---|
| H1 | Nulos en campos clave y filas casi vacías | `ADMINISTRADO` nulo en muestra F5; (hist.) filas F4 casi vacías | Regla R01 + tabla de rechazos |
| H2 | Formatos heterogéneos de CAM | `20250300003` (11) vs `2025020000005` (13) en F5 | Normalización documentada `AAAA+SS+7` (R03) |
| H3 | Texto multilínea en `MEDIDA_ADMINISTRATIVA` | saltos de línea embebidos en F5 | Limpieza de caracteres de control en ODS |
| H4 | Heterogeneidad de motores y fechas | Oracle vs Sheets (F4 hist. fuera) | Parseo tipificado único a `DATE` |
| H5 | Lógica de negocio en fórmulas Excel | `WORKDAY.INTL`, `ArrayFormula`, `INDEX/MATCH` | Migración de reglas a la capa DWH documentada |
| H6 | Catálogos / IMPORTRANGE históricos | Plantillas Excel con `#REF!` (no stageados) | UIT desde MEF; DIC desde Excel legacy |
| H7 | Dos layouts de registro de MC | F1 (32 col OD) vs F2 (48 col CSEP) | 3 facts evidencia + enrich; attrs F2 en hechos |
| H8 | Estados como texto libre | `INCUMPLIDO` (F1/F2), `ACTIVO`/`INACTIVO` (F5) | `MI_DIM_ESTADO` con homologación |
| H9 | Claves de cruce sin correspondencia total | Sheets↔SISUD por resolución+monto | `RES_MONTO_Sheets_vs_SISUD` → `MI_QA_AMARRE*` / K5 |

---

**Siguiente:** [02 · Modelo dimensional](02-modelo-dimensional.md)

