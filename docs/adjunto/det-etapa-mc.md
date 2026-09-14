# `DW_M_DET_ETAPA_MC` — etapas del workflow de sede central

Detalle de la multa de **sede central**: **muchas filas de etapa por una multa**. No es el fact de negocio y no se analiza sola como universo (no mezclar con OD ni SISUD).

Relación:

```text
DW_M_FACT_MULTA_COERCITIVA  1  ───  N  DW_M_DET_ETAPA_MC
```

Sirve para ver en qué paso está (o estuvo) cada proyecto de multa: quién lo tiene, cuándo se asignó, si hubo conformidad, cuántos días llevó.

Solo hay etapas de **sede central**. Las planillas OD no traen esta hoja.

---

## De dónde salen los datos

Diez Google Sheets de sede central (unidades del catálogo [`f2_csep_sheets.json`](../inputs/f2_csep_sheets.json)). En cada libro, la hoja **`2) Etapas`**.

Camino:

```text
Sheet sede central  →  hoja "2) Etapas"  →  Hop  →  STG_GS1_ETAPAS (H2)
                                                 →  Python homologa y pega a la multa de sede central
                                                 →  Oracle DW_M_DET_ETAPA_MC
```

La foto cruda de esa descarga queda en `DW_M_AUD_F2_CSEP_ETAPAS` (nombre técnico interno). El detalle usable para reporte es `DW_M_DET_ETAPA_MC`.

La multa padre vive en la hoja **`1) Multas coercitivas`** del mismo Sheet. Se cruzan por **`COD_PROY_MC`** (código de proyecto de la multa). Si el código no aparece en el fact (filas de sede central), la etapa igual se guarda y `ID_MC` puede ir vacío.

---

## Cómo se arma (idea)

1. Hop baja las 10 hojas de etapas a una sola tabla staging (`STG_GS1_ETAPAS`).
2. Python limpia nombres de columnas (p. ej. `ACCION_MC` → `ACCION`) y tipifica fechas/números.
3. Por cada fila de etapa busca la multa de sede central con el mismo `COD_PROY_MC` y copia su `ID_MC`.
4. Se publica en Oracle junto al fact enriquecido. El `ID_MC` apunta a `DW_M_FACT_MULTA_COERCITIVA` (las filas de sede central van primero, así el id sigue coincidiendo).

`ID_FUENTE` en esta tabla es siempre sede central (`CODIGO` interno `CAGR`).

---

## Qué hay en cada fila

| Columna | En la planilla | Pregunta |
|---|---|---|
| `COD_PROY_MC` | `COD_PROY_MC` | ¿De qué proyecto/multa es esta etapa? |
| `NRO_ETAPA` | `NRO_ETAPA_MC` | ¿Qué número de paso? |
| `ACCION` | `ACCION_MC` | ¿Qué se hace en este paso? |
| `PERFIL_ENCARGADO` | `PERF_ENCARG_MC` | ¿Qué perfil? |
| `ENCARGADO` | `ENCARGADO_MC` | ¿Quién? |
| `F_ASIGNACION` | `F_ASIG_MC` | ¿Cuándo se asignó? |
| `F_ENTREGA_DEV` | `F_ENT_DEV_MC` | ¿Cuándo se entregó/devolvió? |
| `ESTADO_ETAPA` | `EST_ETAPA_MC` | ¿Terminada, pendiente, …? |
| `CONFORMIDAD` | `CONFORMIDAD_MC` | ¿Hubo conformidad? |
| `DIAS_ELABORACION` | `T_ELAB_MC` | ¿Cuántos días llevó? |
| `ID_MC` | (lookup) | Enlace al fact de negocio |

Catálogo y rango de la hoja: [`../inputs/README.md`](../inputs/README.md) (F2-ET). Lectura del DW: [`README.md`](README.md).
