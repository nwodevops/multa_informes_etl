# Status del proyecto — lineamientos Fases 1 a 7

Resumen alineado a [`lineamientos/PROPUESTA_ADAPTADA_ETL.md`](../lineamientos/PROPUESTA_ADAPTADA_ETL.md) (sección 6) y al diseño vigente.  
Rama de trabajo: `fase-1-lineamiento`.  
Manual del fact: [`../lineamientos/extra/manual-como-se-arma-el-fact.md`](../lineamientos/extra/manual-como-se-arma-el-fact.md).  
Guía modelo: [`../modelo-kimball.md`](../modelo-kimball.md).

---

## Vista en una corrida

```mermaid
flowchart TB
  subgraph fuentes [Fuentes activas]
    F1["F1 Sheets OD"]
    F2["F2 Sheets CSEP + etapas"]
    F5["F5 Oracle SISUD"]
  end

  subgraph hop [Apache Hop]
    WF["wf_main.hwf"]
    RESET["Reset H2"]
    STG_LOAD["pl_stage_* / stage_*_sheets → STG_*"]
  end

  subgraph h2 [H2 mem:csep — staging efímero]
    STG["STG_* tablas espejo"]
  end

  subgraph py [Python logica/dwh/]
    F2b["Fase 2–7: perfil … indicadores"]
    EV["3 facts evidencia<br/>DW_M_FACT_MC_CSEP / _OD / _SISUD"]
  end

  subgraph oracle [Oracle BD_CURSOR]
    LOAD["cargar_dw TRUNCATE+INSERT"]
    ENR["07_enrich_sheets_sisud.sql"]
    FACT["DW_M_FACT_MULTA_COERCITIVA"]
    VW["VW_MC_* + VW_MC_ENRIQUECIDA"]
  end

  fuentes --> WF
  WF --> RESET --> STG_LOAD --> STG
  STG --> F2b --> EV
  EV -->|"cargar_dw.py"| LOAD
  LOAD --> ENR --> FACT
  FACT --> VW
```

> **F3 OUT.** **F4 MySQL fuera de ingestión** (semilla `GAPPS` en dim fuente únicamente).

---

## Semáforo por fase del lineamiento

| Fase | Qué pide el lineamiento | Status | Evidencia en repo |
|:---:|---|:---:|---|
| **1** | Entorno Python: leer H2, conectar BD_CURSOR, invocado desde Hop | **Listo** | `python/main.py`, `leer_h2.py`, `cargar_dw.py`, `.venv`, `wf_main.hwf` |
| **2** | Perfilamiento + diccionario de las fuentes de multa; evidencia H1–H9 | **Implementado** | `logica/dwh/perfilamiento.py`, `diccionario.py` → `PROF_*`, `DICCIONARIO` |
| **3** | Homologación + dataframes intermedios tipificados (F1/F2/F5, sin merge a un solo fact) | **Implementado** | `homologacion.py`, `integracion.py` → `df_csep` / `df_od` / `df_sisud` / `DF_ETAPAS` |
| **4** | R01–R05, `DW_M_DQ_HALLAZGO`, % amarre H9 | **Implementado** | `calidad.py` |
| **5** | `DIM_*`, 3× `DW_M_FACT_MC_*`, `DW_M_DET_ETAPA_MC` en memoria | **Implementado** | `dimensional.py` |
| **6** | Carga TRUNCATE+INSERT + enrich 07 → `DW_M_FACT_MULTA_COERCITIVA` | **Implementado** | `python/io/cargar_dw.py`, `ddl/07_enrich_sheets_sisud.sql` |
| **7** | KPIs `DW_M_INDICADOR_RESULTADO` K1–K5 | **Implementado** | `logica/dwh/indicadores.py`, `ddl/04_indicadores.sql` |
| **8** | Power BI contra BD_CURSOR | **Fuera de alcance** | No se realizará en este repo |

---

