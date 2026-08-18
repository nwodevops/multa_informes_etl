# Estructura del proyecto Apache Hop + H2

Estructura de `etl_cursor`, copia del arquetipo (original en `~/Documents/desarrollo/workspace_oefa/archetype`) portada a **Linux**.

```
etl_cursor/
├── project-config.json                  # Fuente única de variables (H2 + Oracle + MySQL)
├── switch-env.sh                        # Cambia entorno: ./switch-env.sh local|remote
├── switch-env.ps1                       # Referencia Windows (no se usa en Linux)
├── .gitignore                           # client_secret.json, *.xlsx, 02_stg.sql, .venv/
├── .venv/                               # GENERADO (gitignore): deps de python/requirements.txt
├── inputs.yaml                          # Manifiesto de fuentes STG (sources: [] = no-op)
├── README.md                            # Cómo usar el arquetipo
├── AGENTS.md                            # Guía para agentes en este proyecto
├── ESTRUCTURA.md                        # Este documento
├── .agents/skills/
│   ├── oefa-hop-etl/                    # Skill del arquetipo (Hop + H2 STG + Python)
│   │   ├── SKILL.md
│   │   ├── reference.md
│   │   └── inputs.example.yaml
│   └── medallion-auditable/             # Skill de capas, QA y trazabilidad (TDR d/e/f)
│       └── SKILL.md
├── docs/
│   ├── TDR REQ 3629-2026.pdf            # Requerimiento del servicio
│   └── arquitectura.md                  # Diagramas: vista general y capa de lógica
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
│   │   ├── oracle_repocsep.json         #   Oracle REPOCSEP, destino (variables DB_ORA_REPO_*)
│   │   └── mysql.json                   #   Conexión MySQL (variables DB_MYSQL_*)
│   ├── pipeline-run-configuration/
│   │   └── local.json                   #   Run config "local" para pipelines
│   └── workflow-run-configuration/
│       └── local.json                   #   Run config "local" para workflows
│
├── python/                              # DDL STG + capa de lógica
│   ├── create_stg.py                    #   DDL: introspecta fuentes, CREATE TABLE STG_* (no extrae filas)
│   ├── config.py                        #   project-config.json + inputs.yaml
│   ├── h2_ddl.py                        #   mapeo tipos + JDBC apply + connect_h2()
│   ├── main.py                          #   Lógica: orquesta leer_h2 → unico .py → escritores
│   ├── CONTRATO.md                      #   Contrato entrada/salida
│   ├── plantilla_logica.py              #   Plantilla (copiar a python/logica/)
│   ├── requirements.txt
│   ├── introspect/
│   │   ├── oracle.py
│   │   ├── mysql.py
│   │   └── sheets.py
│   ├── io/
│   │   ├── leer_h2.py                   #     ENTRADA: H2 → DataFrames (dict LECTURAS)
│   │   ├── escribir_excel.py            #     SALIDA default: output/resultado.xlsx
│   │   ├── escribir_mysql.py            #     SALIDA default: MySQL (skip si placeholders)
│   │   └── escribir_oracle.py           #     SALIDA legado: Oracle REPOCSEP (skip si placeholders)
│   └── logica/                          #     ZONA DE PEGADO: un solo .py auto-descubierto
│       └── LEEME.md
│
├── workflows/
│   ├── wf_create_stg.hwf                # Diseño: Reset H2 → Python STG → Success (H2 vivo)
│   └── wf_main.hwf                      # Corrida: Reset H2 → Python STG → Pipeline demo → Run Python
│
├── pipelines/
│   └── pl_demo.hpl                      # Pipeline demo: H2 DEMO_TABLA_EJEMPLO → Dummy
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
     → Pipeline demo (pl_demo.hpl) → Run Python (python/main.py) → Success
```

- **Reset H2 clean**: detiene el server H2, lo levanta y aplica `h2/sql/00_reset.sql` + `h2/sql/01_schema.sql`. H2 es **in-memory** (`mem:csep`): se limpia sola al parar el server, por eso el DDL se aplica por TCP después del start. El reset **no** ejecuta `02_stg.sql`.
- **Python create STG**: lee `inputs.yaml`, introspecta Oracle/MySQL/Sheets, escribe `h2/sql/02_stg.sql` y aplica `CREATE TABLE STG_*` en H2. Con `sources: []` es no-op (smoke test sin BDs externas).
- **Pipeline demo**: lee `PUBLIC.DEMO_TABLA_EJEMPLO` (creada en `01_schema.sql`) por la conexión `h2`. Es un smoke test: funciona sin BDs externas. Los extract `pl_stage_*` se cablean **después** de Python.
- **Run Python**: ejecuta `python/main.py` → lee H2 (`python/io/leer_h2.py`), corre la lógica (el único `.py` en `python/logica/`, zona de pegado), escribe `output/resultado.xlsx` y omite MySQL/Oracle si las credenciales son placeholders.

## Cómo se propaga a un proyecto nuevo

1. Copiar `archetype/` a `<workspace>/<nombre_proyecto>/`.
2. Registrar el proyecto con `~/apps/hop/hop-conf.sh --project-create --project=<nombre> --project-home=<ruta> --project-keep-config-file`.
3. Completar variables en `project-config.json` (o `environments/local.json` + `./switch-env.sh local`).
4. Declarar fuentes en `inputs.yaml`, Play `wf_create_stg` (H2 vivo) y mapear `pl_stage_*.hpl`. Corrida: `wf_main.hwf`.
