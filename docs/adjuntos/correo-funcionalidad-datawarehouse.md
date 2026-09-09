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
- ¿Quién es el **jefe** / qué **UF** / en qué **etapa** está el proyecto? (campos del Sheet F2 en el DW)
- ¿Cuánto se cobró (UIT / soles) y cómo avanza el ciclo (notificación → firma → vencimiento / pago)?

El modelo sigue un diseño **Kimball** (evidencia + negocio):

- **Evidencia:** `MI_FACT_MC_CSEP` / `_OD` / `_SISUD` → lo descargado de cada fuente
- **Negocio enriquecido:** `MI_FACT_MULTA_COERCITIVA` → **Sheet manda**; CUM/CAM de SISUD a la derecha (resolución + monto)
- **Dimensiones:** fuente, órgano/unidad CSEP, oficina OD, administrado, estado, tiempo, UIT, etc.
- **Detalle F2:** etapas en `MI_DET_ETAPA_MC`
- **Audit (foto cruda):** `MI_AUD_F1_OD_MULTAS` / `MI_AUD_F2_CSEP_MULTAS` / `MI_AUD_F2_CSEP_ETAPAS` / `MI_AUD_F5_SISUD_VW` → columnas 1:1 del origen (fuera de la estrella)

> Alcance: **solo Multas**. Los informes de supervisión (F3) **no forman parte** de este DW.  
> No hay vistas `VW_MC_*` en el destino: se consulta **directo** `MI_FACT_*`.  
> Calidad/KPIs (DQ, amarre H9, K1–K5) se calculan en la corrida ETL; **no** se publican como tablas en Oracle.

Esquema típico: `APP` (local / Docker) o `REPOCSEP` (remoto).

## Inputs (de dónde nacen los datos)

El ETL (Apache Hop + Python) carga primero a staging (`STG_*`) y luego construye el modelo `MI_*`. Los inputs vigentes son:

| Universo | Origen | Qué entra al DW |
|---|---|---|
| **F1 — ODs** | **31 Google Sheets** de oficinas desconcentradas (catálogo `f1_ods_sheets.json`) | Multas OD → `ID_FUENTE` = OD_SHEETS; territorio por `MI_DIM_OD` |
| **F2 — CSEP** | **10 Google Sheets** de unidades CSEP (catálogo `f2_csep_sheets.json`) | Multas CSEP (+ etapas) → `ID_FUENTE` = CAGR; territorio por `MI_DIM_ORGANO_UNIDAD` |
| **F4 — GAPP** | ~~MySQL~~ **fuera de alcance** | Semilla histórica `ID_FUENTE=3`; sin ingestión |
| **F5 — SISUD** | Oracle (`VW_MULTA_COERCITIVA`) | Vista institucional / universo SISUD_VW |

Puntos importantes sobre inputs:

1. **F1 y F2** se leen desde Google Sheets (`client_secret.json` + compartir sheets con la cuenta de servicio).
2. El Excel CAGR queda como **legacy** (p. ej. diccionario).
3. Linaje en el DW: **`ID_FUENTE`** → `MI_DIM_FUENTE_REGISTRO`. **No** sumar F1+F2+F5 como un solo censo.

Inventario: `docs/inputs/README.md` · manifiesto: `inputs.yaml`.

## Tablas de consulta por universo

| Tabla | Para qué sirve |
|---|---|
| **`MI_FACT_MC_CSEP`** | Evidencia **10 Sheets CSEP** |
| **`MI_FACT_MC_OD`** | Evidencia **Sheets OD** |
| **`MI_FACT_MC_SISUD`** | Evidencia **vista SISUD** |
| **`MI_FACT_MULTA_COERCITIVA`** | Negocio: planillas + CUM/CAM; attrs F2 (`JEFE`, `UF`, …) |
| **`MI_AUD_*`** | Auditoría: foto cruda 1:1 del staging |

**Regla:** evidencia = qué se descargó; enriquecido = lo que pide negocio (Sheet manda; sin filas solo-SISUD). Conteos: enriquecida ≈ CSEP + OD.

```sql
SELECT COD_MA, N_RES_MC, JEFE, UF, ETA_REG_PROY_MC, CUM, CAM, MONTO_UIT
FROM APP.MI_FACT_MULTA_COERCITIVA
WHERE UPPER(JEFE) LIKE '%MEJIA%';
```

Manual del fact: `docs/lineamientos/extra/manual-como-se-arma-el-fact.md`

## Dimensiones (`MI_DIM_*`)

| Dimensión | Responde a… | Cómo se usa |
|---|---|---|
| **`MI_DIM_FUENTE_REGISTRO`** | ¿De qué universo vino la fila? | Linaje (`ID_FUENTE`); acotar CSEP / OD / SISUD |
| **`MI_DIM_ORGANO_UNIDAD`** | ¿Qué unidad CSEP? | Territorio **F2** (10 + ND) |
| **`MI_DIM_OD`** | ¿Qué oficina desconcentrada? | Territorio **F1** |
| **`MI_DIM_ADMINISTRADO`** | ¿Quién es el administrado? | Filtrar/agrupar |
| **`MI_DIM_ESTADO`** | ¿En qué estado? | Roles vía `ID_ESTADO_*` |
| **`MI_DIM_TIEMPO`** | ¿Día/mes/trimestre/año? | p. ej. `ID_TIEMPO_FIRMA` |
| **`MI_DIM_PARAMETRO_UIT`** | ¿UIT del año? | Contexto de montos |
| **`MI_DIM_MATERIA_SUBSECTOR`** | ¿Materia / subsector? | A menudo `-1` |

- `ID_* = -1` = “NO ESPECIFICADO”.
- No mezclar órgano CSEP con OD.

## Cómo se usa

Consultar Oracle sobre **`MI_DIM_*` / `MI_FACT_*` / `MI_AUD_*`** (no `STG_*`, no vistas).

1. Definir el grano (multas).
2. Acotar por fuente: tabla evidencia o `ID_FUENTE` / `CODIGO`.
3. Cortar por territorio: CSEP → `MI_DIM_ORGANO_UNIDAD`; OD → `MI_DIM_OD`.
4. Medir: conteos, `MONTO_UIT` / `MONTO_S`, `DIAS_*`, flags.

Ejemplos:

- Multas CSEP por unidad → `MI_FACT_MC_CSEP` + `MI_DIM_ORGANO_UNIDAD`
- Multas OD por oficina → `MI_FACT_MC_OD` + `MI_DIM_OD`
- Negocio (jefe / CUM) → `MI_FACT_MULTA_COERCITIVA`

Guía: `docs/adjuntos/guia-leer-modelo-dimensional.md`  
Modelo: `docs/adjuntos/modelo-kimball.md`  
Manual Word: `docs/adjuntos/Manual_uso_datawarehouse_multas.docx`

Quedo atento/a a comentarios o a una sesión corta de recorrido sobre las tablas `MI_FACT_*` y los catálogos de Sheets.

Saludos cordiales,  
[Nombre]

---

## Notas internas (no enviar)

- Adjuntar opcionalmente el Word `Manual_uso_datawarehouse_multas.docx` (revisar si aún menciona `VW_MC_*`).
- Destinatario solo negocio: omitir `STG_*` / Hop / `MI_AUD_*`.
- Acceso técnico: esquema `REPOCSEP` / `APP`; ETL con `./init.sh` (Linux) o `init.bat` / `wf_main_win` (Windows).
- Cada corrida: wipe canónico de `MI_*` y republicación (dims + facts + AUD).