## Flujo de datos hoy (Fases 2–7)

```mermaid
flowchart LR
  STG["STG_* H2"]
  P2["PROF_RESUMEN<br/>PROF_HALLAZGO<br/>DICCIONARIO"]
  P3["df_csep / df_od / df_sisud<br/>DF_ETAPAS"]
  P4["FG_CONFORME<br/>DW_M_DQ_HALLAZGO<br/>DW_M_QA_AMARRE*"]
  P5["DW_M_DIM_* / DW_M_FACT_MC_*"]
  P7["DW_M_INDICADOR_RESULTADO"]
  ORA["Oracle: evidencia + 07 enrich<br/>+ VW_MC_*"]

  STG --> P2 --> P3 --> P4 --> P5 --> P7 --> ORA
```

| Salida | Fase | Persiste en Oracle |
|---|---|---|
| `PROF_RESUMEN` / `PROF_HALLAZGO` / `DICCIONARIO` | 2 | No — memoria + log |
| Intermedios F1/F2/F5 + `DF_ETAPAS` | 3–4 | No (incluye `FG_CONFORME`) |
| `DW_M_DQ_HALLAZGO` | 4 | Sí |
| `DW_M_QA_AMARRE` / `DW_M_QA_AMARRE_DETALLE` | 4 | Sí |
| `DW_M_DIM_*` / `DW_M_FACT_MC_CSEP` / `_OD` / `_SISUD` / `DW_M_DET_ETAPA_MC` | 5–6 | Sí |
| `DW_M_FACT_MULTA_COERCITIVA` | 6 (SQL 07) | Sí — (CSEP∪OD) LEFT JOIN SISUD |
| `DW_M_INDICADOR_RESULTADO` | 7 | Sí |
| `VW_MC_CSEP` / `_OD` / `_SISUD` / `VW_MC_ENRIQUECIDA` | 6 | Sí (vistas) |
| `RESULTADO` | 2–7 | No — resumen de corrida |

---

## Tablas que se crean en cada motor

### H2 (`mem:csep`, puerto 9092) — **sí, en cada corrida**

Se recrean al inicio: `reset_and_create.sh` (DDL base) + `create_stg.py` (DDL staging) + Hop carga filas.

| Tabla | Origen | Quién crea el DDL | Quién carga filas |
|---|---|---|---|
| `DEMO_TABLA_EJEMPLO` | Smoke arquetipo | `h2/sql/01_schema.sql` | Insert fijo en DDL |
| `STG_GS1_CSEP_MULTAS` | F2 Google Sheets CSEP | `create_stg.py` | `pl_stage_csep_sheet.hpl` + `stage_csep_sheets.sh` |
| `STG_GS1_ETAPAS` | F2 Sheets CSEP etapas | `create_stg.py` | `stage_csep_sheets.sh` |
| `STG_GS2_OD_MULTAS` | F1 Google Sheets OD | `create_stg.py` | `pl_stage_od_sheet.hpl` + `stage_ods_sheets.sh` |
| `STG_GS1_DIC_TABLAS` | F2 hoja DIC_TABLAS (Excel legacy) | `create_stg.py` | `pl_stage_excel.hpl` |
| `STG_GS1_DIC_VARIABLES` | F2 hoja DIC_VARIABLES (Excel legacy) | `create_stg.py` | `pl_stage_excel.hpl` |
| `STG_ORA_VW_MULTA_COERCITIVA` | F5 Oracle SISUD | `create_stg.py` | `pl_stage_oracle.hpl` |

H2 es **efímero**: al parar el server o al Reset desaparece todo. No es entregable.

DDL staging generado: `h2/sql/02_stg.sql` (gitignore).

### Oracle REPOCSEP — **no, en el flujo actual**

Conexión legada (`metadata/rdbms/oracle_repocsep.json`, variables `DB_ORA_REPO_*`).  
**Ningún paso de `wf_main.hwf` escribe aquí** tras el refactor a lineamientos Fases 2–3.

