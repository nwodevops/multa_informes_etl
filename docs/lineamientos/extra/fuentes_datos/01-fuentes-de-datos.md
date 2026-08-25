# 01 · Fuentes de Datos — Inventario Detallado

> **Proyecto:** Data Warehouse OEFA — Estrategias de promoción del cumplimiento
> **Referencia:** TDR REQ N.° 3629-2026 · Área usuaria: CSEP — DPEF
> **Contenido:** inventario campo por campo de las 5 fuentes, con tipos, descripciones,
> dominios observados y hallazgos de calidad **verificados sobre los archivos reales**.

---

## 1. Resumen de fuentes

| ID | Fuente | Tipo / Motor origen | Contenido | Estructura real verificada |
|---|---|---|---|---|
| **F1** | `Copia de MEDIDAS ADMINISTRATIVAS OD LAMBAYEQUE.xlsx` | Excel (migrado de Google Sheets) | Registro operativo de MC — OD Lambayeque + catálogos | 4 hojas: `5) Multas Coercitivas` (32 col, **21 filas con datos**), `M_FERIADO`, `M_UBIGEO`, `M_PARAMETROS` |
| **F2** | `Copia de Modificado CAGR_ MA OEFA - 3) MULTAS COERCITIVAS.xlsx` | Excel (migrado de Google Sheets) | Registro evolucionado de MC — CAGR + workflow de etapas + gobierno de datos | 7 hojas: `1) Multas coercitivas` (48 col, **7 filas**), `2) Etapas` (12 col, **7 filas**), `Equipo` (**20 filas**), `DIC_TABLAS`, `DIC_VARIABLES` (594 filas de estructura), `PARAMETROS`, `MA_INDIVIDUALES` |
| **F3** | `CSEP_INFORMES_VIEW_202608130925.sql` | Respaldo SQL — **Oracle** (esquema `SISUD`) | Informes de supervisión ambiental | `CSEP_INFORMES_VIEW`: **56 columnas**, 10 filas de muestra |
| **F4** | `T_MVC_MULTACOERCITIVA_MC_202608111806.sql` | Respaldo SQL — **SQL Server** (base `gappsdb`) | Tabla transaccional de la aplicación de MC | `T_MVC_MULTACOERCITIVA_MC`: **17 columnas**, 4 filas de muestra |
| **F5** | `VW_MULTA_COERCITIVA_202608111808.sql` | Respaldo SQL — **Oracle** (esquema `SISUD`) | Vista institucional consolidada de MC | `VW_MULTA_COERCITIVA`: **13 columnas**, 10 filas de muestra |

> **Nota de volumen:** los conteos corresponden a los respaldos/muestras entregados con el
> TDR. El diseño es independiente del volumen (rangos esperados: miles a decenas de miles
> de filas por año).

---

## 2. F1 — Excel Medidas Administrativas OD Lambayeque

Libro operativo migrado desde Google Sheets. Convención: fila 1 = sección (etapa del ciclo
de vida), fila 2 = descripción larga, **fila 3 = códigos de campo** (nombres técnicos);
los datos inician en la fila 4.

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

### 2.2 Catálogos de F1 (⚠ con IMPORTRANGE rotos en la copia entregada)

| Hoja | Columnas | Contenido esperado | Estado en la copia |
|---|---|---|---|
| `M_FERIADO` | `Feriados` | Calendario de feriados (base del cómputo de días hábiles) | ❌ `#REF!` — 0 filas válidas |
| `M_UBIGEO` | `DEPARTAMENTO`, `PROVINCIA`, `DISTRITO` | Catálogo geográfico (~1 893 distritos) | ❌ `#REF!` — 0 filas válidas |
| `M_PARAMETROS` | `SOLICITUD_CATEGORIA`, `PLAZO`, `CLAVE_CONSECUENCIA`, `CONSECUENCIA_RESPUESTA`, `AÑO`, `UIT`, `TIPO_SOLICITUD`, `SOLICITUD`, `RESPUESTA`, `Resolución`, `firmeza`, `OD` | UIT por año, plazos, tipos de solicitud, resoluciones y firmeza | ❌ `#REF!` en col. A; solo datos residuales en columnas J–L |

> **Acción requerida (semana 1):** solicitar a la CSEP la exportación **con valores** o el
> acceso a la fuente viva. Mientras tanto, la UIT se siembra con los valores oficiales del
> MEF (ver `07-consideraciones-especiales.md`).

---

