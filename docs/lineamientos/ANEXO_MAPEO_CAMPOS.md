# Anexo — Mapeo Campo a Campo (Fuentes → Modelo Dimensional)

> Complementa `PROPUESTA_ADAPTADA_ETL.md` y los DDL en `ddl/`. Este anexo cierra la brecha
> entre "qué tablas construir" y "de dónde sale exactamente cada columna", para que la capa
> lógica (Python) se pueda escribir sin ambigüedad.
>
> Inventario de fuentes: [`extra/fuentes_datos/01-fuentes-de-datos.md`](extra/fuentes_datos/01-fuentes-de-datos.md).
> Inputs runtime: [`docs/inputs/README.md`](../inputs/README.md) · catálogos F1/F2 JSON · `inputs.yaml`.
> F3 (informes) está **fuera de alcance**.

---

## 0. Fuentes y su identificador corto

| ID | Fuente (vigente) | Objeto / STG | Columnas |
|---|---|---|---|
| F1 | **31 Google Sheets** OD (`f1_ods_sheets.json`) | hoja `5) Multas Coercitivas` → `STG_GS2_OD_MULTAS` (+ `COD_OD`) | 32 |
| F2 | **10 Google Sheets** CSEP (`f2_csep_sheets.json`) | hoja `1) Multas coercitivas` → `STG_GS1_CSEP_MULTAS` (+ `COD_UNIDAD`) | 48 (32 comunes F1 + 16 propias) |
| F2-ET | Mismos sheets F2 | hoja `2) Etapas` → `STG_GS1_ETAPAS` | 12 |
| F4 | MySQL gapps | `T_MVC_MULTACOERCITIVA_MC` → `STG_MYSQL_*` | 17 |
| F5 | Oracle SISUD | `VW_MULTA_COERCITIVA` → `STG_ORA_*` | 13 |

| `CODIGO` (`MI_DIM_FUENTE_REGISTRO`) | Significado |
|---|---|
| `OD_SHEETS` | Fila procedente de F1 (Sheets OD) |
| `CAGR` | Fila procedente de F2 (Sheets CSEP; unidad en `COORD` / `COD_UNIDAD`) |
| `GAPPS` | F4 MySQL |
| `SISUD_VW` | F5 Oracle |

Dimensión formal: `MI_DIM_FUENTE_REGISTRO` (`ID_FUENTE` en el hecho y en etapas). El VARCHAR degenerado `FUENTE_REGISTRO` **se eliminó** del hecho; usar `CODIGO` vía join o vistas `VW_MC_*`.

> Excel OD / CAGR históricos viven en `input_excel/.../legacy/`. Solo el DIC (`DIC_TABLAS` / `DIC_VARIABLES`) se stagea aún desde el Excel CAGR legacy (`pl_stage_excel.hpl`).

**Regla general de prioridad cuando dos fuentes traen el mismo dato:** se prioriza la fuente
más confiable/reciente y se conserva el resto como respaldo con su `ID_FUENTE` visible;
nunca se descarta el dato divergente, se registra como hallazgo de calidad (R… según regla
aplicable, ver sección 4 de `PROPUESTA_ADAPTADA_ETL.md`).

---

## 1. `MI_FACT_MULTA_COERCITIVA`

