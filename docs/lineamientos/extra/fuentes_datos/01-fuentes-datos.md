# 01 - Fuentes de Datos

> **Alcance vigente:** el DW carga solo Multas (F1, F2, F4, F5). La vista `CSEP_INFORMES_VIEW` (F3) no se extrae ni se modela.
>
> **Inputs runtime:** [`docs/inputs/README.md`](../../../inputs/README.md) · catálogos F1/F2 JSON · `inputs.yaml`.

## Inventario de Sistemas Origen

### 1. Oracle SISUD - Sistema de Supervisión

#### Tabla: `SISUD.CSEP_INFORMES_VIEW`

Contiene los informes de supervisión y actividades de fiscalización. **Fuera de alcance del ETL.**

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

#### Tabla: `SISUD.VW_MULTA_COERCITIVA` (F5)

Vista consolidada de multas coercitivas. Staging: `STG_ORA_VW_MULTA_COERCITIVA` · Hop `pl_stage_oracle.hpl`.

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

**Volumen estimado**: ~10,000+ registros · universo DW `SISUD_VW` (`ID_FUENTE`)

---

### 2. MySQL GAPP - Gestión operativa (F4)

#### Tabla: `gappsdb.T_MVC_MULTACOERCITIVA_MC`

Staging: `STG_MYSQL_T_MVC_MULTACOERCITIVA` · Hop `pl_stage_mysql.hpl` · universo `GAPPS`.

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

### 3. Google Sheets — F1 familia OD (31 oficinas)

Catálogo: [`docs/inputs/f1_ods_sheets.json`](../../../inputs/f1_ods_sheets.json).  
Staging: `STG_GS2_OD_MULTAS` (+ `COD_OD`) · `scripts/stage_ods_sheets.sh` · universo `OD_SHEETS` (`VW_MC_OD`).

| Elemento | Valor |
|----------|--------|
| Hoja | `5) Multas Coercitivas` |
| Header | Fila 3 (códigos) |
| Rango Hop | `'5) Multas Coercitivas'!A3:AF` (32 columnas) |
| Dimensión territorio | `MI_DIM_OD` vía `COD_OD` |

Excel OD histórico: `input_excel/medidas_administrativas/legacy/` (ya no es input).

**Campos clave (hoja multas):**

| Campo | Descripción |
|-------|-------------|
| COD_MA | Código de la medida administrativa |
| EXP_INF_INCUMP | Expediente informe de incumplimiento |
| N_CARTA_DCG | N° de carta que requiere descargos |
| FN_MC | Fecha de notificación |
| F_VENC_DCG | Fecha de vencimiento de descargos |
| PRESENT_DCG_ADM | ¿Presentó descargos? (SI/NO) |
| F_RPTA_ADM | Fecha respuesta del administrado |
| F_INIC_ANALISIS | Fecha inicio de análisis |
| REQ_VERIF_CAMPO | ¿Requiere verificación en campo? |
| F_VERIF_CAMPO | Fecha verificación en campo |
| F_FIN_ANALISIS | Fecha fin de análisis |
| AMERIT_MC | ¿Amerita multa? (SI/NO) |
| EXP_RES_MC | Expediente con resolución de MC |
| N_RES_MC | N° de resolución de MC |
| F_FIRMA_RES_MC | Fecha firma de resolución |
| FN_RES_MC | Fecha notificación de resolución |
| F_VENC_MC | Fecha vencimiento de multa |
| MULTA_UIT | Multa en UIT |
| MULTA_S | Multa en soles |
| RECORD_SEG | Recordatorio nuevo seguimiento |
| F_VERIF_POST_MC | Fecha verificación post multa |
| ESTADO_MC | Estado de la multa (INCUMPLIDO, PAGADO) |
| MEMO_EF | Memorándum de traslado a ejecución forzosa |
| F_REMIS | Fecha remisión del memorándum |
| SIGED | N° SIGED |

Detalle columna a columna: [`01-fuentes-de-datos.md`](01-fuentes-de-datos.md) §2.

---

### 4. Google Sheets — F2 unidades CSEP (10)

Catálogo: [`docs/inputs/f2_csep_sheets.json`](../../../inputs/f2_csep_sheets.json).  
Staging: `STG_GS1_CSEP_MULTAS` (+ `COD_UNIDAD`) + `STG_GS1_ETAPAS` · `scripts/stage_csep_sheets.sh` · universo `CAGR` (`VW_MC_CSEP`).

| # | `cod_unidad` | Descripción (dim órgano) |
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

| Elemento | Multas | Etapas |
|----------|--------|--------|
| Hoja | `1) Multas coercitivas` | `2) Etapas` |
| Header | Fila 3 (48 cols) | Fila 2 (12 cols) |
| Rango Hop | `'1) Multas coercitivas'!A3:AV` | `'2) Etapas'!A2:L` |

**Campos adicionales vs F1 (multas):** `COD_PROY_MC`, `JEFE`, `ETA_REG_PROY_MC`, `N_PROY_MC`, `COORD`, `ADM`, `UF`, `EST_DCG`, `RESULT_PROY_MC`, `ETA_REG_MC`, `ESTADO_PAGO_MC`, auxiliares (`AUX_*`, `URESOL_MC`, `FN_URESOL_MC`).

**Etapas:** `COD_PROY_MC`, `NRO_ETAPA_MC`, `PERF_ENCARG_MC`, `ACCION_MC`, `ENCARGADO_MC`, `F_ASIG_MC`, `EST_ETAPA_MC`, `CONFORMIDAD_MC`, `F_ENT_DEV_MC`, `T_ELAB_MC`, `COD_ETAPA_MC`, `AUX_FIN_MC`.

**DIC (Excel legacy):** `DIC_TABLAS` / `DIC_VARIABLES` desde `input_excel/legacy/CAGR_…xlsx` → `STG_GS1_DIC_*` (`pl_stage_excel.hpl`).

---

### 5. Mapeo de Relaciones entre Fuentes

```
SISUD.VW_MULTA_COERCITIVA (F5)
    └── CUM / CAM ──────────┐
                             ├──► MI_QA_AMARRE / MI_QA_AMARRE_DETALLE / K5
gappsdb.T_MVC_MULTACOERCITIVA_MC (F4)
    └── TX_IDCUM / TX_IDCAM ─┘

F1 Sheets OD (31)
    └── COD_MA + COD_OD ───► MI_DIM_OD · ID_FUENTE=OD_SHEETS · VW_MC_OD

F2 Sheets CSEP (10)
    └── COD_MA + COORD ────► MI_DIM_ORGANO_UNIDAD (DESCRIPCION) · ID_FUENTE=CAGR · VW_MC_CSEP
    └── COD_PROY_MC ───────► MI_DET_ETAPA_MC
```

### 6. Calidad de Datos Observada

| Problema | Fuente | Impacto |
|----------|--------|---------|
| Códigos de expediente inconsistentes | GAPP vs SISUD | Dificulta cruce (H9) |
| Tokens `#REF!` / `#N/A` residuales | Sheets / legacy Excel | Homologación / cuarentena blanda |
| Fechas heterogéneas | Todos | Parseo unificado en Python |
| Nulos en campos obligatorios | SISUD / Sheets | Completitud / DQ |
| Sheets vacíos (p. ej. CPES, CCAM) | F2 CSEP | Unidad sembrada en dim con n_fact=0 |
| Rate limit Google (429/503) | F1/F2 Sheets | Reintentos en `stage_*_sheets.sh` |
