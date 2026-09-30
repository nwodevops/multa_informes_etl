# Por qué `NUMERO_EXPEDIENTE` puede ser `NULL` en `DW_M_FACT_MULTA_COERCITIVA`

> Verificado en `REPOCSEP` @ `10.6.0.15:1532/dvoefacore` (2026-09-16). Fact: 1271 filas.

## 1. Qué es y de dónde sale

`NUMERO_EXPEDIENTE` documenta el **expediente del informe de incumplimiento** (formato típico `0133-2023-DSIS-CRES`).

| Fact | Planilla (sede central / OD) |
|---|---|
| `NUMERO_EXPEDIENTE` | `EXP_INF_INCUMP` |

En el ETL se copia tal cual con un simple `rename EXP_INF_INCUMP → NUMERO_EXPEDIENTE`
(`logica/dwh/integracion.py`). No se calcula, no se normaliza ni se rellena desde otra fuente.

## 2. Por qué es `NULL`

Tres razones, en orden de frecuencia:

### 2.1 La celda `EXP_INF_INCUMP` viene vacía en la planilla (caso real)

Como se copia tal cual, si la planilla no registró ese campo para la fila, el fact queda
`NULL`. Es independiente de otros campos: una multa puede tener expediente de la resolución
(`EXP_RES_MC`) y aun así no tener expediente del informe.

- `EXP_INF_INCUMP` = expediente del **informe de incumplimiento** (la supervisión previa).
- `EXP_RES_MC` = expediente de la **resolución** de multa (el acto final).

Que en los ejemplos de `docs/lineamientos/extra/fuentes_datos/fuentes-detalle.md` ambos
coincidan (`0067-2022-DSIS-CRES`) es coincidencia del caso documentado, no una regla.

### 2.2 SISUD no lo rellena (decisión de diseño)

SISUD **sí** tiene `NUMERO_EXPEDIENTE` (542/542 filas en `DW_M_AUD_F5_SISUD_VW`), pero el
lookup Sheet←SISUD solo pega:

`CUM`, `CAM`, `NUMERO_REGISTRO_SIGED`, `ID_ESTADO_RESOLUCION`, `ID_ADMINISTRADO`,
`MEDIDA_ADMINISTRATIVA`, `MONTO_MULTA_REC`, `MONTO_MULTA_TFA`
(+ sombras `N_RES_SISUD` / `MONTO_UIT_SISUD`).

`NUMERO_EXPEDIENTE` no está en la lista (`logica/dwh/enrich.py`, `_COLS_SISUD`). Incluso el
SQL histórico `07_enrich_sheets_sisud.sql` toma `NUMERO_EXPEDIENTE` solo del lado Sheet.
Regla documentada en `docs/adjunto/fuera-del-fact.md`: **SISUD no pisa identificadores de
Sheet**.

### 2.3 Es un campo descriptivo, no una clave

No interviene en el match con SISUD (ese match usa `N_RES_MC` + `MONTO_UIT`), ni en ningún
`JOIN`. Por eso un `NULL` no rompe ningún amarre: es solo un texto para auditar.

## 3. Cuánto ocurre (REPOCSEP)

| Consulta | Resultado |
|---|---|
| Filas del fact | 1271 |
| `NUMERO_EXPEDIENTE = NULL` y `EXP_RES_MC NOT NULL` | **208** (148 `CAGR` + 60 `OD_SHEETS`) |
| En la planilla de origen (`EXP_INF_INCUMP IS NULL` y `EXP_RES_MC NOT NULL`) | 149 en `DW_M_AUD_F2_CSEP_MULTAS`, 60 en `DW_M_AUD_F1_OD_MULTAS` |

(La diferencia 208 vs 209 se explica porque una fila trae `EXP_RES_MC = '  '` (espacios):
la homologación la vacía, así que esa fila ya no cumple `EXP_RES_MC NOT NULL` en el fact.)

## 4. Consulta de diagnóstico

```sql
-- ¿Cuántas y cuáles?
SELECT COUNT(*) FROM DW_M_FACT_MULTA_COERCITIVA
WHERE NUMERO_EXPEDIENTE IS NULL AND EXP_RES_MC IS NOT NULL;

SELECT COD_MA, EXP_INF_INCUMP, EXP_RES_MC
FROM DW_M_AUD_F2_CSEP_MULTAS
WHERE EXP_RES_MC IS NOT NULL AND EXP_INF_INCUMP IS NULL;

-- ¿El valor existe en SISUD para esa resolución/monto?
SELECT NUMERO_EXPEDIENTE
FROM DW_M_AUD_F5_SISUD_VW
WHERE RESOLUCION = '<N_RES_MC>' AND MONTO_MULTA = <MONTO_UIT>;
```

## 5. Si se requiere el valor

Dos opciones, a evaluar con negocio:

1. **Llenar desde SISUD** cuando el Sheet viene vacío: añadir `NUMERO_EXPEDIENTE` al lookup
   de `logica/dwh/enrich.py` con `_tomar_si_vacio`. Cambiaría ~208 filas y ya no sería
   "SISUD no pisa identificadores de Sheet".
2. **Dejarlo `NULL`** y documentar que la fuente primaria del expediente es la planilla;
   usar `EXP_RES_MC` como referencia cuando se quiera rastrear el trámite.

Relacionados: [`diccionario-fact.md`](diccionario-fact.md) · [`fuera-del-fact.md`](fuera-del-fact.md).