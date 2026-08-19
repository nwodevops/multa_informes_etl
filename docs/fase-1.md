# Entregable 1 — actividades a, b y c (TDR REQ 3629-2026)

Sustento editable del **primer entregable** (numeral 6 y 7 del TDR). No es el PDF de mesa de partes.

Vista general con diagramas: [`fase-1-vista.md`](fase-1-vista.md). Inputs vs H2 vs Oracle: [`antes-durante-fase1.md`](antes-durante-fase1.md). Glosario: [`glosario.md`](glosario.md).

Alcance: consolidar informes de supervisión y multas coercitivas, revisar estructura y **diagnosticar** completitud/consistencia. **No se depura** (actividad d = entregable 2).

Código: [`../logica/ejecutar.py`](../logica/ejecutar.py) + paquete [`../logica/fase1/`](../logica/fase1/). Contrato: [`../python/CONTRATO.md`](../python/CONTRATO.md).

## Cómo corre

```
Hop wf_main (o smoke):
  Reset H2 → create_stg.py → pl_stage_* → python/main.py
```

- Bronze: H2 `mem:csep` tablas `STG_*` (efímeras).
- Silver landing + control: Oracle **BD_CURSOR** (PDB en `etl_oracle_xe2`, puerto **1524**, usuario `APP`), esquema `APP`.
- Anexo local: [`../output/fase1.xlsx`](../output/fase1.xlsx) (siempre).

Levantar el DW si no está:

```bash
cd ../bucket/data_for_etl   # o la ruta local del compose
docker compose up -d oracle_xe
```

Smoke post-staging (H2 ya cargado en esa corrida):

```bash
.venv/bin/python python/main.py
```

`INT_*` se recargan (TRUNCATE). `QA_*` se **acumulan** (append) por `ID_CORRIDA`.

## a) Consolidar

Integrar las fuentes proporcionadas **sin filtrar filas**. Cada universo queda en su `INT_*` porque **no hay llave conformada** entre Excel, SISUD y GAPP.

| Fuente operativa | Staging H2 | Landing BD_CURSOR | `FUENTE` |
|---|---|---|---|
| Excel CAGR hoja «1) Multas coercitivas» | `STG_GS1_MULTAS_COERCITIVAS` | `INT_MC_EXCEL` (UNION con GS2) | `GS1_CAGR` |
| Excel CAGR hoja «2) Etapas» | `STG_GS1_ETAPAS` | `INT_MC_ETAPAS` | `GS1_ETAPAS` |
| Excel Lambayeque hoja «5) Multas Coercitivas» | `STG_GS2_MULTAS_COERCITIVAS` | `INT_MC_EXCEL` | `GS2_LAMBAYEQUE` |
| Oracle SISUD `VW_MULTA_COERCITIVA` | `STG_ORA_VW_MULTA_COERCITIVA` | `INT_MC_SISUD` | `SISUD_VW_MULTA` |
| MySQL `gappsdb.T_MVC_MULTACOERCITIVA_MC` | `STG_MYSQL_T_MVC_MULTACOERCITIVA` | `INT_MC_GAPP` | `GAPP_T_MVC` |
| Oracle SISUD `CSEP_INFORMES_VIEW` | `STG_ORA_CSEP_INFORMES` | `INT_INFORMES` | `SISUD_CSEP_INFORMES` |

Reglas de a):

- Toda fila que llegó a `STG_*` aparece en el `INT_*` correspondiente.
- `INT_MC_EXCEL` = `concat(GS1, GS2)` alineando columnas; las de GS1 que GS2 no tiene quedan nulas en las filas Lambayeque.
- Columnas de control: `ID_CORRIDA`, `FUENTE`.
- No hay un hecho único «multa»: Excel es proyecto/MA; SISUD es expediente/resolución; GAPP es otro grano. Cruzarlos sería inventar equivalencia.

Invariante: `N_FILAS` de `INT_MC_EXCEL` = `N_FILAS(GS1) + N_FILAS(GS2)`. Igual 1:1 para los otros `INT_*` vs su `STG_*`.

## b) Revisar estructura

