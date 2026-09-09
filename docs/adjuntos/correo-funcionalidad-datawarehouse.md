# Borrador de correo — Data Warehouse de Multas Coercitivas

> Copiar el bloque siguiente al cuerpo del correo. Ajustar destinatario/saludo según corresponda.

---

**Asunto:** Data Warehouse de Multas OEFA — funcionalidad, inputs y cómo consultarlo

---

Estimados/as,

Les comparto un resumen del **Data Warehouse de Multas Coercitivas** (proyecto ETL OEFA): qué hace, de dónde toma los datos y cómo usarlo para análisis.

## ¿Qué funcionalidad ofrece?

El warehouse integra en un solo modelo Oracle (tablas `MI_*`) las multas coercitivas que hoy viven en sistemas y planillas distintas. Permite responder, sin cruzar a mano varias fuentes:

- ¿Cuántas multas hay por unidad CSEP, oficina OD o periodo?
- ¿Cuánto se cobró (UIT / soles) y cómo avanza el ciclo (notificación → firma → vencimiento / pago)?
- ¿Qué tan bien “amarra” una fuente con otra? (calidad / amarre H9 y KPI K5)

El modelo sigue un diseño **Kimball** (estrella):

- **Hecho:** `MI_FACT_MULTA_COERCITIVA` → **1 fila = 1 multa**
- **Dimensiones:** fuente, órgano/unidad CSEP, oficina OD, administrado, estado, tiempo, UIT, etc.
- **Detalle F2:** etapas en `MI_DET_ETAPA_MC`
- **Calidad y KPIs:** `MI_DQ_HALLAZGO`, `MI_QA_AMARRE` / `MI_QA_AMARRE_DETALLE`, `MI_INDICADOR_RESULTADO` (K1–K5)

> Alcance: **solo Multas**. Los informes de supervisión (F3) **no forman parte** de este DW.

Esquema típico: `APP` (local) o `REPOCSEP` (remoto).

## Inputs (de dónde nacen los datos)

El ETL (Apache Hop + Python) carga primero a staging (`STG_*`) y luego construye el modelo `MI_*`. Los inputs vigentes son:

| Universo | Origen | Qué entra al DW |
|---|---|---|
| **F1 — ODs** | **31 Google Sheets** de oficinas desconcentradas (catálogo `f1_ods_sheets.json`) | Multas OD → `ID_FUENTE` = OD_SHEETS; territorio por `MI_DIM_OD` |
| **F2 — CSEP** | **10 Google Sheets** de unidades CSEP (catálogo `f2_csep_sheets.json`) | Multas CSEP (+ etapas) → `ID_FUENTE` = CAGR; territorio por `MI_DIM_ORGANO_UNIDAD` |
| **F4 — GAPP** | ~~MySQL~~ **fuera de alcance** | Semilla histórica `ID_FUENTE=3`; sin ingestión |
| **F5 — SISUD** | Oracle (`VW_MULTA_COERCITIVA`) | Vista institucional / universo SISUD_VW |

Puntos importantes sobre inputs:

1. **F1 y F2 ya no dependen de Excel local como fuente principal**; se leen desde Google Sheets (se requiere `client_secret.json` y compartir cada sheet con la cuenta de servicio).
2. El Excel CAGR queda como **legacy** (p. ej. diccionario); los Excel OD de medidas administrativas tampoco son input operativo.
3. En el DW el linaje se guarda con **`ID_FUENTE`** (dimensión `MI_DIM_FUENTE_REGISTRO`). No se debe sumar F1+F2+F5 como un solo universo: son coberturas distintas (a veces solapadas) y mezclarlas infla conteos y confunde territorios CSEP vs OD. El amarre entre fuentes se mide con `MI_QA_AMARRE` / K5, no con un total único.

Inventario detallado: `docs/inputs/README.md` · manifiesto: `inputs.yaml`.

## Vistas de reporte por universo (`VW_MC_*`)

Hay **tres facts de evidencia** (`MI_FACT_MC_CSEP` / `_OD` / `_SISUD`) y un fact de **negocio enriquecido**
(`MI_FACT_MULTA_COERCITIVA` = Sheets enriquecidos con CUM/CAM de SISUD por resolución+monto, en SQL Oracle).

