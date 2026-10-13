# impl `aud-pk-oficina`

Rama: `windows_v3`.

## Qué

`DW_M_AUD_F1_OD_MULTAS` y `DW_M_AUD_F2_CSEP_MULTAS` son foto 1:1 del staging
salvo por **una** columna: `PK_OFICINA`, la llave de la sede que emitió la
multa. Sin ella la auditoría no permite atribuir el hallazgo a una oficina.

Única excepción 1:1 del modelo. `DW_M_AUD_F2_CSEP_ETAPAS`,
`DW_M_AUD_F4_FORM` y `DW_M_AUD_F5_SISUD_VW` siguen foto cruda pura, y
`PK_OFICINA` no entra a `DW_M_DIM_*`, `DW_M_FACT_*` ni al enriquecido `07`.

## De dónde sale la PK

`COD_OD` (`TALARA`) no es una PK. La cadena son tres saltos:

| # | Dato | Origen |
|---|---|---|
| 1 | `COD_OD` | Staging F1 (`STG_GS2_OD_MULTAS`) |
| 2 | `nombre` (`Talara`) | `docs/inputs/f1_ods_sheets.json` |
| 3 | `TX_DESCRIPCION` | `gappsdb.T_SEP_OFICINA` → `PK_OFICINA` (`COR091`) |

Se generan candidatos con los 4 prefijos que usa GAPPS y gana el primero que
exista. Hace falta porque la fuente es inconsistente: existe
`Oficina de Enlace **de** Talara` (COR091) pero `Oficina de Enlace Chimbote`
(COR033), sin "de".

## Orden de resolución

1. **Override** del catálogo F2 (`pk_oficina` en `f2_csep_sheets.json`).
   Necesario para `CCAM`/`UFED`/`UFSAVC`, cuyo nombre de catálogo no
   corresponde a ningún `TX_DESCRIPCION` de la fuente.
2. **Derivación** por coincidencia normalizada.
3. **Sin coincidencia** → `NULL` + aviso, conservando la fila.

Emparejar por nombre **completo** normalizado, nunca por prefijo ni subcadena:
así un renombre en GAPPS produce `NULL` y no una PK equivocada de otra oficina.
Si un nombre quedara con 2 PK, la corrida **falla** (`oficinas.py:116`) en vez
de elegir una al azar.

## Archivos

- `inputs.yaml` + `pipelines/pl_stage_mysql.hpl` — `STG_MYSQL_OFICINAS` (5 col)
- `python/audit/oficinas.py` — índice normalizado y resolución
- `python/audit/cargar_aud.py` — `DERIVADOS_AUD` + `enriquecer()`
- `python/io/leer_h2.py` — lectura `OFICINAS`
- `python/f1_ods_catalog.py` / `f2_csep_catalog.py` — accesores de catálogo
- `docs/inputs/f2_csep_sheets.json` — overrides de las 3 siglas

`enriquecer()` muta el dict de staging **antes** de abrir cualquier conexión, así
que un fallo de `T_SEP_OFICINA` no deja una transacción Oracle a medias, y la
foto Oracle y el espejo MySQL publican la misma forma de columnas sin tocar
`cargar_aud_mysql.py`.

## Verificación

`init.bat` → **HARNESS OK** (exit 0), log `output/init_win_20260930_114519.log`.

En Oracle:

| Tabla | `COUNT(*)` | `COUNT(PK_OFICINA)` | |
|---|---|---|---|
| `DW_M_AUD_F1_OD_MULTAS` | 282 | 282 | 100.0% |
| `DW_M_AUD_F2_CSEP_MULTAS` | 994 | 994 | 100.0% |

Mapeo real: `TALARA→COR091`, `AMAZONAS→COR047`, `HUANUCO→COR037`,
`CAGR→COR065`, `CMIN→COR064`. Catálogos 31/31 y 10/10 resueltos.

Scope: dentro de `DW_M_*` la columna existe solo en esas 2 tablas. El esquema
tiene además `DW_ACU_*` / `DW_INF_CONSOL_*` con `PK_OFICINA`, pero son de otro
sistema, ya la traían y el wipe de este ETL solo borra `DW_M_%`.

Pruebas: `python/audit/tests/test_oficinas.py` (7, sin red) y
`test_oficinas_e2e.py` (7, MySQL real read-only).

## Merge

Se integró sobre `windows_v3` (dual-write MySQL) con 2 conflictos resueltos a
mano en `python/main.py` y `python/CONTRATO.md`. Fast-forward, sin force.