Correspondencia de campos según el schema vivo de [`../h2/sql/02_stg.sql`](../h2/sql/02_stg.sql) (regenerado por `create_stg.py`).

### Multas Excel: GS1 vs GS2

GS2 es un **subconjunto** de GS1 (mismas ideas de negocio, menos columnas operativas). Unión posible a nivel de columnas; no implica el mismo universo de expedientes.

| Campo | GS1 | GS2 | Rol aparente |
|---|---|---|---|
| `COD_MA` | sí | sí | Llave candidata de medida administrativa |
| `COD_PROY_MC` | sí | no | Proyecto de multa (GS1) |
| `EXP_INF_INCUMP` | sí | sí | Expediente / informe de incumplimiento |
| `N_CARTA_DCG` … `AMERIT_MC` | sí | sí | Trámite DCG / análisis |
| `N_RES_MC`, `F_FIRMA_RES_MC`, `MULTA_UIT`, `MULTA_S` | sí | sí | Resolución y monto |
| `ESTADO_MC`, `F_PAGO`, `ESTADO_PAGO_MC` | sí / GS1 extra | parcial | Cierre / pago |
| `JEFE`, `COORD`, `UF`, etapas de registro, auxiliares | GS1 | no | Organización interna CAGR |

Etapas (`STG_GS1_ETAPAS`): grano `COD_PROY_MC` + `NRO_ETAPA_MC`. Puente **interno** a GS1 por `COD_PROY_MC`, no a SISUD/GAPP.

### SISUD `VW_MULTA_COERCITIVA` vs Excel vs GAPP

| Idea | Excel | SISUD | GAPP |
|---|---|---|---|
| Identificador | `COD_MA`, `COD_PROY_MC` | `NUMERO_EXPEDIENTE`, `CUM`, `CAM` | `TX_IDCUM`, `TX_IDCAM`, `NU_IDINFORMACIONMC` |
| Administrado | no (o en texto de otras cols) | `ADMINISTRADO` | no |
| Resolución | `N_RES_MC` | `RESOLUCION` | no |
| Monto | `MULTA_UIT`, `MULTA_S` (texto, `#N/A`) | `MONTO_MULTA` (número) | `NU_MONTOMCUIT`, `NU_MONTOMCS` |
| Estado | `ESTADO_MC` | `ESTADO_MULTA`, `ESTADO_RESOLUCION` | `FG_ESTADOMULTA` |
| Verificación post | `F_VERIF_POST_MC` | no | `FE_F_VERIF_POST_MC` |

Nombres parecidos (`CUM`/`TX_IDCUM`) **no** se tratan como llave conformada en esta fase. Cobertura de puentes = entregable 2 (`QA_COBERTURA_PUENTE`).

### Informes de supervisión (`CSEP_INFORMES_VIEW`)

Grano candidato: `IDACTIVIDAD` (y expediente `TXNUMEXP`). Campos de proceso: fechas de comisión, elaboración de informe, derivación, recomendación (`TXRECOMENDACION`), unidad (`TXSUBUNIDAD`, `TXCOORDINACION`). Universo distinto al de multas coercitivas.

### Tipos y periodos

- Excel: todo `VARCHAR` a propósito (`#N/A`). Fechas y montos se **inspeccionan** en QA, no se castean en `INT_`.
- SISUD/MySQL: tipos nativos en staging (timestamp/decimal); el landing a BD_CURSOR se serializa a `VARCHAR2(4000)` / `TIMESTAMP` según el DataFrame.
- Periodo de negocio: aún no hay columna `PERIODO` (fase 2, a partir de fecha de referencia del grano).

## c) Completitud, consistencia y coherencia

Controles **warn**: el pipeline no aborta. El defecto queda en el landing y se lista en QA.

### `QA_CORRIDA` (append)

Una fila por corrida, capa (`STG` / `INT`) y fuente:

| Columna | Significado |
|---|---|
| `ID_CORRIDA` | `YYYYMMDDHHMMSS` de la corrida |
| `N_FILAS` | Conteo del DataFrame |
| `N_LLAVE_NULA` | Filas sin la llave candidata |
| `N_DUPLICADO_LLAVE` | Repeticiones (se marca la 2.ª en adelante) |
| `CHECK_STS` | `OK` o `WARN` |
| `DETALLE` | Rama/commit git si hay, llave usada, conteo de fechas/montos no parseables |

