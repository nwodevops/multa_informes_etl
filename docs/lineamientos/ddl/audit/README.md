# Audit Oracle — foto cruda (fuera de estrella)

Tablas `DW_M_AUD_*` en BD_CURSOR / REPOCSEP: copia 1:1 de staging H2, columnas VARCHAR.

| Tabla | Origen STG | Fuente |
|---|---|---|
| `DW_M_AUD_F1_OD_MULTAS` | `STG_GS2_OD_MULTAS` (`GS2`) | Sheets F1 |
| `DW_M_AUD_F2_CSEP_MULTAS` | `STG_GS1_CSEP_MULTAS` (`GS1`) | Sheets F2 |
| `DW_M_AUD_F2_CSEP_ETAPAS` | `STG_GS1_ETAPAS` (`ETAPAS`) | Sheets F2 etapas |
| `DW_M_AUD_F5_SISUD_VW` | `STG_ORA_VW_MULTA_COERCITIVA` (`ORA`) | Vista F5 |
| `DW_M_AUD_F4_FORM` | `STG_MYSQL_MULTAS` (`MYSQL`) | Query F4 `vw_multas_app.sql` |

Runtime: `python/audit/cargar_aud.py` (CREATE dinámico). No forma parte del wipe DDL `01`/`02`;
se regeneran **después** de `cargar_dw` (el wipe canónico borra todo `DW_M_%` y luego AUD se recrea).

No usar en KPIs ni enrich `07`. Solo auditoría de “qué se bajó”.

## Excepción 1:1 — `PK_OFICINA` (solo F1 y F2)

`DW_M_AUD_F1_OD_MULTAS` y `DW_M_AUD_F2_CSEP_MULTAS` agregan **una** columna derivada,
`PK_OFICINA`. Las otras tres tablas AUD siguen siendo foto cruda pura, y `PK_OFICINA`
no entra a `DW_M_DIM_*`, `DW_M_FACT_*` ni al enriquecido `07`.

Origen: `gappsdb.T_SEP_OFICINA` stageada en `STG_MYSQL_OFICINAS`
(`inputs.yaml` → `pl_stage_mysql.hpl`), leída como `OFICINAS` en
`python/io/leer_h2.py`. Resolución en `python/audit/oficinas.py`.

Publicación: `cargar_aud.enriquecer()` muta el dict de staging **antes** de abrir
cualquier conexión, así que la foto Oracle (`cargar_aud`) y el espejo MySQL
(`cargar_aud_mysql`, que arma sus columnas desde `df.columns`) publican la misma
forma. La columna llega a los dos destinos; si el espejo MySQL no responde,
`cargar_aud_mysql` avisa y la corrida sigue (Oracle ya cargó).

| AUD | Columna origen | Clave |
|---|---|---|
| `DW_M_AUD_F2_CSEP_MULTAS` | `COD_UNIDAD` | sigla → `Coordinación de Supervisión Ambiental en {nombre}` |
| `DW_M_AUD_F1_OD_MULTAS` | `COD_OD` | `Oficina (Desconcentrada de\|de Enlace) {nombre}` |

El emparejamiento es por nombre de oficina **completo y normalizado** (sin acentos,
mayúsculas, signos ni espacios), nunca por prefijo o subcadena. Un código sin
coincidencia queda `NULL` y se avisa por código en el log; nunca se descarta la fila.
Si un nombre llegara a corresponder a varias PK, el pipeline falla en vez de elegir una.

Tres unidades no se derivan del nombre de catálogo y declaran `pk_oficina` explícito
en `docs/inputs/f2_csep_sheets.json`:

| Sigla | `PK_OFICINA` | Motivo |
|---|---|---|
| `CCAM` | `COR068` | 3 oficinas de consultoras ambientales (`COR060`/`COR068`/`COR085`) |
| `UFED` | `COR095` | el catálogo dice “UF educación”; la oficina es “Unidad Funcional Supervisión Ambiental en Educación” |
| `UFSAVC` | `COR071` | el catálogo dice “UF vivienda”; la oficina es “…en Vivienda y Construcción” |

Cobertura verificada contra la fuente: F2 994/994 filas, F1 282/282 filas.