### Oracle BD_CURSOR — **sí, Fases 6–7**

Destino del modelo dimensional (`DB_ORA_DW_*` / esquema `APP` local o `REPOCSEP` remote).  
`python/main.py` → `cargar_dw.py` hace wipe + DDL `01`–`06`, INSERT de evidencia/dims/QA/KPIs, y ejecuta enrich 07.

| Grupo | Tablas / vistas |
|---|---|
| Dimensiones | `DW_M_DIM_TIEMPO`, `DW_M_DIM_ADMINISTRADO`, `DW_M_DIM_ORGANO_UNIDAD` (~11), `DW_M_DIM_OD`, `DW_M_DIM_FUENTE_REGISTRO`, `DW_M_DIM_MATERIA_SUBSECTOR`, `DW_M_DIM_ESTADO`, `DW_M_DIM_PARAMETRO_UIT` |
| Hechos evidencia | `DW_M_FACT_MC_CSEP`, `DW_M_FACT_MC_OD`, `DW_M_FACT_MC_SISUD`, `DW_M_DET_ETAPA_MC` |
| Hecho negocio | `DW_M_FACT_MULTA_COERCITIVA` (SQL 07) |
| Calidad | `DW_M_DQ_HALLAZGO`, `DW_M_QA_AMARRE`, `DW_M_QA_AMARRE_DETALLE` |
| Indicadores | `DW_M_INDICADOR_RESULTADO` (K1–K5) |
| Vistas reporte | `VW_MC_CSEP`, `VW_MC_OD`, `VW_MC_SISUD`, `VW_MC_ENRIQUECIDA` |

```mermaid
flowchart LR
  subgraph h2now [H2 hoy]
    STG8["STG_* Sheets F1/F2 + F5"]
  end
  subgraph oranow [BD_CURSOR hoy]
    MI["DW_M_FACT_MC_* + enrich + VW_MC_*"]
  end
  STG8 --> MI
```

**Conteos de referencia:** CSEP~990 · OD~281 · SISUD~534 · enriquecido~1271.

---

## Fuentes y staging

| ID | Fuente | STG H2 | Carga Hop | Notas |
|---|---|---|:---:|---|
| F1 | Google Sheets OD | `STG_GS2_OD_MULTAS` | Sí | `stage_ods_sheets.sh` |
| F2 | Google Sheets CSEP | `STG_GS1_CSEP_MULTAS` / `ETAPAS` | Sí | `stage_csep_sheets.sh` |
| F2 | DIC (Excel legacy) | `STG_GS1_DIC_*` | Sí | `pl_stage_excel.hpl` |
| F3 | Informes SISUD | — | **No** | Fuera de alcance |
| F4 | MySQL GAPP | — | **No** | Fuera de ingestión; semilla `GAPPS` en dim |
| F5 | SISUD vista multas | `STG_ORA_VW_*` | Sí | credenciales Oracle |

---

## Qué se eliminó vs. enfoque anterior

| Antes (medallion TDR) | Ahora (lineamientos) |
|---|---|
| `logica/fase1/` → `INT_*`, `QA_*` | `logica/dwh/` → `PROF_*`, intermedios, `DW_M_*` |
| `output/fase1.xlsx` + carga `INT_*` Oracle | `cargar_dw.py` → evidencia + enrich + `VW_MC_*` |
| Modelo por universo sin cruce | 3 facts evidencia + enrich Sheet←SISUD; amarre H9 `RES_MONTO_Sheets_vs_SISUD` |

---

## Cómo verificar

```bash
./init.sh   # HARNESS OK
```

Detalle: [`../verification.md`](../verification.md) · modelo: [`../modelo-kimball.md`](../modelo-kimball.md).

---

## Alcance del lineamiento

Fases 1–7 + infra staging: **cerradas**. Fase 8 (Power BI): **fuera de alcance** — no se realizará.
