# Arquitectura del proyecto

Cómo está armado este ETL hoy, con foco en qué hace exactamente la capa de lógica
(Python). Rama `capa-python`: la capa R de `master` se reemplazó; el contrato es el mismo.

Estado: capa lógica alineada a [`lineamientos/PROPUESTA_ADAPTADA_ETL.md`](lineamientos/PROPUESTA_ADAPTADA_ETL.md)
**Fases 2–3** (`logica/dwh/`: perfilamiento, diccionario, homologación, integración en memoria).
Modelo dimensional `FACT_*`/`DIM_*` en Oracle BD_CURSOR = lineamiento Fases 5–6 (pendiente).
Detalle implementación: [`lineamientos/implementacion-fase-2-3.md`](lineamientos/implementacion-fase-2-3.md).
TDR: [`TDR REQ 3629-2026.pdf`](TDR%20REQ%203629-2026.pdf).

## Vista general

Cuatro tecnologías, cada una con un trabajo que las otras no hacen. Python aparece dos
veces a propósito: DDL de staging y lógica de negocio son entry points distintos.

```mermaid
flowchart TB
  subgraph fuentes [Fuentes]
    GS["Google Sheets"]
    ORA["Oracle SISUD"]
    MY["MySQL"]
  end

  subgraph declaracion [Declaracion]
    YAML["inputs.yaml<br/>que fuente, que tabla STG"]
    PCFG["project-config.json<br/>unica fuente de variables"]
  end

  subgraph ddl [DDL de staging]
    PY["python/create_stg.py<br/>introspecta y crea CREATE TABLE"]
  end

  subgraph extract [Extract]
    HOP["Apache Hop<br/>pipelines pl_stage_*.hpl"]
  end

  subgraph staging [Staging efimero]
    H2["H2 mem:csep<br/>tablas STG_*"]
  end

  subgraph logica [Logica de negocio]
    PYL["python/main.py<br/>unico .py en logica/"]
  end

  subgraph destino [Destino]
    OUT["Excel fase1.xlsx<br/>Oracle APP@BD_CURSOR"]
  end

  GS --> YAML
  ORA --> YAML
  MY --> YAML
  YAML --> PY
  PCFG --> PY
  PY -->|"crea tablas vacias"| H2
  GS --> HOP
  ORA --> HOP
  MY --> HOP
  PCFG --> HOP
  HOP -->|"truncate + insert"| H2
  H2 --> PYL
  PCFG --> PYL
  PYL --> OUT
```

| Capa | Hace | No hace |
|---|---|---|
| `inputs.yaml` | Declara fuentes y el nombre `STG_*` | Extraer filas |
| Python DDL | Introspecta el schema vivo y emite el DDL de H2 | Cargar datos ni reglas |
| Hop | Extrae 1:1 y carga `STG_*` | Lógica de negocio multi-fuente |
| Python lógica | Unión, reglas, esquema ancho | Abrir conexiones dentro de `logica/` |
| H2 | Landing tolerante, todo nullable | Persistir entre corridas |

La separación que sostiene el diseño: **`create_stg.py` decide la forma de las tablas, Hop
mueve las filas y `logica/` decide el significado**. H2 es solo el punto de
encuentro, in-memory a propósito: cada corrida arranca de cero.

## Qué hace la capa de lógica

Ahí vive el negocio. El resto del proyecto existe para dejarle los DataFrames en memoria
y para llevarse el resultado.

Está partida en tres responsabilidades que no se mezclan:

```mermaid
flowchart TB
  subgraph orq [Orquestacion]
    MAIN["python/main.py<br/>sin negocio"]
  end

  subgraph io [I O generico, no se toca por proyecto]
    LEER["io/leer_h2.py<br/>LECTURAS: nombre a query"]
    XLS["io/escribir_excel.py"]
    MYW["io/escribir_mysql.py skip placeholder"]
    ORAW["io/escribir_oracle.py legado skip"]
  end

  subgraph zona [Zona de pegado, se reemplaza por proyecto]
    LOG["logica/*.py<br/>un solo archivo"]
  end

  subgraph contratos [Contratos]
    ENT["Entrada: un DataFrame<br/>por clave de LECTURAS"]
    SAL["Salida: DataFrame RESULTADO"]
  end

  MAIN --> LEER
  LEER --> ENT
  ENT -->|"inyecta nombres + pd"| LOG
  LOG --> SAL
  SAL --> XLS
  SAL --> MYW
  SAL --> ORAW
```

### La orquestación es deliberadamente tonta

`python/main.py` no tiene reglas de negocio. Hace cuatro cosas:

1. **Setup**: root + variables de `project-config.json`.
2. **Entrada**: carga `python/io/leer_h2.py` por ruta, llama a `leer_h2(root, variables)`.
3. **Lógica**: lista los `.py` de `logica/` (raíz del proyecto) y hace `exec` del único que encuentra,
   con los DataFrames y `pd` inyectados en el namespace.
