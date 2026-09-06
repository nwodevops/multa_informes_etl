# Status del proyecto — lineamientos Fases 1 a 7

Resumen alineado a [`lineamientos/PROPUESTA_ADAPTADA_ETL.md`](../lineamientos/PROPUESTA_ADAPTADA_ETL.md) (sección 6).  
Rama de trabajo: `fase-1-lineamiento`.

---

## Vista en una corrida

```mermaid
flowchart TB
  subgraph fuentes [Fuentes de multa]
    F1["F1 Sheets OD 31"]
    F2["F2 Sheets CSEP 10 + DIC"]
    F4["F4 MySQL GAPP"]
    F5["F5 Oracle vista MC"]
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
    OUT["MI_* en memoria"]
  end

  subgraph oracle [Oracle BD_CURSOR]
    ORA["MI_* + VW_MC_*"]
  end

  fuentes --> WF
  WF --> RESET --> STG_LOAD --> STG
  STG --> F2b --> OUT
  OUT -->|"cargar_dw.py"| ORA
```

---

## Semáforo por fase del lineamiento

| Fase | Qué pide el lineamiento | Status | Evidencia en repo |
|:---:|---|:---:|---|
| **1** | Entorno Python: leer H2, conectar BD_CURSOR, invocado desde Hop | **Listo** | `python/main.py`, `leer_h2.py`, `cargar_dw.py`, `.venv`, `wf_main.hwf` |
| **2** | Perfilamiento + diccionario de las fuentes de multa; evidencia H1–H9 | **Implementado** | `logica/dwh/perfilamiento.py`, `diccionario.py` → `PROF_*`, `DICCIONARIO` |
| **3** | Homologación + dataframes integrados tipificados en memoria | **Implementado** | `homologacion.py`, `integracion.py` → `DF_MULTAS`, `DF_ETAPAS` |
| **4** | R01–R05, `MI_DQ_HALLAZGO`, % amarre H9 | **Implementado** | `calidad.py` |
| **5** | `DIM_*`, `FACT_*`, `MI_DET_ETAPA_MC` en memoria | **Implementado** | `dimensional.py` |
| **6** | Carga TRUNCATE+INSERT a BD_CURSOR | **Implementado** | `python/io/cargar_dw.py` |
| **7** | KPIs `MI_INDICADOR_RESULTADO` K1–K5 | **Implementado** | `logica/dwh/indicadores.py`, `ddl/04_indicadores.sql` |
| **8** | Power BI contra BD_CURSOR | **Fuera de alcance** | No se realizará en este repo |

---

## Flujo de datos hoy (Fases 2–7)

```mermaid
flowchart LR
  STG["STG_* H2"]
  P2["PROF_RESUMEN<br/>PROF_HALLAZGO<br/>DICCIONARIO"]
  P3["DF_MULTAS<br/>DF_ETAPAS"]
  P4["FG_CONFORME<br/>MI_DQ_HALLAZGO<br/>MI_QA_AMARRE*"]
  P5["MI_DIM_* / MI_FACT_*"]
  P7["MI_INDICADOR_RESULTADO"]
  ORA["Oracle BD_CURSOR<br/>+ VW_MC_*"]

  STG --> P2 --> P3 --> P4 --> P5 --> P7 --> ORA
```

| Salida | Fase | Persiste en Oracle |
|---|---|---|
| `PROF_RESUMEN` / `PROF_HALLAZGO` / `DICCIONARIO` | 2 | No — memoria + log |
| `DF_MULTAS` / `DF_ETAPAS` | 3–4 | No (incluye `FG_CONFORME`) |
| `MI_DQ_HALLAZGO` | 4 | Sí |
| `MI_QA_AMARRE` / `MI_QA_AMARRE_DETALLE` | 4 | Sí |
| `MI_DIM_*` / `MI_FACT_*` / `MI_DET_ETAPA_MC` | 5–6 | Sí |
| `MI_INDICADOR_RESULTADO` | 7 | Sí |
| `VW_MC_*` | 6 | Sí (vistas) |
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
| `STG_GS2_OD_MULTAS` | F1 31 Google Sheets OD | `create_stg.py` | `pl_stage_od_sheet.hpl` + `stage_ods_sheets.sh` |
| `STG_GS1_DIC_TABLAS` | F2 hoja DIC_TABLAS (Excel legacy) | `create_stg.py` | `pl_stage_excel.hpl` |
| `STG_GS1_DIC_VARIABLES` | F2 hoja DIC_VARIABLES (Excel legacy) | `create_stg.py` | `pl_stage_excel.hpl` |
| `STG_ORA_VW_MULTA_COERCITIVA` | F5 Oracle SISUD | `create_stg.py` | `pl_stage_oracle.hpl` |
| `STG_MYSQL_T_MVC_MULTACOERCITIVA` | F4 MySQL GAPP | `create_stg.py` | `pl_stage_mysql.hpl` |

