# Anexo — Mapeo Campo a Campo (Fuentes → Modelo Dimensional)

> Complementa `PROPUESTA_ADAPTADA_ETL.md` y los DDL en `ddl/`. Este anexo cierra la brecha
> entre "qué tablas construir" y "de dónde sale exactamente cada columna", para que la capa
> lógica (Python) se pueda escribir sin ambigüedad.
>
> Basado en el inventario campo por campo verificado con datos reales de las 5 fuentes
> (`propuesta_5/docs/dwh/01-fuentes-de-datos.md`), adaptado a los nombres de columna
> definidos en `ddl/01_dimensiones.sql` y `ddl/02_hechos.sql`.

---

## 0. Fuentes y su identificador corto

| ID | Fuente | Objeto | Columnas |
|---|---|---|---|
| F1 | Excel OD Lambayeque | hoja `5) Multas Coercitivas` | 32 |
| F2 | Excel CAGR | hoja `1) Multas coercitivas` | 48 (incluye las 32 de F1 + 16 propias) |
| F2-ET | Excel CAGR | hoja `2) Etapas` | 12 |
| F3 | Oracle SISUD | `CSEP_INFORMES_VIEW` | 56 |
| F4 | MySQL gapps | `T_MVC_MULTACOERCITIVA_MC` | 17 |
| F5 | Oracle SISUD | `VW_MULTA_COERCITIVA` | 13 |