4. **Salida**: verifica que exista `RESULTADO` y lo pasa a los escritores.

El paso 3 es el corazón del arquetipo: `main.py` **auto-descubre** el archivo de lógica y
**falla a propósito** si hay cero o más de uno. Esa restricción es la que hace que las
fases del servicio se manejen **por rama de git y no por carpetas**.

`python/io/` no se importa como paquete `io`: choca con la stdlib. `main.py` carga esos
módulos por ruta (`importlib`).

### El contrato: nombres, no argumentos

La lógica no recibe parámetros. Recibe **nombres ya poblados en el namespace**, que
salen de las claves de `LECTURAS`:

```python
LECTURAS = {
    "DEMO": "SELECT ID, TXNOMBRE, FEALTA FROM PUBLIC.DEMO_TABLA_EJEMPLO",
}
```

```python
RESULTADO = DEMO[["ID", "TXNOMBRE", "FEALTA"]].copy()
RESULTADO["FEALTA"] = pd.to_datetime(RESULTADO["FEALTA"]).dt.date
```

Agregar una fuente al ETL es agregar una clave a `LECTURAS` y usar ese nombre en la
lógica. Contrato: [`../python/CONTRATO.md`](../python/CONTRATO.md).

### Aislamiento: qué está prohibido dentro de logica/

Sin conexiones, sin jars, sin drivers, sin rutas de archivo. Todo eso vive en
`python/io/`. La lógica es **pegable**: se copia un `.py` escrito contra DataFrames y
corre. `pandas` llega inyectado como `pd`.

### La corrida completa

```mermaid
sequenceDiagram
  participant HOP as Hop wf_main
  participant H2 as H2 mem:csep
  participant MAIN as python/main.py
  participant LEER as io/leer_h2.py
  participant LOG as logica/*.py
  participant XLS as io/escribir_excel.py
  participant ESC as io/escribir_mysql Oracle

  HOP->>H2: reset (stop, start, DDL)
  HOP->>H2: pipelines: truncate + insert STG_*
  HOP->>MAIN: python/main.py
  MAIN->>LEER: leer_h2(root, variables)
  LEER->>H2: JDBC, una query por clave de LECTURAS
  H2-->>LEER: filas
  LEER-->>MAIN: dict de DataFrames
  MAIN->>LOG: exec del unico .py
  LOG-->>MAIN: RESULTADO
  MAIN->>XLS: output/resultado.xlsx
  MAIN->>ESC: skip si placeholders; si no TRUNCATE INSERT COUNT
```

Los escritores a BD consultan `COUNT(*)` **después** del `INSERT`. Contar el DataFrame en
memoria no prueba nada sobre la base.

## Qué se evitó al salir de R (y qué quedó)

| Evitado | Qué había |
|---|---|
| Segundo runtime | R 4.3.3 + RJDBC + rJava aparte del venv |
| JVM por partida doble | rJava más JPype |
| Orden frágil | `options(java.parameters=...)` antes de `library(RJDBC)` |
| Credenciales duplicadas | `leer_h2.R` hardcodeaba URL y `sa`/`csep` |
| Jar extra | `lib/ojdbc11.jar`; ahora `oracledb` thin |
| Ruido en el log de Hop | `message()` de R salía como `ERROR: (stderr)` |

Lo que **no** desapareció: la JVM. H2 solo expone JDBC y `jaydebeapi` arrastra JPype.

## Dónde va cada cosa cuando arranque el ETL

```mermaid
flowchart LR
  TDR["TDR: informes de supervision<br/>y multas coercitivas"]

  subgraph f1 [rama fase-1]
    A["a consolidar"]
    B["b revisar estructura"]
    C["c validar completitud"]
    CAPA1["STG_ + INT_ + QA_"]
  end

  subgraph f2 [rama fase-2]
    D["d depurar"]
    E["e trazabilidad"]
    F["f efectividad"]
    CAPA2["FCT_ + VW_VALIDADA + IND_"]
  end

  subgraph f3 [rama fase-3]
    G["g cuadros y graficos"]
    H["h hallazgos"]
    CAPA3["salidas en output/"]
  end

  TDR --> f1 --> f2 --> f3
  A --> CAPA1
  B --> CAPA1
  C --> CAPA1
  D --> CAPA2
  E --> CAPA2
  F --> CAPA2
  G --> CAPA3
  H --> CAPA3
```

Las capas `INT_`, `FCT_`, `VW_*_VALIDADA`, `IND_` y `QA_` no existen todavía: se
construyen dentro de la capa de lógica, fase por fase. Reglas, controles de calidad y
por qué una rama por fase: [`../.agents/skills/auditable-soft-quarantine/SKILL.md`](../.agents/skills/auditable-soft-quarantine/SKILL.md). Fases técnicas del lineamiento: [`../.agents/skills/phased-dwh-lineamiento/SKILL.md`](../.agents/skills/phased-dwh-lineamiento/SKILL.md).
