# Inputs del ETL multa_informes_etl

> Fuente principal: `inputs.yaml` — generado automáticamente por `python/create_stg.py`.

## Resumen

El ETL consume **8 fuentes** de datos: 5 Excel locales, 2 Oracle y 1 MySQL.

---

## Fuentes Excel locales

### 1. `CAGR_ MA OEFA - 3) MULTAS COERCITIVAS.xlsx`

| # | Hoja | Tabla STG | Fila cabecera |
|---|------|-----------|---------------|
| F1 | `1) Multas coercitivas` | `STG_GS1_MULTAS_COERCITIVAS` | 3 |
| F2 | `2) Etapas` | `STG_GS1_ETAPAS` | 2 |
| F3 | `DIC_TABLAS` | `STG_GS1_DIC_TABLAS` | 1 |
| F4 | `DIC_VARIABLES` | `STG_GS1_DIC_VARIABLES` | 1 |

**Notas:**
- F1 contiene ~48 columnas de medidas coercitivas (CUM, CAM, montos, fechas, estados, etc.)
- F2 contiene etapas del proceso (aepercionado, seguimiento, etc.)
- F3 y F4 son diccionarios de datos/tablas

### 2. `MEDIDAS ADMINISTRATIVAS OD LAMBAYEQUE.xlsx`

| # | Hoja | Tabla STG | Fila cabecera |
|---|------|-----------|---------------|
| F5 | `5) Multas Coercitivas` | `STG_GS2_MULTAS_COERCITIVAS` | 3 |

---

## Fuentes de bases de datos

### Oracle (SISUD)

| # | Objeto | Tabla STG | Conexión |
|---|--------|-----------|----------|
| F6 | `SISUD.VW_MULTA_COERCITIVA` | `STG_ORA_VW_MULTA_COERCITIVA` | `oracle_sisud` |
| F7 | `SISUD.CSEP_INFORMES_VIEW` | `STG_ORA_CSEP_INFORMES` | `oracle_sisud` |

**Columnas clave de F6 (VW_MULTA_COERCITIVA):**
`NUMERO_EXPEDIENTE`, `ADMINISTRADO`, `RESOLUCION`, `FECHA_EMISION`, `NUMERO_REGISTRO`, `ESTADO_RESOLUCION`, `MEDIDA_ADMINISTRATIVA`, `CUM`, `CAM`, `MONTO_MULTA`, `MONTO_MULTA_REC`, `MONTO_MULTA_TFA`, `ESTADO_MULTA`

### MySQL (GAPPS)

| # | Objeto | Tabla STG | Conexión |
|---|--------|-----------|----------|
| F8 | `gappsdb.T_MVC_MULTACOERCITIVA_MC` | `STG_MYSQL_T_MVC_MULTACOERCITIVA` | `mysql` |

**Columnas clave de F8:**
`NU_MONTOMCUIT`, `NU_MONTOMCS`, `TX_IDCUM`, `TX_IDCAM`, `TX_RECORD_SEG`, `FE_F_VERIF_POST_MC`, `TX_DOC_VERIF_MC`, `TX_EXP_SIGED_DOC`, `FG_ESTADOMULTA`, `NU_IDVERIFICACIONMA`

---

## Flujo de datos

```
inputs.yaml → Hop STG_* → python/main.py → logica/ejecutar.py → DW Oracle (cargar_dw.py)
```

## Archivos de entrada físicos

| Archivo | Ruta relativa |
|---------|---------------|
| CAGR (Multas Coercitivas) | `input_excel/CAGR_ MA OEFA - 3) MULTAS COERCITIVAS.xlsx` |
| OD Lambayeque | `input_excel/MEDIDAS ADMINISTRATIVAS OD LAMBAYEQUE.xlsx` |