**Regla general de prioridad cuando dos fuentes traen el mismo dato:** se prioriza la fuente
más confiable/reciente y se conserva el resto como respaldo con su `FUENTE_REGISTRO` visible;
nunca se descarta el dato divergente, se registra como hallazgo de calidad (R... según regla
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
| `ID_INFORME` | resuelto por amarre | `NUMERO_EXPEDIENTE` ↔ F3 `TXCUC`/`TXNUMEXP` | FK a `MI_FACT_INFORME_SUPERVISION`; `NULL`/`-1` si no amarra (H9) |
| `ID_ADMINISTRADO` | resuelto vía informe amarrado (F3 `IDADMINISTRADO`) | F5 `ADMINISTRADO` (si no hay amarre) | lookup en `MI_DIM_ADMINISTRADO`; `-1` si no resuelve |
| `ID_ORGANO` | F2 `COORD` | sigla final de `NUMERO_EXPEDIENTE` (ej. `...-DSIS-CRES`) | lookup en `MI_DIM_ORGANO_UNIDAD`; `-1` si no resuelve |
| `ID_MATERIA` | vía informe amarrado (F3 `TXSUBSECTOR_UND`) | — | lookup en `MI_DIM_MATERIA_SUBSECTOR`; `-1` si no resuelve |
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
| `VALOR_UIT_APLICADO` | `MI_DIM_PARAMETRO_UIT.VALOR_UIT` del año resuelto en `ID_UIT` | — | lookup |
| `MONTO_S` | F1/F2 `MULTA_S` (puede venir `#N/A` en F2, H5) | F4 `NU_MONTOMCS` | tokens de error → `NULL` |
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
| `FLAG_PAGADA` | calculado | `1` si `ID_ESTADO_PAGO` homologa a grupo `CUMPLIDO` | — |
| `FLAG_EJECUCION_FORZOSA` | calculado | `1` si `MEMO_EF` no es nulo | — |
| `FLAG_CUMPLIO_VERIF` | calculado | `1` si `F_VERIF_POST_MC` no es nulo y resultado registrado como conforme | — |
| `FUENTE_REGISTRO` | asignado por el proceso | `'LAM_OD'` (fila viene solo de F1), `'CAGR'` (viene de F2), complementado con `'GAPPS'`/`'SISUD_VW'` si F4/F5 aportaron datos de conciliación | — |
| `FECHA_CARGA` | asignado por el proceso | `SYSDATE` al insertar | — |

---

## 2. `MI_FACT_INFORME_SUPERVISION`

| Columna destino | Origen (F3 `CSEP_INFORMES_VIEW`) | Transformación |
|---|---|---|
| `IDACTIVIDAD` | `IDACTIVIDAD` | ninguna |
| `TXCUC` | `TXCUC` | ninguna (clave de amarre con `NUMERO_EXPEDIENTE`) |
| `TXNUMEXP` | `TXNUMEXP` | ninguna (frecuentemente nulo en la muestra) |
| `TXINFORME` | `TXINFORME` | ninguna |
| `ID_ADMINISTRADO` | `IDADMINISTRADO` / `TXADMINISTRADO` | lookup/alta en `MI_DIM_ADMINISTRADO` |
| `ID_ORGANO` | `TXCOORDINACION` | lookup/alta en `MI_DIM_ORGANO_UNIDAD` |
| `ID_MATERIA` | `TXSUBSECTOR_UND` | lookup/alta en `MI_DIM_MATERIA_SUBSECTOR` |
| `ID_ESTADO_INFORME` | `TXESTADO` (o `TXPRY_ESTADO` si aplica al ciclo del informe) | homologar contra `MI_DIM_ESTADO` (`TIPO_ESTADO='INFORME'`) |
| `TIPO_SUPERVISION` | `TXTIPSUP` | ninguna (`ESPECIAL`/`REGULAR`) |
| `FUENTE_PROGRAMACION` | `TXFUENTE` | ninguna (`PLANEFA`/`OTRA`) |
| `NIVEL_REVISION` | `TXNIVELES_REVISION` | ninguna (texto con fechas embebidas, se conserva tal cual) |
| `F_INICIO` | `FEINICIO` | parsear `TIMESTAMP'...'` de Oracle a `DATE` |
| `F_FIN` | `FEFIN` | ídem |
| `F_INFORME_ESPERADO` | `FEINFORME_ESPERADO` | ídem |
| `F_INFORME` | `FEINFORME` | ídem |
| `F_REG_INFORME` | `FEREG_INFORME` | ídem |
| `DIAS_SUPERVISION` | calculado | `F_FIN − F_INICIO` |
| `DIAS_ELAB_INFORME` | calculado | `F_INFORME − F_FIN` |
| `FLAG_INFORME_OPORTUNO` | calculado | `1` si `F_INFORME ≤ F_INFORME_ESPERADO` |
| `FLAG_DERIVADO` | calculado | `1` si `TX_DOC_DERIVACION` no es nulo |
| `FUENTE_REGISTRO` | asignado | `'SISUD_INF'` constante |
| `FECHA_CARGA` | asignado | `SYSDATE` al insertar |

**Campos de F3 que NO suben al datamart** (permanecen solo en la capa de integración/H2 por
tratarse de datos personales, según gobierno de datos): `TXNOMBRE_RESP_COMISION`,
`TXNOMBRE_RESP_MONITOREO`, `TXNOMBRE_ANAL_LEGAL`, `TXNOMBRE_JEFE_ACTIVIDAD`.

---

## 3. `MI_DET_ETAPA_MC`

| Columna destino | Origen (F2-ET `2) Etapas`) | Transformación |
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
| `FUENTE_REGISTRO` | asignado | `'CAGR'` constante |
| `FECHA_CARGA` | asignado | `SYSDATE` al insertar |

---

## 4. Dimensiones

### `MI_DIM_ADMINISTRADO`

| Columna | Origen | Transformación |
|---|---|---|
| `COD_ADMINISTRADO` | F3 `IDADMINISTRADO` (`ADM#####`) | si la fuente solo trae nombre (F1/F2/F5 `ADMINISTRADO`), usar `NOM-<razón social normalizada>` como clave natural |
| `RAZON_SOCIAL` | F3 `TXADMINISTRADO` / F5 `ADMINISTRADO` | conservar tal cual |
| `RAZON_SOCIAL_NORM` | calculado | mayúsculas, sin dobles espacios, sin tildes opcional |

### `MI_DIM_ORGANO_UNIDAD`

| Columna | Origen | Transformación |
|---|---|---|
| `SIGLA` | F3 `TXCOORDINACION`; F2 `COORD` | si no viene explícita, extraer de la sigla final de `NUMERO_EXPEDIENTE` (ej. `0209-2023-DSIS-CRES` → `DSIS-CRES`) |
| `NOMBRE` | igual a `SIGLA` si no hay nombre largo disponible | catálogo institucional a completar con CSEP |
| `TIPO` | inferido de la sigla | `DIRECCION`/`COORDINACION`/`ODES`/`OD` según catálogo (Fase 3) |

### `MI_DIM_MATERIA_SUBSECTOR`

| Columna | Origen |
|---|---|
| `NOMBRE` | F3 `TXSUBSECTOR_UND` |

### `MI_DIM_ESTADO`

| `TIPO_ESTADO` | Fuentes que homologan a este tipo |
|---|---|
| `RESOLUCION` | F5 `ESTADO_RESOLUCION` |
| `MULTA` | F1/F2 `ESTADO_MC`; F5 `ESTADO_MULTA`; F4 `FG_ESTADOMULTA` |
| `PAGO` | F2 `ESTADO_PAGO_MC` |
| `ETAPA` | F2-ET `EST_ETAPA_MC` |
| `DESCARGOS` | F1/F2 `PRESENT_DCG_ADM`, F2 `EST_DCG` |
| `INFORME` | F3 `TXESTADO`, `TXPRY_ESTADO` |

Las semillas ya cargadas en `ddl/01_dimensiones.sql` cubren los valores observados en el
diagnóstico; deben confirmarse/ampliarse con CSEP en la Fase 3 del plan de implementación.

### `MI_DIM_PARAMETRO_UIT`

| Columna | Origen |
|---|---|
| `ANIO` / `VALOR_UIT` | catálogo `M_PARAMETROS` (F1, actualmente roto por `IMPORTRANGE`, H6) + siembra oficial MEF ya incluida en el DDL como contingencia |

### `MI_DIM_TIEMPO`

Generada por script de calendario (no proviene de ninguna fuente); el flag `ES_FERIADO` se
alimenta del catálogo `M_FERIADO` (F1) una vez materializado (resuelve H6).

---

## 5. Tabla `MI_DQ_HALLAZGO` — qué la alimenta

Cada regla (R01-R05, ver `PROPUESTA_ADAPTADA_ETL.md` sección 4) genera una fila por cada
registro no conforme, con `REGISTRO_ID` igual a la clave natural del registro afectado
(`COD_MA`, `CUM+CAM`, o `NUMERO_EXPEDIENTE` según el caso) para poder rastrearlo hasta la
fuente original sin necesidad de una FK dura.

---

**Nota de mantenimiento:** si CSEP entrega una versión corregida de los catálogos rotos
(`M_FERIADO`, `M_UBIGEO`, `M_PARAMETROS`, `DIC_VARIABLES` — hallazgo H6), este anexo no
cambia de estructura; solo cambia el origen de `MI_DIM_TIEMPO.ES_FERIADO`, `MI_DIM_ORGANO_UNIDAD`/
`MI_DIM_MATERIA_SUBSECTOR` (si trae UBIGEO) y `MI_DIM_PARAMETRO_UIT` (si trae la UIT oficial vigente).