| Columna destino | Origen principal | Origen(es) secundario(s) / conciliación | Transformación |
|---|---|---|---|
| `COD_MA` | F1/F2 `COD_MA` | F2 `AUX_COD_MA` (si `COD_MA` viene roto) | ninguna (clave natural) |
| `COD_PROY_MC` | F2 `COD_PROY_MC` | — | ninguna |
| `NUMERO_EXPEDIENTE` | F5 `NUMERO_EXPEDIENTE` | F1/F2 `EXP_INF_INCUMP` | normalizar formato `NNNN-AAAA-SIGLA` |
| `EXP_RES_MC` | F1/F2 `EXP_RES_MC` | — | ninguna |
| `N_RES_MC` | F1/F2 `N_RES_MC` | F5 `RESOLUCION` (conciliar) | ninguna |
| `CUM` | F5 `CUM` | F4 `TX_IDCUM` (conciliar, regla R04) | solo dígitos, relleno a 11 posiciones (H2) |
| `CAM` | F5 `CAM` | F4 `TX_IDCAM` (conciliar, regla R04) | patrón `AAAA`(4)+segmento(2)+correlativo(7)=13 (H2) |
| `NUMERO_REGISTRO_SIGED` | F5 `NUMERO_REGISTRO` | F1/F2 `SIGED`; F4 `TX_EXP_SIGED_DOC` | ninguna |
| `ID_ADMINISTRADO` | F5 `ADMINISTRADO` | F2 `ADM` / nombre si existe | lookup en `MI_DIM_ADMINISTRADO` (`NOM-…`); `-1` si no resuelve |
| `ID_ORGANO` | F2 `COORD` (o `COD_UNIDAD` inyectado) | sigla final de `NUMERO_EXPEDIENTE` | lookup `MI_DIM_ORGANO_UNIDAD.SIGLA`; `-1` si no resuelve |
| `ID_OD` | F1 `COD_OD` (inyectado desde catálogo OD) | — | lookup `MI_DIM_OD`; `-1` si no aplica (filas F2/F4/F5) |
| `ID_FUENTE` | `FUENTE_ORIGEN` → código | catálogo `MI_DIM_FUENTE_REGISTRO` | lookup por `CODIGO`; alias `LAM_OD`/`OD_EXCEL` → `OD_SHEETS` |
| `ID_TIEMPO_FIRMA` | `F_FIRMA_RES_MC` | `MI_DIM_TIEMPO` | `AAAAMMDD`; `-1` si no hay fecha |
| `ID_MATERIA` | catálogo semilla | — | lookup en `MI_DIM_MATERIA_SUBSECTOR`; `-1` si no resuelve |
| `ID_ESTADO_RESOLUCION` | F5 `ESTADO_RESOLUCION` | — | homologar contra `MI_DIM_ESTADO` (`TIPO_ESTADO='RESOLUCION'`) |
| `ID_ESTADO_MULTA` | F1/F2 `ESTADO_MC` | F5 `ESTADO_MULTA`; F4 `FG_ESTADOMULTA` (conciliar) | homologar contra `MI_DIM_ESTADO` (`TIPO_ESTADO='MULTA'`) |
| `ID_ESTADO_PAGO` | F2 `ESTADO_PAGO_MC` | — | homologar contra `MI_DIM_ESTADO` (`TIPO_ESTADO='PAGO'`) |
| `ID_UIT` | resuelto por año | `YEAR(F_FIRMA_RES_MC)` → `YEAR(FECHA_EMISION F5)` → `YEAR(FN_MC)` | lookup en `MI_DIM_PARAMETRO_UIT` |
| `F_NOTIF_DCG` | F1/F2 `FN_MC` | — | parseo a `DATE` |
| `F_VENC_DCG` | F1/F2 `F_VENC_DCG` | — | parseo a `DATE` |
| `F_RPTA_ADM` | F1/F2 `F_RPTA_ADM` | — | parseo a `DATE` |
| `F_INIC_ANALISIS` | F1/F2 `F_INIC_ANALISIS` | — | parseo a `DATE` |
| `F_FIN_ANALISIS` | F1/F2 `F_FIN_ANALISIS` | — | parseo a `DATE` |
| `F_FIRMA_RES_MC` | F1/F2 `F_FIRMA_RES_MC` | — | parseo a `DATE` |
| `F_NOTIF_RES_MC` | F1/F2 `FN_RES_MC` | — | parseo a `DATE` |
| `F_VENC_MC` | F1/F2 `F_VENC_MC` | — | parseo a `DATE` |
| `F_VERIF_POST_MC` | F1/F2 `F_VERIF_POST_MC` | F4 `FE_F_VERIF_POST_MC` (conciliar) | parseo a `DATE` |
| `F_PAGO` | no existe columna explícita en ninguna fuente | inferir de `ESTADO_MC='PAGADO'` + fecha de última modificación (F4 `FE_FECHA_MODIFICACION`) si aplica | **dato derivado, documentar como tal**; puede quedar `NULL` |
| `F_REMISION_MEMO` | F1/F2 `F_REMIS` | — | parseo a `DATE` |
| `PRESENTO_DESCARGOS` | F1/F2 `PRESENT_DCG_ADM` | — | `SI`→`S`, `NO`→`N`, variantes homologadas |
| `AMERITA_MC` | F1/F2 `AMERIT_MC` | — | `SI`→`S`, `NO`→`N` |
| `REQUIERE_VERIF_CAMPO` | F1/F2 `REQ_VERIF_CAMPO` | — | `SI`→`S`, `NO`→`N` |
| `MEDIDA_ADMINISTRATIVA` | F5 `MEDIDA_ADMINISTRATIVA` | — | quitar saltos de línea embebidos (H3) |
| `MEMO_EF` | F1/F2 `MEMO_EF` | — | ninguna |
| `SIGED` | F1/F2 `SIGED` | — | ninguna |
| `DOC_VERIF_MC` | F1/F2 `DOC_VERIF_MC` | F4 `TX_DOC_VERIF_MC` | ninguna |
| `MONTO_UIT` | F1/F2 `MULTA_UIT` | F4 `NU_MONTOMCUIT`; F5 `MONTO_MULTA` (conciliar, regla R05) | ninguna |
| `VALOR_UIT_APLICADO` | `MI_DIM_PARAMETRO_UIT.VALOR_UIT` del año resuelto en `ID_UIT` | — | lookup (catálogo MEF en Python) |
| `MONTO_S` | F1/F2 `MULTA_S` (puede venir `#N/A` / token de error) | F4 `NU_MONTOMCS` | tokens de error → `NULL` |
| `MONTO_S_CALC` | calculado | `MONTO_UIT × VALOR_UIT_APLICADO` | fuente de verdad cuando `MONTO_S` es `NULL` o difiere (regla R05) |
| `MONTO_MULTA_REC` | F5 `MONTO_MULTA_REC` | — | ninguna |
| `MONTO_MULTA_TFA` | F5 `MONTO_MULTA_TFA` | — | ninguna |
| `DIAS_NOTIF_A_RESPUESTA` | calculado | `F_RPTA_ADM − F_NOTIF_DCG` | — |
| `DIAS_ANALISIS` | calculado | `F_FIN_ANALISIS − F_INIC_ANALISIS` | — |
| `DIAS_NOTIF_A_FIRMA` | calculado | `F_FIRMA_RES_MC − F_NOTIF_DCG` | — |
| `DIAS_FIRMA_A_VENC` | calculado | `F_VENC_MC − F_FIRMA_RES_MC` | — |
| `DIAS_VENC_A_PAGO` | calculado | `F_PAGO − F_VENC_MC` (si `F_PAGO` existe) | — |
| `DIAS_RESOL_A_VERIF` | calculado | `F_VERIF_POST_MC − F_FIRMA_RES_MC` | — |
| `FLAG_PRESENTO_DCG` | calculado | `1` si `PRESENTO_DESCARGOS='S'` | — |
| `FLAG_AMERITA_MC` | calculado | `1` si `AMERITA_MC='S'` | — |
| `FLAG_PAGADA` | calculado | `1` si `ID_ESTADO_PAGO` homologa a grupo `CUMPLIDO` / `PAGADO` | — |
| `FLAG_EJECUCION_FORZOSA` | calculado | `1` si `MEMO_EF` no es nulo | — |
| `FLAG_CUMPLIO_VERIF` | calculado | `1` si `F_VERIF_POST_MC` no es nulo | — |
| `FECHA_CARGA` | asignado por el proceso | timestamp al construir el hecho | — |

