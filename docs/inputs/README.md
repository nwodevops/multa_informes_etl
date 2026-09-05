# Inputs del ETL — alcance actual

Inventario de las fuentes que alimentan el pipeline **Hop → H2 (`STG_*`) → Python → Oracle DW (`MI_*`)**.

Este data warehouse es **solo Multas**. F3 (informes de supervisión / `CSEP_INFORMES_VIEW`) **no entra** en Hop, Kimball ni Oracle.

Manifiesto canónico: [`../../inputs.yaml`](../../inputs.yaml).  
Detalle campo a campo: [`../lineamientos/ANEXO_MAPEO_CAMPOS.md`](../lineamientos/ANEXO_MAPEO_CAMPOS.md) y [`../lineamientos/extra/fuentes_datos/01-fuentes-de-datos.md`](../lineamientos/extra/fuentes_datos/01-fuentes-de-datos.md).

---

## Alcance validado a la fecha

El modelo dimensional y los indicadores K1–K5 se construyen con:

| Universo | Fuente | Estado |
|---|---|---|
| **3 de 31 ODs** | F1 — familia Excel medidas administrativas | En uso: Lambayeque, Ica, Puno |
| **1 unidad (CAGR)** | F2 — Excel multas + etapas de una coordinación | En uso |
| **Conciliación multas** | F4 — MySQL GAPP | En uso |
| **Vista institucional multas** | F5 — Oracle SISUD | En uso |

**Fuera de alcance:** F3 — Oracle SISUD informes (`CSEP_INFORMES_VIEW`).

**Pendiente de incorporar** (semilla ya en `MI_DIM_OD`): las **28 oficinas restantes** del universo F1 y las **9 unidades restantes** CAGR. Ver convención más abajo.

---

## Flujo de inputs

```mermaid
flowchart LR
  subgraph excel [Excel local]
    F1["F1 familia OD"]
    F2["F2 CAGR"]
  end

  subgraph remoto [Bases fuente]
    F4["F4 GAPP multas"]
    F5["F5 SISUD vista MC"]
  end

  subgraph hop [Apache Hop]
    STG["STG_* en H2"]
  end

  subgraph py [Python]
    DF["DF_MULTAS · DF_ETAPAS"]
  end

  F1 --> STG
  F2 --> STG
  F4 --> STG
  F5 --> STG
  STG --> DF
```

---

## Resumen por fuente (F1, F2, F4, F5)

| ID | Nombre corto | Dominio | Pestaña Excel | Tipo | Origen | Tabla STG | Pipeline Hop | Uso en el DW |
|---|---|---|---|---|---|---|---|---|
| **F1** | Familia OD | **Multas** | `5) Multas Coercitivas` | Excel | `input_excel/medidas_administrativas/MEDIDAS ADMINISTRATIVAS OD {COD}.xlsx` | `STG_GS2_*` (una por OD activa) | `pl_stage_excel.hpl` | Hecho multa + `ID_OD` (`MI_DIM_OD`) |
| **F2** | CAGR multas | **Multas** | `1) Multas coercitivas` | Excel | `CAGR_ MA OEFA - 3) MULTAS COERCITIVAS.xlsx` | `STG_GS1_MULTAS_COERCITIVAS` | `pl_stage_excel.hpl` | Hecho multa (`ID_OD = -1`) |
| **F2-ET** | CAGR etapas | **Multas** (detalle) | `2) Etapas` | Excel | mismo archivo F2 | `STG_GS1_ETAPAS` | `pl_stage_excel.hpl` | Detalle `MI_DET_ETAPA_MC` |
| **F2-DIC** | Diccionario | Apoyo (no hecho) | `DIC_TABLAS` / `DIC_VARIABLES` | Excel | mismo archivo F2 | `STG_GS1_DIC_TABLAS`, `STG_GS1_DIC_VARIABLES` | `pl_stage_excel.hpl` | Perfilamiento y diccionario de campos |
| **F4** | GAPP multas | **Multas** (conciliación) | — | MySQL | `gappsdb.T_MVC_MULTACOERCITIVA_MC` | `STG_MYSQL_T_MVC_MULTACOERCITIVA` | `pl_stage_mysql.hpl` | Conciliación CUM/CAM (`ID_OD = -1`) |
| **F5** | SISUD vista MC | **Multas** | — | Oracle | `SISUD.VW_MULTA_COERCITIVA` | `STG_ORA_VW_MULTA_COERCITIVA` | `pl_stage_oracle.hpl` | Expediente, resolución (`ID_OD = -1`) |

Los IDs F4 y F5 se conservan (no se renumeran). F3 queda hueco a propósito.

`FUENTE_REGISTRO` de filas F1 = **`OD_EXCEL`**. El territorio (Ica, Lambayeque, …) va en **`MI_DIM_OD`**, no en la fuente.

---

