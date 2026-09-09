# Glosario

Nombres cortos que usa este ETL. Diseño vigente: [`modelo-kimball.md`](modelo-kimball.md) · Manual fact: [`lineamientos/extra/manual-como-se-arma-el-fact.md`](lineamientos/extra/manual-como-se-arma-el-fact.md).  

El `_` al final (`STG_`, `MI_`) significa “todas las tablas de esa capa”.

## Capas (prefijos vigentes)

| Término | Qué es, en una frase |
|---|---|
| **STG_** | Staging en H2: copia 1:1 de cada fuente activa (F1/F2/F5). Sin UNION, sin QA. |
| **MI_** | Modelo dimensional en Oracle BD_CURSOR (dims, hechos, DQ, indicadores). |
| **MI_FACT_MC_*** | Facts de **evidencia** por universo: CSEP / OD / SISUD (lo que se descargó). |
| **MI_FACT_MULTA_COERCITIVA** | Fact de negocio **enriquecido**: (CSEP∪OD) LEFT JOIN SISUD (SQL 07). |
| **VW_MC_*** | Vistas de reporte: evidencia (`_CSEP`/`_OD`/`_SISUD`) y `VW_MC_ENRIQUECIDA`. |

## Legado (fase 1 medallion — ya no es el entregable)

| Término | Qué era |
|---|---|
| **INT_** / **QA_** / **FCT_** | Capas medallion antiguas; sustituidas por `MI_*` + cuarentena blanda. |

## Tablas de control / calidad

| Término | Qué es, en una frase |
|---|---|
| **MI_DQ_HALLAZGO** | Defectos R01–R05 (cuarentena blanda; filas no se eliminan). |
| **MI_QA_AMARRE** (+ `_DETALLE`) | Amarre H9 entre fuentes; puente vigente `RES_MONTO_Sheets_vs_SISUD`. |
| **FG_CONFORME** | Marca S/N de calidad en intermedios / hechos. |
| **ID_CORRIDA** / **QA_CORRIDA** | Legado fase 1; el lineamiento usa `ID_CARGA` / tablas `MI_*`. |

## Dónde vive

| Término | Qué es, en una frase |
|---|---|
| **H2** | Workbench de la corrida (puerto 9092): solo `STG_*`. No es el entregable. |
| **BD_CURSOR** | Oracle destino (`DB_ORA_DW_*`): `MI_*` + `VW_MC_*`. |
| **LECTURAS** | DataFrames que lee Python desde H2 (`GS1`, `GS2`, `ORA`, `ETAPAS`…). |
| **RESULTADO** | Resumen de corrida en memoria/log. |

## Fuentes (nombres cortos)

| Término | Qué es, en una frase |
|---|---|
| **F1 / GS2** | Sheets OD (oficinas desconcentradas) → `MI_FACT_MC_OD`. |
| **F2 / GS1** | Sheets CSEP (+ etapas) → `MI_FACT_MC_CSEP`. |
| **F5 / SISUD** | Vista Oracle `VW_MULTA_COERCITIVA` → `MI_FACT_MC_SISUD` (+ CUM/CAM en enrich). |
| **F3** | Informes SISUD — **fuera de alcance**. |
| **F4 / GAPP** | MySQL histórico — **fuera de ingestión** (semilla `GAPPS` en dim). |
| **MC** | Multa coercitiva. |
| **Evidencia** | Fact 1:1 por fuente, sin merge. |
| **Enriquecida** | Negocio Sheet + CUM/CAM SISUD a la derecha. |
