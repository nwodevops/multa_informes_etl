# 01 - Fuentes de Datos

## Inventario de Sistemas Origen

### 1. Oracle SISUD - Sistema de Supervisión

#### Tabla: `SISUD.CSEP_INFORMES_VIEW`

Contiene los informes de supervisión y actividades de fiscalización.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| IDACTIVIDAD | NUMBER | Identificador de la actividad |
| TXMES | VARCHAR2 | Mes de la actividad |
| TXNUMEXP | VARCHAR2 | Número de expediente |
| TXCUC | VARCHAR2 | Código CUC (expediente) |
| TXESTADO | VARCHAR2 | Estado del expediente (EN CUSTODIA, etc.) |
| IDADMINISTRADO | VARCHAR2 | Código del administrado |
| TXADMINISTRADO | VARCHAR2 | Razón social del administrado |
| IDSUBUNIDAD | VARCHAR2 | Código de sub-unidad fiscalizable |
| TXSUBUNIDAD | VARCHAR2 | Nombre de la unidad fiscalizable |
| TXCOORDINACION | VARCHAR2 | Coordinación responsable |
| TXTIPSUP | VARCHAR2 | Tipo de supervisión (ESPECIAL, REGULAR) |
| TXFUENTE | VARCHAR2 | Fuente de la actividad (PLANEFA, OTRA) |
| FEINICIO | TIMESTAMP | Fecha de inicio de la supervisión |
| FEFIN | TIMESTAMP | Fecha de fin de la supervisión |
| TXNVL_CMPLJ | VARCHAR2 | Nivel de cumplimiento |
| TXNOMBRE_RESP_COMISION | VARCHAR2 | Nombre del responsable de comisión |
| TXNOMBRE_RESP_MONITOREO | VARCHAR2 | Nombre del responsable de monitoreo |
| TXSUBSECTOR_UND | VARCHAR2 | Sub-sector de la unidad |
| TXPRY_ESTADO | VARCHAR2 | Estado del proyecto (APROBADO, EN REVISIÓN) |
| TXINFORME | VARCHAR2 | Número de informe |
| FEINFORME | TIMESTAMP | Fecha del informe |
| TXRECOMENDACION | VARCHAR2 | Recomendación del informe |

**Volumen estimado**: ~50,000+ registros históricos

---

#### Tabla: `SISUD.VW_MULTA_COERCITIVA`

Vista consolidada de multas coercitivas con información de expedientes y estados.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| NUMERO_EXPEDIENTE | VARCHAR2 | Número de expediente SIGED |
| ADMINISTRADO | VARCHAR2 | Razón social del administrado |
| RESOLUCION | VARCHAR2 | Número de resolución |
| FECHA_EMISION | DATE | Fecha de emisión de la resolución |
| NUMERO_REGISTRO | VARCHAR2 | Número de registro SIGED |
| ESTADO_RESOLUCION | VARCHAR2 | Estado (ACTIVO, INACTIVO) |
| MEDIDA_ADMINISTRATIVA | VARCHAR2 | Descripción de la medida administrativa |
| CUM | VARCHAR2 | Código Único de Medida |
| CAM | VARCHAR2 | Código de Acción de Monitoreo |
| MONTO_MULTA | NUMBER | Monto de la multa en UIT |
| MONTO_MULTA_REC | NUMBER | Monto de multa por recargo |
| MONTO_MULTA_TFA | NUMBER | Monto de multa TFA |
| ESTADO_MULTA | VARCHAR2 | Estado de la multa (ACTIVO, INACTIVO) |

**Volumen estimado**: ~10,000+ registros

---

### 2. Oracle GApps - Gestión Operativa

#### Tabla: `gappsdb.T_MVC_MULTACOERCITIVA_MC`