| Vista | Tabla base | Para qué sirve |
|---|---|---|
| **`VW_MC_CSEP`** | `MI_FACT_MC_CSEP` | Evidencia **10 Sheets CSEP** |
| **`VW_MC_OD`** | `MI_FACT_MC_OD` | Evidencia **Sheets OD** |
| **`VW_MC_SISUD`** | `MI_FACT_MC_SISUD` | Evidencia **vista SISUD** |
| **`VW_MC_ENRIQUECIDA`** | `MI_FACT_MULTA_COERCITIVA` | Negocio: planillas + CUM/CAM (lookup SISUD) |

**Regla:** evidencia = qué se descargó; enriquecido = lo que pide negocio (Sheet manda; sin filas solo-SISUD). No sumar CSEP+OD+SISUD como un solo censo.

## Dimensiones (`MI_DIM_*`) — para qué sirve cada una

Las dimensiones son los “cortes” del hecho. Se unen al hecho por `ID_*`:

| Dimensión | Responde a… | Cómo se usa |
|---|---|---|
| **`MI_DIM_FUENTE_REGISTRO`** | ¿De qué universo vino la fila? (F1/F2/F5; GAPPS histórico) | Linaje (`ID_FUENTE`). Base de las vistas `VW_MC_*`. |
| **`MI_DIM_ORGANO_UNIDAD`** | ¿Qué unidad CSEP? (CMIN, CRES, …) | Territorio **F2**. Solo las 10 unidades del catálogo (+ ND). |
| **`MI_DIM_OD`** | ¿Qué oficina desconcentrada? (Ica, Puno, …) | Territorio **F1**. Cortar multas OD por `COD_OD`. |
| **`MI_DIM_ADMINISTRADO`** | ¿Quién es el administrado? | Filtrar/agrupar por sujeto fiscalizado. |
| **`MI_DIM_ESTADO`** | ¿En qué estado? (resolución / multa / pago) | Misma tabla, varios roles vía `ID_ESTADO_*` en el hecho. |
| **`MI_DIM_TIEMPO`** | ¿En qué día/mes/trimestre/año? | Calendario; p. ej. firmas vía `ID_TIEMPO_FIRMA`. |
| **`MI_DIM_PARAMETRO_UIT`** | ¿Qué valor UIT aplica ese año? | Contexto de montos / recálculo en soles. |
| **`MI_DIM_MATERIA_SUBSECTOR`** | ¿Qué materia / subsector? | Corte temático; a menudo `-1` si no hay dato. |

**Notas rápidas:**
- `ID_* = -1` = “NO ESPECIFICADO” (el hecho existe; esa etiqueta no se resolvió).
- No usar `MI_DIM_ORGANO_UNIDAD` para ODs ni `MI_DIM_OD` para unidades CSEP: son territorios distintos.

## Cómo se usa el Data Warehouse

Para **analizar**, se consulta Oracle sobre `MI_*` / vistas `VW_MC_*` (no el staging `STG_*`).

Método recomendado:

1. Definir el grano (multas).
2. **Acotar por fuente** con la vista `VW_MC_*` del universo correspondiente.
3. Cortar por territorio: unidad CSEP (`MI_DIM_ORGANO_UNIDAD`) u oficina OD (`MI_DIM_OD`).
4. Medir: conteos, `MONTO_UIT` / `MONTO_S`, plazos `DIAS_*`, flags de pago/verificación.
5. Si hay diferencias entre sistemas: revisar amarre (`MI_QA_AMARRE_DETALLE`) y KPI **K5**, sin forzar cruces que “hagan cuadrar” artificialmente.

Ejemplos rápidos:

- Multas CSEP por unidad → `VW_MC_CSEP` + `MI_DIM_ORGANO_UNIDAD`
- Multas OD por oficina → `VW_MC_OD` + `MI_DIM_OD`
- KPIs ya calculados → `MI_INDICADOR_RESULTADO` (K1 cobertura, K2 tiempos, K3 cobranza, K4 verificación, K5 amarre)

Guía de lectura del modelo: `docs/adjuntos/guia-leer-modelo-dimensional.md`  
Manual breve (Word, 2 págs.): `docs/adjuntos/Manual_uso_datawarehouse_multas.docx`

Quedo atento/a a comentarios o a una sesión corta de recorrido sobre las vistas `VW_MC_*` y los catálogos de Sheets.

Saludos cordiales,  
[Nombre]

---

## Notas internas (no enviar)

- Adjuntar opcionalmente el Word `Manual_uso_datawarehouse_multas.docx`.
- Si el destinatario es solo negocio: se puede omitir la mención a `STG_*` / Hop.
- Si piden acceso técnico: indicar esquema Oracle (`REPOCSEP` / `APP`) y que el ETL se dispara con `init.bat` (Windows) o `./init.sh` (Linux).