## 3. F2 — Excel CAGR Multas Coercitivas

Versión evolucionada del registro de F1: agrega gestión de proyectos (workflow de etapas),
estado de pago, campos auxiliares y diccionario de datos. Misma convención de F1
(fila 3 = códigos de campo).

### 3.1 Hoja `1) Multas coercitivas` (48 columnas)

Contiene las 32 columnas de F1 (mismos códigos) **más** las siguientes:

| Código | Sección | Tipo | Descripción | Dominio observado |
|---|---|---|---|---|
| `COD_PROY_MC` | CÓDIGOS | Texto | Código de proyecto de MC | `MULTA COERCITIVA - 1/CÓDIGO DE EXPEDIENTE INVÁLIDO` ⚠ |
| `JEFE` | ESTADO | Texto | Jefe de equipo responsable | `PEÑA, AGUSTÍN` (6), `RIMACHI, LUIS` (1) |
| `ETA_REG_PROY_MC` | ESTADO | Texto | Etapa de registro del proyecto | `EN ETAPA DE COBRANZA` (7) |
| `N_PROY_MC` | — | Entero | N.° de proyecto | 1..5 |
| `COORD` | INF. GENERAL | Texto | Coordinación | ⚠ `CÓDIGO DE EXPEDIENTE INVÁLIDO` (fórmula rota) |
| `ADM` | INF. GENERAL | Texto | Administrado | ⚠ idem |
| `UF` | INF. GENERAL | Texto | Unidad fiscalizable | ⚠ idem |
| `EST_DCG` | DESCARGOS | Texto | Estado de descargos | `NO PRESENTÓ DESCARGOS` (7) |
| `RESULT_PROY_MC` | RESULTADO | Texto | Resultado del proyecto | `ELABORAR MC` (7) |
| `ETA_REG_MC` | ETAPAS REG. | Texto | Etapas de registro de la MC | `SIN REGISTRO DE ETAPAS` (7) |
| `ESTADO_PAGO_MC` | COBRANZA | Texto | Estado del pago de la multa | `NO PAGÓ MULTA` (7) |
| `AUX_FIN_MC` | AUXILIARES | Entero | Auxiliar de finalizado | `-1` (verdadero en Sheets) |
| `AUX_COD_MA` | AUXILIARES | Texto | COD_MA auxiliar | |
| `AUX_EST_MC` | AUXILIARES | Texto | Estado auxiliar de MC | ⚠ `#VALUE!` |
| `URESOL_MC` | AUXILIARES | Texto | Última resolución de MC | ⚠ `#VALUE!` |
| `FN_URESOL_MC` | AUXILIARES | Fecha | Fecha de notificación de la última resolución | |

> **Observación:** `MULTA_S` llega como `#N/A` en las 7 filas (referencia rota a
> parámetros) → en el DWH el monto en soles se **recalcula** siempre como
> `MULTA_UIT × UIT(año)`.

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

| Hoja | Estructura | Estado |
|---|---|---|
| `Equipo` | `RESPONSABLE`, `ESTADO`, `RESPONSABLE` (lista duplicada) | ✅ 20 personas, todas `ACTIVO` |
| `DIC_TABLAS` | `DATASET`, `DESCRIPCION / INSTRUCCIONES` | ✅ 2 datasets documentados |
| `DIC_VARIABLES` | `DATASET`, `SECCION`, `CAMPO EN BD`, `CODIGO CAMPO`, `CAMPO NO PUBLICABLE`, `NO PUBLICABLE PERO NECESARIO (CSEP)`, `VARIABLES DE LLENADO MINIMO`, `DESCRIPCION`, `TIPO DE VARIABLE` | ❌ 594 filas de estructura con `#REF!` (IMPORTRANGE roto) — **reconstruir como activo institucional** |
| `PARAMETROS` | 26 columnas | ❌ `#REF!` |
| `MA_INDIVIDUALES` | 18 columnas | Parcial: solo lista de proyectos que ameritan multa (col. R) |

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
| `IDADMINISTRADO` | Texto | Código del administrado | `ADM13002` — clave natural de `DIM_ADMINISTRADO` |
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

## 5. F4 — SQL Server gappsdb · `T_MVC_MULTACOERCITIVA_MC`

Tabla transaccional de la aplicación web de multas coercitivas. Fechas como cadena
`YYYY-MM-DD [HH:MM:SS]`. Grano: **un registro de MC en la app** (con auditoría).

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

