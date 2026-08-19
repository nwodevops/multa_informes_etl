# CONTRATO — dos capas Python (no mezclar)

Ver también [`LEEME.md`](LEEME.md). Fase 1: [`../docs/fase-1.md`](../docs/fase-1.md).

```
CAPA STG / DDL (antes del extract Hop)
  python/create_stg.py      entry: inputs.yaml → introspect/ → CREATE TABLE STG_*
  python/introspect/        schema vivo. No extrae filas. No lógica.

CAPA POST-STAGING (después de que Hop cargó STG_*)
  python/main.py            orquesta: io/leer_h2 → [único .py de logica/] → escritores
  python/io/leer_h2.py      ENTRADA: H2 mem:csep → DataFrames (nombres = claves de LECTURAS)
  logica/                   LOGICA: un .py en la raiz (ejecutar.py) + paquete fase1/
  python/io/escribir_excel.py  SALIDA: output/fase1.xlsx (una hoja por DataFrame)
  python/io/escribir_dw.py     SALIDA: Oracle BD_CURSOR (INT_ refresh, QA_ append)
```

`config.py` y `h2_conn.py` son compartidos (variables + JDBC). No son negocio.

## Entrada de la lógica (la deja `python/io/leer_h2.py`)

Cada clave de `LECTURAS` se convierte en un DataFrame con **ese mismo nombre** inyectado
en el namespace del script de lógica.

| Nombre | Fuente (query en `leer_h2.py`) |
|---|---|
| `DEMO` | `SELECT ID, TXNOMBRE, FEALTA FROM PUBLIC.DEMO_TABLA_EJEMPLO` |
| `GS1` | `SELECT * FROM PUBLIC.STG_GS1_MULTAS_COERCITIVAS` |
| `ETAPAS` | `SELECT * FROM PUBLIC.STG_GS1_ETAPAS` |
| `GS2` | `SELECT * FROM PUBLIC.STG_GS2_MULTAS_COERCITIVAS` |
| `ORA` | `SELECT * FROM PUBLIC.STG_ORA_VW_MULTA_COERCITIVA` |
| `INFORMES` | `SELECT * FROM PUBLIC.STG_ORA_CSEP_INFORMES` |
| `MYSQL` | `SELECT * FROM PUBLIC.STG_MYSQL_T_MVC_MULTACOERCITIVA` |

`pandas` está disponible como `pd`.

## Salida (fase 1)

La lógica deja:

| Nombre | Qué es | Carga en BD_CURSOR |
|---|---|---|
| `RESULTADO` | Portada: copia de `QA_CORRIDA` | No (solo Excel) |
| `INT_MC_EXCEL` | UNION GS1+GS2, sin filtrar | TRUNCATE + INSERT |
| `INT_MC_ETAPAS` | Etapas Excel | TRUNCATE + INSERT |
| `INT_MC_SISUD` | Vista SISUD de multas | TRUNCATE + INSERT |
| `INT_MC_GAPP` | MySQL gapps | TRUNCATE + INSERT |
| `INT_INFORMES` | Informes de supervisión | TRUNCATE + INSERT |
| `QA_CORRIDA` | Una fila por corrida/capa/fuente | **Append** |
| `QA_EXCEPCION` | Un hallazgo por fila | **Append** |

`main.py` recoge del namespace todo `INT_*`, `QA_*` y `RESULTADO`. No escribe a MySQL
`gappsdb` (fuente) ni a Oracle REPOCSEP (legado).

Excel siempre: `output/fase1.xlsx`. Oracle DW: skip si `DB_ORA_DW_*` son placeholders;
si las credenciales están llenas y el PDB no responde, falla.

## Reglas

- En `logica/` no se abren conexiones, jars ni drivers. Solo pandas/stdlib.
- `python/io/` no se importa como `import io`. `main.py` carga por ruta.
- El landing `INT_` **no se filtra**. Defectos → `QA_EXCEPCION`, no se borran filas.
- No hay `FG_VALIDO` ni `FCT_` en esta fase (entregable 2).
