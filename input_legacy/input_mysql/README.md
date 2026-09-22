# MySQL (gappsdb) — F4 input del ETL

Query ancha al molde Excel F2. Hop la stagea a `STG_MYSQL_MULTAS`.

| Archivo | Contenido |
|---|---|
| [`vw_multas_app.sql`](vw_multas_app.sql) | 1 fila = 1 multa (`NU_IDMC`); códigos Excel + CUM/CAM |
| [`tablas.txt`](tablas.txt) | Tablas `T_MVC_*` de interés |

En el DW: `DW_M_AUD_F4_GAPPS` (foto 1:1) y filas del fact con `ID_FUENTE=GAPPS` (sin lookup SISUD).

Credenciales: `docs/credenciales/` / `environments/*.json` (`DB_MYSQL_*`). No versionar passwords aquí.
