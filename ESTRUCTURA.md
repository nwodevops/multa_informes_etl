# Estructura del proyecto Apache Hop + H2

Estructura de `etl_cursor`, copia del arquetipo (original en `~/Documents/desarrollo/workspace_oefa/archetype`) portada a **Linux**.

```
etl_cursor/
├── project-config.json                  # Fuente única de variables (H2 + Oracle + MySQL)
├── switch-env.sh                        # Cambia entorno: ./switch-env.sh local|remote
├── switch-env.ps1                       # Referencia Windows (no se usa en Linux)
├── .gitignore                           # client_secret.json, *.xlsx, 02_stg.sql, .venv/
├── .venv/                               # GENERADO (gitignore): deps de python/requirements.txt
├── inputs.yaml                          # Manifiesto de fuentes STG (excel local CAGR + Lambayeque)
├── README.md                            # Cómo usar el arquetipo
├── AGENTS.md                            # Mapa corto para agentes (divulgación progresiva)
├── CHECKPOINTS.md                       # Criterios de "estado final correcto" por fase
├── feature_list.json                    # Alcance harness: una feature in_progress
├── init.sh                              # Verificación ejecutable (smoke ETL)
├── progress/
│   ├── current.md                       # Sesión activa (plan vivo)
│   └── history.md                       # Bitácora append-only
├── ESTRUCTURA.md                        # Este documento
├── .agents/skills/
│   ├── hop-python-etl/                  # Arquetipo Hop + H2 STG + Python
│   ├── phased-dwh-lineamiento/        # Fases 2–7: perfil → indicadores
│   ├── auditable-soft-quarantine/     # Cuarentena blanda, DQ, amarre H9
│   └── oracle-cargar-dw/              # Carga TRUNCATE+INSERT Oracle
├── docs/
│   ├── TDR REQ 3629-2026.pdf            # Requerimiento del servicio
│   ├── arquitectura.md                  # Diagramas: vista general y capa de lógica
│   ├── verification.md                  # Cómo demostrar que funciona (init.sh + manual)
│   └── harness/
│       ├── workflow.md                  # Roles líder / implementador / revisor
│       └── platform.md                  # Hop, H2, variables (detalle desde AGENTS.md)
│
├── environments/                        # Plantillas de variables por entorno
│   ├── local.json                       #   Entorno local/oficina (completar Oracle/MySQL)
│   └── remote.json                      #   Entorno remoto/casa (completar Oracle/MySQL)
│
├── h2/                                  # Infra H2 in-memory (reutilizada de etl_diego/h2)
│   ├── lib/
│   │   └── h2-2.4.240.jar               #   Driver/Server H2
│   ├── scripts/
│   │   ├── start_h2.sh                  #   Levanta H2 TCP+WEB en puerto 9092 (nohup)
│   │   ├── stop_h2.sh                   #   Mata procesos org.h2.tools.Server
│   │   ├── reset_and_create.sh          #   stop + start + DDL (00_reset.sql + 01_schema.sql)
│   │   └── *.bat                        #   Referencia Windows (no se usan en Linux)
│   └── sql/
│       ├── 00_reset.sql                 #   DROP ALL OBJECTS (limpia mem:csep)
│       ├── 01_schema.sql                #   DDL del proyecto (tabla demo)
│       └── 02_stg.sql                   #   GENERATED (gitignore); no lo aplica el reset
│
├── metadata/                            # Metadatos que lee Apache Hop
│   ├── rdbms/
│   │   ├── h2.json                      #   Conexión H2 (variables DB_H2_*)
│   │   ├── oracle_sisud.json            #   Oracle oefabd SISUD, fuente (variables DB_ORA_SISUD_*)
│   │   ├── oracle_BD_CURSOR.json         #   Oracle BD_CURSOR, destino (variables DB_ORA_REPO_*)
│   │   └── mysql.json                   #   Conexión MySQL (variables DB_MYSQL_*)
│   ├── pipeline-run-configuration/
│   │   └── local.json                   #   Run config "local" para pipelines
│   └── workflow-run-configuration/
│       └── local.json                   #   Run config "local" para workflows
│
├── python/                              # Dos capas: STG/DDL y post-staging (ver python/LEEME.md)
│   ├── LEEME.md                         #   Mapa de capas
│   ├── create_stg.py                    #   ENTRY STG: introspect → CREATE TABLE STG_* (no extrae filas)
│   ├── main.py                          #   ENTRY lógica: leer_h2 → unico .py → escritores
│   ├── config.py                        #   Compartido: project-config.json + inputs.yaml
│   ├── h2_conn.py                       #   Compartido: JDBC H2 (CREATE y SELECT)
│   ├── CONTRATO.md                      #   Contrato entrada/salida de la lógica
│   ├── plantilla_logica.py              #   Plantilla (copiar a logica/; no dejarla ahí)
│   ├── requirements.txt
│   ├── introspect/                      #   CAPA STG: schema vivo → Column (no filas)
│   │   ├── h2_ddl.py
│   │   ├── excel.py
│   │   ├── oracle.py
│   │   ├── mysql.py
│   │   └── sheets.py                    #   handler opcional (inputs type sheets)
│   └── io/                              #   CAPA post-staging: I/O
│       ├── leer_h2.py                   #     ENTRADA: H2 STG_* → DataFrames
│       └── cargar_dw.py                 #     SALIDA: TRUNCATE+INSERT MI_* → Oracle DW
│
├── logica/                              # Zona de pegado: un solo .py (+ paquete dwh/)
│   ├── LEEME.md
│   ├── ejecutar.py
│   └── dwh/
├── workflows/
│   ├── wf_create_stg.hwf                # Diseño: Reset H2 → Python STG → Success (H2 vivo)
│   └── wf_main.hwf                      # Corrida: Reset H2 → Python STG → Excel + Oracle + MySQL → demo → Run Python
│
├── pipelines/
│   ├── pl_demo.hpl                      # Pipeline demo: H2 DEMO_TABLA_EJEMPLO → Dummy
│   ├── pl_stage_excel.hpl               # Excel input_excel → H2 STG_GS1_* / STG_GS2_* (todo String)
│   ├── pl_stage_oracle.hpl              # SISUD.VW_MULTA_COERCITIVA → STG_ORA_VW_MULTA_COERCITIVA
│   ├── pl_stage_informes.hpl            # SISUD.CSEP_INFORMES_VIEW → STG_ORA_CSEP_INFORMES
│   └── pl_stage_mysql.hpl               # gappsdb.T_MVC_MULTACOERCITIVA_MC → STG_MYSQL_T_MVC_MULTACOERCITIVA
│
├── input_excel/                         # Excel local (*.xlsx gitignored): CAGR + Lambayeque
│
└── output/
    └── .gitkeep                         # Salidas generadas (xlsx, csv, logs)
```

