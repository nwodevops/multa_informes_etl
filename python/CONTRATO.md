# CONTRATO — capa de lógica (Python) del arquetipo Apache Hop + H2

El proyecto es un **arquetipo**: el I/O es genérico y reutilizable; solo se cambia la
**lógica de negocio** pegando un `.py` en `python/logica/`.

```
python/main.py              orquesta: SETUP → io/leer_h2.py → [único .py de logica/] → escritores
python/io/leer_h2.py        ENTRADA genérica : H2 mem:csep → DataFrames (nombres = claves de LECTURAS)
python/logica/              LOGICA de negocio : zona de pegado (un solo .py)
python/io/escribir_excel.py SALIDA default   : DataFrame → output/resultado.xlsx
python/io/escribir_mysql.py SALIDA default   : DataFrame → MySQL (skip si placeholders)
python/io/escribir_oracle.py SALIDA legado  : DataFrame → Oracle REPOCSEP (skip si placeholders)
```

`python/create_stg.py` e `introspect/` **no son esta capa**: solo emiten el DDL de `STG_*`.

## Entrada (la deja `python/io/leer_h2.py`)

Cada clave de `LECTURAS` se convierte en un DataFrame con **ese mismo nombre** inyectado
en el namespace del script de lógica.

| Nombre | Fuente (query en `leer_h2.py`) |
|---|---|
| `DEMO` | `SELECT ID, TXNOMBRE, FEALTA FROM PUBLIC.DEMO_TABLA_EJEMPLO` |

Para un ETL nuevo, agregar/editar entradas en `LECTURAS`; los nombres pasan a ser el
contrato de entrada de tu lógica. `pandas` está disponible como `pd`.

## Salida

La lógica debe dejar un DataFrame con el nombre de `SALIDA_DF` (default **`RESULTADO`**,
configurable en `python/main.py`).

El orquestador escribe:

1. Excel a `output/resultado.xlsx` (siempre, smoke test).
2. MySQL: TRUNCATE + INSERT + `COUNT(*)` leído de vuelta; skip si placeholders.
3. Oracle REPOCSEP: igual, legado; skip si placeholders.

## Cómo crear otro ETL en este arquetipo

1. Copiar `python/plantilla_logica.py` → `python/logica/<tu_logica>.py` (**un solo .py**).
2. Escribir la transformación usando los DataFrames de entrada (nombres de `LECTURAS`)
   y dejar el DataFrame `RESULTADO`.
3. Completar tabla/esquema en los escritores si el destino no es el default.
4. Reutilizar `python/io/` y `python/main.py` sin tocarlos.

## Reglas

- **Aislamiento de la lógica**: en `python/logica/` no se abren conexiones, no se cargan
  jars ni drivers, no se usan rutas de archivo. Solo pandas/stdlib sobre los DataFrames.
- `python/io/` no se llama `import io` desde el path de Python: choca con la stdlib.
  `main.py` carga esos módulos por ruta.
- Credenciales salen de `project-config.json`. Los passwords quedan en texto plano
  (igual que en Hop).