---

## 2. `MI_FACT_INFORME_SUPERVISION`

**Fuera de alcance.** El DW es solo Multas. F3 (`CSEP_INFORMES_VIEW`) no se extrae ni se modela.

---

## 3. `MI_DET_ETAPA_MC`

| Columna destino | Origen (F2-ET `2) Etapas` en sheets CSEP) | Transformación |
|---|---|---|
| `ID_MC` | resuelto por amarre `COD_PROY_MC` | lookup contra `MI_FACT_MULTA_COERCITIVA.COD_PROY_MC`; `NULL` si aún no existe el hecho padre |
| `COD_PROY_MC` | `COD_PROY_MC` | ninguna |
| `NRO_ETAPA` | `NRO_ETAPA_MC` | ninguna |
| `ACCION` | `ACCION_MC` | ninguna (`ELABORACION`/`REVISION`/`CALCULO`/`FIRMA`) |
| `PERFIL_ENCARGADO` | `PERF_ENCARG_MC` | ninguna |
| `ENCARGADO` | `ENCARGADO_MC` | ninguna |
| `F_ASIGNACION` | `F_ASIG_MC` | parseo a `DATE` |
| `F_ENTREGA_DEV` | `F_ENT_DEV_MC` | parseo a `DATE` |
| `ESTADO_ETAPA` | `EST_ETAPA_MC` | ninguna (`TERMINADO`/`PENDIENTE`) |
| `CONFORMIDAD` | `CONFORMIDAD_MC` | ninguna |
| `DIAS_ELABORACION` | `T_ELAB_MC` | validar/recalcular con `MI_DIM_TIEMPO.ES_DIA_HABIL` si se requiere precisión |
| `ID_FUENTE` | asignado | lookup `CAGR` en `MI_DIM_FUENTE_REGISTRO` |
| `FECHA_CARGA` | asignado | timestamp al insertar |

