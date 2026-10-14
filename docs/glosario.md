# Glosario

Nombres cortos que usa este ETL. Diseño vigente: [`modelo-kimball.md`](modelo-kimball.md) · Manual fact: [`lineamientos/extra/manual-como-se-arma-el-fact.md`](lineamientos/extra/manual-como-se-arma-el-fact.md).  

El `_` al final (`STG_`, `DW_M_`) significa “todas las tablas de esa capa”.

## Capas (prefijos vigentes)

| Término | Qué es, en una frase |
|---|---|
| **STG_** | Staging en H2: copia 1:1 de cada fuente activa (F1/F2/F5). Sin UNION, sin QA. |
| **DW_M_** | Modelo dimensional en Oracle BD_CURSOR (dims, hechos, DQ, indicadores). |
| **DW_M_FACT_MC_*** | Facts de **evidencia** en memoria (sede central / OD / SISUD). No se publican a Oracle. |
| **DW_M_FACT_MULTA_COERCITIVA** | Fact de negocio: planillas sede central + OD, lookup SISUD (CUM/CAM). |
| **VW_MC_*** | Vistas legado (no son el entregable actual). El tablero lee el fact + dims. |

## Legado (fase 1 medallion — ya no es el entregable)

| Término | Qué era |
|---|---|
| **INT_** / **QA_** / **FCT_** | Capas medallion antiguas; sustituidas por `DW_M_*` + cuarentena blanda. |

## Tablas de control / calidad

| Término | Qué es, en una frase |
|---|---|
| **DW_M_DQ_HALLAZGO** | Defectos R01–R05 (cuarentena blanda; filas no se eliminan). |
| **DW_M_QA_AMARRE** (+ `_DETALLE`) | Amarre H9 entre fuentes; puente vigente `RES_MONTO_Sheets_vs_SISUD`. |
| **FG_CONFORME** | Marca S/N de calidad en intermedios / hechos. |
| **ID_CORRIDA** / **QA_CORRIDA** | Legado fase 1; el lineamiento usa `ID_CARGA` / tablas `DW_M_*`. |

## Dónde vive

| Término | Qué es, en una frase |
|---|---|
| **H2** | Workbench de la corrida (puerto 9092): solo `STG_*`. No es el entregable. |
| **BD_CURSOR** | Oracle destino (`DB_ORA_DW_*`): `DW_M_*` + `VW_MC_*`. |
| **LECTURAS** | DataFrames que lee Python desde H2 (`GS1`, `GS2`, `ORA`, `ETAPAS`…). |
| **RESULTADO** | Resumen de corrida en memoria/log. |

## Fuentes (nombres cortos)

**CSEP** administra todas las fuentes. No es una base: las planillas son **sede central** (10) y **OD** (31). SISUD es lookup.

| Término | Qué es, en una frase |
|---|---|
| **CSEP** | Área que administra sede central, OD y SISUD. No es `ID_FUENTE`. |
| **Sede central** | 10 Google Sheets de coordinaciones/unidades (CMIN, CRES, …). Código interno F2 / `CAGR`. |
| **OD** | 31 Google Sheets de oficinas desconcentradas. Código interno F1 / `OD_SHEETS`. |
| **F1 / GS2** | Planillas OD → filas del fact con `ID_FUENTE` = OD. |
| **F2 / GS1** | Planillas sede central (+ etapas) → filas del fact con `ID_FUENTE` = Sede central. |
| **F5 / SISUD** | Vista Oracle `VW_MULTA_COERCITIVA` (CUM/CAM al enrich). No agrega filas al fact. |
| **F3** | Informes SISUD — **fuera de alcance**. |
| **F4 / GAPP** | MySQL gapps — AUD + filas al fact (`ID_FUENTE=GAPPS`), sin lookup SISUD. |
| **MC** | Multa coercitiva. |
| **Evidencia** | Fact 1:1 por fuente, en memoria, sin merge. |
| **Enriquecida** | Negocio sede central + OD + GAPPS; CUM/CAM SISUD solo sobre planillas. |