## Archivos Excel F1 (`input_excel/medidas_administrativas/`)

Un libro por oficina. Hoja usada: `5) Multas Coercitivas`, `header_row: 3` (32 columnas idénticas).

| Archivo | `od` / `COD_OD` | STG | Lectura Python | Filas típicas |
|---|---|---|---|---|
| `MEDIDAS ADMINISTRATIVAS OD LAMBAYEQUE.xlsx` | `LAMBAYEQUE` | `STG_GS2_MULTAS_COERCITIVAS` | `GS2` | ~21 |
| `MEDIDAS ADMINISTRATIVAS OD ICA.xlsx` | `ICA` | `STG_GS2_ICA_MULTAS_COERCITIVAS` | `GS2_ICA` | ~28 |
| `MEDIDAS ADMINISTRATIVAS OD PUNO.xlsx` | `PUNO` | `STG_GS2_PUNO_MULTAS_COERCITIVAS` | `GS2_PUNO` | 0 (headers OK, sin datos) |

CAGR sigue en la raíz `input_excel/`.

`MI_DIM_OD` siembra **32 oficinas** (31 de la lista + CODE) + miembro ND. Catálogo: [`../../logica/dwh/catalogos.py`](../../logica/dwh/catalogos.py) (`ODS_OEFA`).

### Cómo añadir otra OD

1. Colocar `MEDIDAS ADMINISTRATIVAS OD {COD}.xlsx` en `input_excel/medidas_administrativas/` (`COD` = slug del catálogo: `AREQUIPA`, `LA_LIBERTAD`, `VRAEM`, …).
2. Entrada en [`../../inputs.yaml`](../../inputs.yaml) con `familia: f1_od`, `od: {COD}`, `stg_table: STG_GS2_{COD}_MULTAS_COERCITIVAS`, misma hoja/`header_row`.
3. `python/create_stg.py` + par ExcelInput/TableOutput en `pl_stage_excel.hpl`.
4. Clave en `LECTURAS` (`python/io/leer_h2.py`) y `F1_OD_LECTURAS` (`logica/dwh/constantes.py`); pasar el DataFrame en `ejecutar.py` → `gs2_ods`.

---

## Fuentes remotas (F4, F5)

No van en esta carpeta; se leen por JDBC en Hop según `project-config.json` / `environments/*.json`.

| ID | Conexión Hop | Esquema / base | Objeto |
|---|---|---|---|
| F4 | `mysql` | `gappsdb` | `T_MVC_MULTACOERCITIVA_MC` |
| F5 | `oracle_sisud` | `SISUD` | `VW_MULTA_COERCITIVA` |

Credenciales: [`../credenciales/`](../credenciales/) o `environments/local.json` / `remote.json` (no versionar secretos).

---

## Integración en Python

Tras el staging, `logica/dwh/` consume las lecturas H2 (`GS1`, `GS2`, `GS2_ICA`, `GS2_PUNO`, `ORA`, `MYSQL`, `ETAPAS`):

| Salida intermedia | Fuentes que integra |
|---|---|
| `DF_MULTAS` | F1 (3 ODs) + F2 + F4 + F5 (`FUENTE_ORIGEN`: `OD_EXCEL`, `CAGR`, `GAPPS`, `SISUD_VW`; `COD_OD` solo F1) |
| `DF_ETAPAS` | F2-ET |

Amarre H9: puentes entre fuentes de **multa** (COD_MA, CUM F4↔F5). No hay cruce multa↔informe.

Mapa en código: [`../../logica/dwh/constantes.py`](../../logica/dwh/constantes.py) (`STG_FUENTE`, `F1_OD_LECTURAS`, `FUENTE_REGISTRO`).

---

## Cómo añadir una región o unidad nueva

**OD Excel (F1):** ver «Cómo añadir otra OD» arriba. El `COD_OD` ya debe existir en `ODS_OEFA` / `MI_DIM_OD`.

**Unidad CAGR (F2):** 

1. Colocar el `.xlsx` en `input_excel/` (o ruta acordada con CSEP).
2. Registrar entrada en [`../../inputs.yaml`](../../inputs.yaml).
3. Ejecutar `python/create_stg.py` y cablear/ajustar `pl_stage_excel.hpl`.
4. Correr `wf_main` / `wf_main_win` y validar conteos `STG_*` → hechos `MI_*`.

Antes de procesar en masa las oficinas restantes, confirmar el modelo dimensional vigente (ver [`../adjuntos/modelo-kimball.md`](../adjuntos/modelo-kimball.md)).

---

## Referencias

- Antes / durante / staging: [`../antes-durante-fase1.md`](../antes-durante-fase1.md)
- Modelo Kimball e inputs: [`../adjuntos/modelo-kimball.md`](../adjuntos/modelo-kimball.md) §0
- Estado fases: [`../fase1-3/status.md`](../fase1-3/status.md)