---

## 4. Dimensiones

### `MI_DIM_ADMINISTRADO`

| Columna | Origen | Transformación |
|---|---|---|
| `COD_ADMINISTRADO` | F5 `ADMINISTRADO` (nombre) | clave natural `NOM-<razón social normalizada>` |
| `RAZON_SOCIAL` | F5 `ADMINISTRADO` | conservar tal cual |
| `RAZON_SOCIAL_NORM` | calculado | mayúsculas, sin dobles espacios, sin tildes opcional |

### `MI_DIM_ORGANO_UNIDAD`

| Columna | Origen | Transformación |
|---|---|---|
| `SIGLA` | F2 `COORD` / `COD_UNIDAD` / catálogo `f2_csep_sheets.json` | **solo** las 10 unidades CSEP activas (+ ND); no se agregan siglas de expediente a la dim |
| `NOMBRE` | igual a `SIGLA` | código corto (compat) |
| `DESCRIPCION` | `f2_csep_sheets.json` → `nombre` | nombre largo (ej. `CMIN` → `Minería`); si no hay match → `SIGLA` |
| `TIPO` | inferido de la sigla | CSEP (`C*`/`UF*`) → `COORDINACION` |

Lookup en el hecho: `COORD` → `COD_UNIDAD` → último token de `NUMERO_EXPEDIENTE` **solo si** es una SIGLA CSEP conocida; si no → `ID_ORGANO = -1`.

### `MI_DIM_OD`

| Columna | Origen |
|---|---|
| `COD_OD` / `NOMBRE` / `TIPO` / `ORDEN` | catálogo F1 (`f1_ods_sheets.json` / semilla `ODS_OEFA`); `ID_OD` en el hecho desde `COD_OD` de STG F1 |

### `MI_DIM_FUENTE_REGISTRO`