### `QA_EXCEPCION` (append)

| `TIPO` | Qué lista |
|---|---|
| `LLAVE_NULA` | Identificador candidato vacío / `#N/A` |
| `DUPLICADO_LLAVE` | Solo ocurrencias extra (la primera no se lista) |
| `FECHA_NO_PARSEABLE` | Columnas `F_*` / `FE*` / `*FECHA*` que no castean |
| `MONTO_NO_PARSEABLE` | Columnas con `MULTA` o `MONTO` no numéricas |

Tope: 2000 excepciones **por tabla** para no inflar Excel/DW; el recorte queda anotado en `DETALLE` de `QA_CORRIDA`.

### Llaves candidatas (diagnóstico, no join)

| Tabla | Llave |
|---|---|
| Excel multas | `COD_MA` |
| Excel etapas | `COD_PROY_MC` + `NRO_ETAPA_MC` |
| SISUD multas | `NUMERO_EXPEDIENTE` |
| GAPP | `NU_IDINFORMACIONMC` |
| Informes | `IDACTIVIDAD` |

### Cómo leer los números

1. Abrir hoja `QA_CORRIDA` (o `RESULTADO`, es la misma portada) en `output/fase1.xlsx`.
2. Verificar invariante STG vs INT por fuente.
3. `WARN` + `QA_EXCEPCION` = hallazgo de calidad para el informe, no filas a borrar.
4. En BD_CURSOR: `SELECT * FROM APP.QA_CORRIDA ORDER BY ID_CORRIDA, CAPA, TABLA`.

Conteos de **esta máquina**, corrida `20260818195022` (`wf_main` Success, 2′50″). Invariante STG→INT 1:1 (Excel = 16+21). `QA_CORRIDA` en BD_CURSOR queda en **22** filas porque la corrida previa (sin extract) se **acumuló**. `QA_EXCEPCION` de esta corrida: **5480** (tope 2000/tabla; informes y SISUD no recortaron).

| TABLA | N_FILAS | N_LLAVE_NULA | N_DUPLICADO_LLAVE | CHECK_STS | Notas QA |
|---|---|---|---|---|---|
| STG_GS1_MULTAS_COERCITIVAS | 16 | 0 | 4 | WARN | `COD_MA` repetido |
| STG_GS2_MULTAS_COERCITIVAS | 21 | 0 | 3 | WARN | 2 fechas no parseables |
| STG_GS1_ETAPAS | 55 | 0 | 0 | OK | |
| STG_ORA_VW_MULTA_COERCITIVA | 530 | 0 | 357 | WARN | llave expediente; 530 montos no parseables |
| STG_MYSQL_T_MVC_MULTACOERCITIVA | 4 | 2 | 1 | WARN | muestra GAPP (4 filas) |
| STG_ORA_CSEP_INFORMES | 53288 | 0 | 1841 | WARN | `IDACTIVIDAD` repetido |
| INT_MC_EXCEL | 37 | 0 | 7 | WARN | UNION GS1+GS2 |
| INT_MC_ETAPAS | 55 | 0 | 0 | OK | |
| INT_MC_SISUD | 530 | 0 | 357 | WARN | espejo STG |
| INT_MC_GAPP | 4 | 2 | 1 | WARN | espejo STG |
| INT_INFORMES | 53288 | 0 | 1841 | WARN | espejo STG |

## Qué no entra (entregables 2 y 3)

- **d)** Depurar, homologar categorías, tipar `FCT_*`, `FG_VALIDO`.
- **e)** Trazabilidad publicada `VW_*_VALIDADA` y puentes `QA_COBERTURA_PUENTE`.
- **f–h)** Efectividad, indicadores, cuadros y hallazgos narrativos de gestión.

## Tablas en `APP@BD_CURSOR`

`INT_MC_EXCEL`, `INT_MC_ETAPAS`, `INT_MC_SISUD`, `INT_MC_GAPP`, `INT_INFORMES`, `QA_CORRIDA`, `QA_EXCEPCION`.