## Flujos (`wf_create_stg.hwf` vs `wf_main.hwf`)

**Diseño** (`wf_create_stg.hwf`) — para mapear pipelines en el GUI:

```
Start → Reset H2 clean (SHELL: ./h2/scripts/reset_and_create.sh)
     → Python create STG (.venv/bin/python python/create_stg.py)
     → Success   (H2 queda vivo en 9092)
```

**Corrida / smoke** (`wf_main.hwf`):

```
Start → Reset H2 clean (SHELL: ./h2/scripts/reset_and_create.sh)
     → Python create STG (.venv/bin/python python/create_stg.py)
     → Stage Excel (pl_stage_excel.hpl)
     → Stage Oracle VW / Informes / MySQL (pl_stage_oracle.hpl, pl_stage_informes.hpl, pl_stage_mysql.hpl)
     → Pipeline demo (pl_demo.hpl) → Run Python (python/main.py) → Success
```

- **Reset H2 clean**: detiene el server H2, lo levanta y aplica `h2/sql/00_reset.sql` + `h2/sql/01_schema.sql`. H2 es **in-memory** (`mem:csep`): se limpia sola al parar el server, por eso el DDL se aplica por TCP después del start. El reset **no** ejecuta `02_stg.sql`.
- **Python create STG**: lee `inputs.yaml`, introspecta Oracle/MySQL/Sheets/Excel, escribe `h2/sql/02_stg.sql` y aplica `CREATE TABLE STG_*` en H2.
- **Stage Excel**: `pl_stage_excel.hpl` lee `input_excel/*.xlsx` (todo String) y carga `STG_GS1_*` / `STG_GS2_*` (truncate).
- **Stage Oracle / Informes / MySQL**: TableInput 1:1 hacia `STG_ORA_VW_MULTA_COERCITIVA`, `STG_ORA_CSEP_INFORMES`, `STG_MYSQL_T_MVC_MULTACOERCITIVA` (truncate).
- **Pipeline demo**: lee `PUBLIC.DEMO_TABLA_EJEMPLO` (creada en `01_schema.sql`) por la conexión `h2`. Es un smoke test: funciona sin BDs externas. Los extract `pl_stage_*` se cablean **después** de Python.
- **Run Python**: ejecuta `python/main.py` → lee H2 (`python/io/leer_h2.py`), corre la lógica (el único `.py` en `logica/`, zona de pegado), escribe `output/resultado.xlsx` y carga Oracle DW vía `cargar_dw.py` (conexión obligatoria).

## Cómo se propaga a un proyecto nuevo

1. Copiar `archetype/` a `<workspace>/<nombre_proyecto>/`.
2. Registrar el proyecto con `~/apps/hop/hop-conf.sh --project-create --project=<nombre> --project-home=<ruta> --project-keep-config-file`.
3. Completar variables en `project-config.json` (o `environments/local.json` + `./switch-env.sh local`).
4. Declarar fuentes en `inputs.yaml`, Play `wf_create_stg` (H2 vivo) y mapear `pl_stage_*.hpl`. Corrida: `wf_main.hwf`.