| Columna | Origen |
|---|---|
| `CODIGO` / `NOMBRE` / `FAMILIA_TDR` / `DESCRIPCION` | semillas en `constantes.SEMILLAS_FUENTE_REGISTRO` (`OD_SHEETS`, `CAGR`, `GAPPS`, `SISUD_VW`, legacy `OD_EXCEL`) |
| `ID_FUENTE` en hecho/etapas | lookup por `CODIGO` (= valor de `FUENTE_ORIGEN` normalizado) |

### `MI_DIM_TIEMPO` (role-playing en el hecho)

| Columna hecho | Uso |
|---|---|
| `ID_TIEMPO_FIRMA` | Día de `F_FIRMA_RES_MC` para cortes Q/año sin `EXTRACT` |

### `MI_DIM_MATERIA_SUBSECTOR`

| Columna | Origen |
|---|---|
| `NOMBRE` | catálogo semilla (Hidrocarburos, Minería, etc.) |

### `MI_DIM_ESTADO`

| `TIPO_ESTADO` | Fuentes que homologan a este tipo |
|---|---|
| `RESOLUCION` | F5 `ESTADO_RESOLUCION` |
| `MULTA` | F1/F2 `ESTADO_MC`; F5 `ESTADO_MULTA`; F4 `FG_ESTADOMULTA` |
| `PAGO` | F2 `ESTADO_PAGO_MC` |
| `ETAPA` | F2-ET `EST_ETAPA_MC` |
| `DESCARGOS` | F1/F2 `PRESENT_DCG_ADM`, F2 `EST_DCG` |

Las semillas en `ddl/01_dimensiones.sql` / código Python cubren valores observados; ampliar con CSEP si aparecen nuevos códigos.

### `MI_DIM_PARAMETRO_UIT`

| Columna | Origen |
|---|---|
| `ANIO` / `VALOR_UIT` | catálogo oficial MEF sembrado en Python (`UIT_MEF`); no se stagea `M_PARAMETROS` desde Sheets |

### `MI_DIM_TIEMPO`

Generada por script de calendario (no proviene de ninguna fuente). `ES_FERIADO` queda en `0` salvo materialización futura de feriados (históricamente `M_FERIADO` en plantillas Excel, no cargado por el ETL F1 vigente).

---

## 5. Calidad y amarre

### `MI_DQ_HALLAZGO`

Cada regla (R01–R05, ver `PROPUESTA_ADAPTADA_ETL.md` sección 4) genera una fila por cada
registro no conforme, con `REGISTRO_ID` igual a la clave natural del registro afectado
(`COD_MA`, `CUM+CAM`, o `NUMERO_EXPEDIENTE` según el caso).

### `MI_QA_AMARRE` / `MI_QA_AMARRE_DETALLE`

| Tabla | Contenido |
|---|---|
| `MI_QA_AMARRE` | Resumen por puente H9 (`PCT_MATCH_IZQ`, etc.); alimenta K5 |
| `MI_QA_AMARRE_DETALLE` | Claves sin match (`SOLO_IZQ` / `SOLO_DER`, `CLAVE`, `MOTIVO`) |

### Vistas de reporte

| Vista | Universo (`CODIGO`) |
|---|---|
| `VW_MC_CSEP` | `CAGR` |
| `VW_MC_OD` | `OD_SHEETS` |
| `VW_MC_SISUD` | `SISUD_VW` |
| `VW_MC_GAPPS` | `GAPPS` |

---

**Nota de mantenimiento:** el origen operativo de F1/F2 es Google Sheets (catálogos JSON + SA).
Si CSEP entrega catálogos auxiliares materializados (feriados, UIT, DIC), este anexo no cambia
de estructura; solo cambia el origen de `MI_DIM_TIEMPO.ES_FERIADO`, dims de territorio/materia
(si aplica UBIGEO) y, opcionalmente, `MI_DIM_PARAMETRO_UIT` frente al MEF.