Detalle operativo de multas coercitivas - sistema de gestión.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| NU_MONTOMCUIT | NUMBER | Monto multa en UIT |
| NU_MONTOMCS | NUMBER | Monto multa en soles |
| TX_IDCUM | VARCHAR2 | ID del CUM |
| TX_IDCAM | VARCHAR2 | ID del CAM |
| TX_RECORD_SEG | VARCHAR2 | Recordatorio de seguimiento |
| FE_F_VERIF_POST_MC | DATE | Fecha verificación post multa |
| TX_DOC_VERIF_MC | VARCHAR2 | Documento de verificación |
| TX_EXP_SIGED_DOC | VARCHAR2 | Expediente SIGED del documento |
| FG_ESTADOMULTA | VARCHAR2 | Estado de la multa (1=Activo) |
| NU_IDVERIFICACIONMA | NUMBER | ID de verificación de medida |
| NU_IDINFORMACIONMC | NUMBER | ID de información de MC |
| FE_FECHA_CREACION | DATETIME | Fecha de creación del registro |
| TX_USUARIO_CREACION | VARCHAR2 | Usuario creador |
| FE_FECHA_MODIFICACION | DATETIME | Fecha última modificación |
| TX_USUARIO_MODIFICACION | VARCHAR2 | Usuario modificador |
| TX_ESTADOREGISTRO | VARCHAR2 | Estado del registro |
| TX_PASOACTUAL | VARCHAR2 | Paso actual del proceso |

**Volumen estimado**: ~5,000+ registros

---

### 3. Archivos Excel - Datos Manuales

#### Excel: Medidas Administrativas OD Lambayeque

| Hoja | Contenido |
|------|-----------|
| M_FERIADO | Calendario de feriados nacionales y locales |
| M_UBIGEO | Departamento, Provincia, Distrito |
| M_PARAMETROS | Parámetros generales: UIT, tipos de solicitud, resoluciones |
| 5) Multas Coercitivas | Tracking manual de multas coercitivas por OD |

**Campos clave del tracking de multas:**

| Campo | Código | Descripción |
|-------|--------|-------------|
| COD_MA | COD_MA | Código de la medida administrativa |
| EXP_INF_INCUMP | EXP_INF_INCUMP | Expediente informe de incumplimiento |
| N_CARTA_DCG | N_CARTA_DCG | N° de carta que requiere descargos |
| FN_MC | FN_MC | Fecha de notificación |
| F_VENC_DCG | F_VENC_DCG | Fecha de vencimiento de descargos |
| PRESENT_DCG_ADM | PRESENT_DCG_ADM | ¿Presentó descargos? (SI/NO) |
| F_RPTA_ADM | F_RPTA_ADM | Fecha respuesta del administrado |
| F_INIC_ANALISIS | F_INIC_ANALISIS | Fecha inicio de análisis |
| REQ_VERIF_CAMPO | REQ_VERIF_CAMPO | ¿Requiere verificación en campo? |
| F_VERIF_CAMPO | F_VERIF_CAMPO | Fecha verificación en campo |
| F_FIN_ANALISIS | F_FIN_ANALISIS | Fecha fin de análisis |
| AMERIT_MC | AMERIT_MC | ¿Amerita multa? (SI/NO) |
| EXP_RES_MC | EXP_RES_MC | Expediente con resolución de MC |
| N_RES_MC | N_RES_MC | N° de resolución de MC |
| F_FIRMA_RES_MC | F_FIRMA_RES_MC | Fecha firma de resolución |
| FN_RES_MC | FN_RES_MC | Fecha notificación de resolución |
| F_VENC_MC | F_VENC_MC | Fecha vencimiento de multa |
| MULTA_UIT | MULTA_UIT | Multa en UIT |
| MULTA_S | MULTA_S | Multa en soles |
| RECORD_SEG | RECORD_SEG | Recordatorio nuevo seguimiento |
| F_VERIF_POST_MC | F_VERIF_POST_MC | Fecha verificación post multa |
| ESTADO_MC | ESTADO_MC | Estado de la multa (INCUMPLIDO, PAGADO) |
| MEMO_EF | MEMO_EF | Memorándum de traslado a ejecución forzosa |
| F_REMIS | F_REMIS | Fecha remisión del memorándum |

---

#### Excel: CAGR Multas Coercitivas