H2 es **efímero**: al parar el server o al Reset desaparece todo. No es entregable.

DDL staging generado: `h2/sql/02_stg.sql` (gitignore).

### Oracle REPOCSEP — **no, en el flujo actual**

Conexión legada (`metadata/rdbms/oracle_repocsep.json`, variables `DB_ORA_REPO_*`).  
**Ningún paso de `wf_main.hwf` escribe aquí** tras el refactor a lineamientos Fases 2–3.

### Oracle BD_CURSOR — **sí, Fases 6–7**

Destino del modelo dimensional (`DB_ORA_DW_*` / esquema `APP` local o `REPOCSEP` remote).  
`python/main.py` → `cargar_dw.py` aplica DDL si falta y hace TRUNCATE+INSERT.

| Grupo | Tablas / vistas |
|---|---|
| Dimensiones | `MI_DIM_TIEMPO`, `MI_DIM_ADMINISTRADO`, `MI_DIM_ORGANO_UNIDAD` (~11), `MI_DIM_OD`, `MI_DIM_FUENTE_REGISTRO`, `MI_DIM_MATERIA_SUBSECTOR`, `MI_DIM_ESTADO`, `MI_DIM_PARAMETRO_UIT` |
| Hechos | `MI_FACT_MULTA_COERCITIVA` (`ID_FUENTE`, `ID_TIEMPO_FIRMA`), `MI_DET_ETAPA_MC` |
| Calidad | `MI_DQ_HALLAZGO`, `MI_QA_AMARRE`, `MI_QA_AMARRE_DETALLE` |
| Indicadores | `MI_INDICADOR_RESULTADO` (K1–K5) |
| Vistas reporte | `VW_MC_CSEP`, `VW_MC_OD`, `VW_MC_SISUD`, `VW_MC_GAPPS` |

```mermaid
flowchart LR
  subgraph h2now [H2 hoy]
    STG8["STG_* Sheets + F4/F5"]
  end
  subgraph oranow [BD_CURSOR hoy]
    MI["MI_* + VW_MC_*"]
  end
  STG8 --> MI
```

---

## Fuentes y staging

| ID | Fuente | STG H2 | Carga Hop | Notas |
|---|---|---|:---:|---|
| F1 | 31 Google Sheets OD | `STG_GS2_OD_MULTAS` | Sí | `stage_ods_sheets.sh` |
| F2 | 10 Google Sheets CSEP | `STG_GS1_CSEP_MULTAS` / `ETAPAS` | Sí | `stage_csep_sheets.sh` |
| F2 | DIC (Excel legacy) | `STG_GS1_DIC_*` | Sí | `pl_stage_excel.hpl` |
| F4 | MySQL GAPP | `STG_MYSQL_*` | Sí | credenciales MySQL |
| F5 | SISUD vista multas | `STG_ORA_VW_*` | Sí | credenciales Oracle |

---

## Qué se eliminó vs. enfoque anterior

| Antes (medallion TDR) | Ahora (lineamientos) |
|---|---|
| `logica/fase1/` → `INT_*`, `QA_*` | `logica/dwh/` → `PROF_*`, `DF_*`, `MI_*` |
| `output/fase1.xlsx` + carga `INT_*` Oracle | `cargar_dw.py` → `MI_*` + `VW_MC_*` en BD_CURSOR |
| Modelo por universo sin cruce | Integración F1+F2+F4+F5 con `ID_FUENTE` / amarre H9 medido |

---

## Cómo verificar

```bash
./init.sh   # HARNESS OK
```

Detalle: [`../verification.md`](../verification.md) · modelo: [`../adjuntos/guia-leer-modelo-dimensional.md`](../adjuntos/guia-leer-modelo-dimensional.md).

---

## Alcance del lineamiento

Fases 1–7 + infra staging: **cerradas**. Fase 8 (Power BI): **fuera de alcance** — no se realizará.