| Concepto | F1 Excel OD Lamb. | F2 Excel CAGR | F4 gappsdb | F5 Vista Oracle | F3 Informes | Modelo DWH |
|---|---|---|---|---|---|---|
| Medida administrativa | `COD_MA` | `COD_MA`/`AUX_COD_MA` | — | (en `MEDIDA_ADMINISTRATIVA`) | — | `COD_MA` |
| Código CUM | — | — | `TX_IDCUM` | `CUM` | — | `CUM` (normalizado, 11 díg.) |
| Código CAM | — | — | `TX_IDCAM` | `CAM` | — | `CAM` (normalizado, 13 díg.) |
| Expediente supervisión | `EXP_INF_INCUMP` | `EXP_INF_INCUMP` | — | `NUMERO_EXPEDIENTE` | `TXCUC` / `TXNUMEXP` | `NUMERO_EXPEDIENTE` → amarre a hecho de supervisión |
| Resolución MC | `N_RES_MC` | `N_RES_MC` | — | `RESOLUCION` | — | `N_RES_MC` |
| Monto UIT | `MULTA_UIT` | `MULTA_UIT` | `NU_MONTOMCUIT` | `MONTO_MULTA` | — | `MONTO_UIT` (conciliado R07) |
| Monto S/ | `MULTA_S` | `MULTA_S` (roto: `#N/A`) | `NU_MONTOMCS` | — | — | `MONTO_S` + `MONTO_S_CALC` |
| Estado multa | `ESTADO_MC` | `ESTADO_MC`/`AUX_EST_MC` | `FG_ESTADOMULTA` | `ESTADO_MULTA` | — | `ID_ESTADO_MULTA` (homologado) |
| Verificación post-MC | `F_VERIF_POST_MC`, `DOC_VERIF_MC` | idem | `FE_F_VERIF_POST_MC`, `TX_DOC_VERIF_MC` | — | — | `F_VERIF_POST_MC`, `DOC_VERIF_MC` |
| SIGED | `SIGED` | `SIGED`, `EXP_SIGED_DOC` | `TX_EXP_SIGED_DOC` | `NUMERO_REGISTRO` | — | `SIGED` |
| Proyecto / etapas | — | `COD_PROY_MC`, hoja `2) Etapas` | `TX_PASOACTUAL` | — | — | `FACT_ETAPA_MC` |

---

## 8. Hallazgos de calidad confirmados (insumo de las reglas DQ)

| # | Hallazgo | Evidencia verificada | Tratamiento |
|---|---|---|---|
| H1 | Nulos en campos clave y filas casi vacías | `ADMINISTRADO` nulo en 5/10 filas de F5; 2/4 filas de F4 solo con auditoría | Regla R01 + tabla de rechazos |
| H2 | Formatos heterogéneos de CAM | `20250300003` (11) vs `2025020000005` (13) en F5 | Normalización documentada `AAAA+SS+7` (R03) |
| H3 | Texto multilínea en `MEDIDA_ADMINISTRATIVA` | saltos de línea embebidos en F5 | Limpieza de caracteres de control en ODS |
| H4 | Heterogeneidad de motores y fechas | Oracle `TIMESTAMP'...'` (F3) vs cadenas ISO (F4) | Parseo tipificado único a `DATE` |
| H5 | Lógica de negocio en fórmulas Excel | `WORKDAY.INTL`, `ArrayFormula`, `INDEX/MATCH` | Migración de reglas a la capa DWH documentada |
| H6 | IMPORTRANGE rotos | `M_FERIADO`, `M_UBIGEO`, `M_PARAMETROS`, `DIC_VARIABLES`, `PARAMETROS` con `#REF!` | Materialización de catálogos + solicitud a CSEP |
| H7 | Dos versiones del registro de MC | F1 (32 col) vs F2 (48 col) con códigos comunes | Integración en una tabla con `FUENTE_ORIGEN` |
| H8 | Estados como texto libre | `INCUMPLIDO` (F1), `ACTIVO`/`INACTIVO` (F5), `1` (F4), `EN REVISIÓN` (F3) | `DIM_ESTADO` con homologación aprobada por CSEP |
| H9 | Claves de cruce múltiples sin correspondencia total | `CUM`/`CAM` (F4↔F5), `COD_MA` (F1↔F2), expedientes (F5↔F3) | Tabla puente de equivalencias + tasa de amarre medida |

---

**Siguiente:** [02 · Modelo dimensional](02-modelo-dimensional.md)