| Hoja | Contenido |
|------|-----------|
| DIC_TABLAS | Diccionario de datasets |
| DIC_VARIABLES | Diccionario de variables con código, descripción y tipo |
| 1) Multas coercitivas | Tracking completo de lifecycle de multas por CAGR |
| 2) Etapas | Detalle de etapas de elaboración de cada proyecto MC |
| PARAMETROS | Parámetros de configuración |
| MA_INDIVIDUALES | Lista de medidas administrativas individuales |
| Equipo | Equipo de trabajo (nombre, estado) |

**Campos adicionales del tracking CAGR:**

| Campo | Código | Descripción |
|-------|--------|-------------|
| COD_PROY_MC | COD_PROY_MC | Código proyecto de multa coercitiva |
| JEFE | JEFE | Jefe de equipo responsable |
| ETA_REG_PROY_MC | ETA_REG_PROY_MC | Etapa de registro del proyecto |
| N_PROY_MC | N_PROY_MC | Número de proyecto |
| COORD | COORD | Coordinación |
| ADM | ADM | Administrado |
| UF | UF | Unidad fiscalizable |
| EST_DCG | EST_DCG | Estado de descargos |
| AMERIT_MC | AMERIT_MC | ¿Amerita multa? |
| RESULT_PROY_MC | RESULT_PROY_MC | Resultado del proyecto |
| ESTADO_MC | ESTADO_MC | Estado de la multa |
| ESTADO_PAGO_MC | ESTADO_PAGO_MC | Estado del pago de la multa |
| URESOL_MC | URESOL_MC | Última resolución de MC |
| FN_URESOL_MC | FN_URESOL_MC | Fecha notificación última resolución |

---

**Hoja: 2) Etapas**

| Campo | Código | Descripción |
|-------|--------|-------------|
| COD_PROY_MC | COD_PROY_MC | Código proyecto MC |
| NRO_ETAPA_MC | NRO_ETAPA_MC | Número de etapa |
| PERF_ENCARG_MC | PERF_ENCARG_MC | Perfil del encargado |
| ACCION_MC | ACCION_MC | Acción (ELABORACIÓN, REVISIÓN, CÁLCULO, FIRMA) |
| ENCARGADO_MC | ENCARGADO_MC | Nombre del encargado |
| F_ASIG_MC | F_ASIG_MC | Fecha de asignación |
| EST_ETAPA_MC | EST_ETAPA_MC | Estado de la etapa (TERMINADO, PENDIENTE) |
| CONFORMIDAD_MC | CONFORMIDAD_MC | Conformidad (CONFORME, NO APLICA) |
| F_ENT_DEV_MC | F_ENT_DEV_MC | Fecha entrega/devolución |
| T_ELAB_MC | T_ELAB_MC | Tiempo de elaboración (días) |

---

### 4. Mapeo de Relaciones entre Fuentes

```
SISUD.CSEP_INFORMES_VIEW
    └── TXCUC ──────────┐
                         │
SISUD.VW_MULTA_COERCITIVA│
    └── CUM ─────────────┼──► Relación por código CUM/CUC
                         │
gappsdb.T_MVC_MULTACOERCITIVA_MC
    └── TX_IDCUM ────────┘

Excel Tracking Multas
    └── COD_MA ──────────► Códigos de medida administrativa
                         │
Excel 2) Etapas
    └── COD_PROY_MC ─────┘──► Relación proyecto ↔ etapas
```

### 5. Calidad de Datos Observada

| Problema | Fuente | Impacto |
|----------|--------|---------|
| Códigos de expediente inconsistentes | GApps vs SISUD | Dificulta cruce de datos |
| Campos con `#REF!`, `#N/A`, `#VALUE!` | Excel CAGR | Errores en transformación |
| Fechas en formato mixto | Todos | Requiere normalización |
| Nulos en campos obligatorios | SISUD | Impacta KPIs de completitud |
| Datos duplicados | Excel | Requiere deduplicación |
| Caracteres especiales (tildes) | Excel | Problemas de encoding |
