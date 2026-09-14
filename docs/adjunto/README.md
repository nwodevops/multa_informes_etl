# Cómo leer este DW

Guía corta para consultar el modelo en Oracle. No es el manual técnico del ETL.

**CSEP** administra todas las fuentes (sede central, OD y SISUD). **No es una base de datos** ni un universo de filas en el fact.

Las planillas de multa son solo dos familias:

| Fuente | Qué es | Cuántas |
|---|---|---|
| **Sede central** | Google Sheets de las coordinaciones/unidades de Lima (CMIN, CRES, CHID, …) | 10 libros |
| **OD** | Google Sheets de las oficinas desconcentradas | 31 libros |

SISUD es Oracle (lookup de CUM/CAM, estado de resolución, medida, montos REC/TFA), no una tercera planilla.

Tabla de negocio: **`DW_M_FACT_MULTA_COERCITIVA`**. Una fila = una multa de esas planillas. Las dimensiones se pegan por `ID_*`. El valor `-1` en una FK significa “no especificado”.

```text
Sede central (10)  ─┐
                    ├─ se apilan (crece en filas)  ─►  FACT  ◄─ lookup SISUD (CUM/CAM, estado resolución, medida, REC/TFA)
OD (31)            ─┘
```

SISUD **no agrega filas** al fact. Si una multa solo existe en SISUD, no entra aquí; queda en la foto cruda `DW_M_AUD_F5_SISUD_VW`.

En `DW_M_DIM_FUENTE_REGISTRO.NOMBRE` se lee **Sede central** u **OD**. El código interno `CAGR` = sede central (alias histórico; no es “solo Agricultura”).

---

## Cómo se arma el universo (vertical + horizontal)

**Vertical — apilar planillas.**  
El universo de análisis es sede central más OD. Cada fila de planilla sigue siendo una fila. `ID_FUENTE` dice de qué familia vino. No se mezclan dos planillas en una sola fila.

**Horizontal — lookup a SISUD.**  
Sobre esas mismas filas se busca en SISUD (resolución normalizada + monto UIT). Si hay match y el Sheet no traía CUM/CAM (u otros identificadores institucionales), se rellenan a la derecha: también `ID_ESTADO_RESOLUCION`, `MEDIDA_ADMINISTRATIVA`, `MONTO_MULTA_REC` y `MONTO_MULTA_TFA` (las planillas no los tienen). Si no hay match, la multa **sigue**; esos campos quedan vacíos o `-1`.

Manda el Sheet: dos filas con la misma resolución y distinto expediente = dos filas en el fact.

Para reportar el universo: contar `DW_M_FACT_MULTA_COERCITIVA`. Cortar sede central vs OD con `ID_FUENTE`. No sumar SISUD como si fuera otro universo de filas.

---

## Hecho

| Tabla | Para qué |
|---|---|
| `DW_M_FACT_MULTA_COERCITIVA` | Multa coercitiva de negocio. Diccionario: [`diccionario-fact.md`](diccionario-fact.md). Qué no entra: [`fuera-del-fact.md`](fuera-del-fact.md). |

Detalle (no es un segundo fact de análisis):

| Tabla | Para qué |
|---|---|
| `DW_M_DET_ETAPA_MC` | Pasos del workflow de sede central (muchas etapas por una multa). Ver [`det-etapa-mc.md`](det-etapa-mc.md). |

---

## Dimensiones

Se usan haciendo `JOIN` desde el fact. En Power BI: arrastrar atributos de la dim y medidas del fact.

| Tabla | Pregunta que responde |
|---|---|
| `DW_M_DIM_TIEMPO` | ¿Cuándo se firmó? (año, trimestre, mes). El fact apunta con `ID_TIEMPO_FIRMA`. |
| `DW_M_DIM_ADMINISTRADO` | ¿Quién es el administrado? |
| `DW_M_DIM_ORGANO_UNIDAD` | ¿Qué unidad de sede central (CMIN, CRES, …)? |
| `DW_M_DIM_OD` | ¿Qué oficina desconcentrada? Distinta del órgano de sede central. |
| `DW_M_DIM_FUENTE_REGISTRO` | ¿La fila nació en sede central o en OD? |
| `DW_M_DIM_MATERIA_SUBSECTOR` | ¿Minería, hidrocarburos, …? (catálogo; puede quedar ND). |
| `DW_M_DIM_ESTADO` | Estados homologados. `ID_ESTADO_MULTA` / `ID_ESTADO_PAGO` salen de la planilla; `ID_ESTADO_RESOLUCION` de SISUD si match (`TIPO_ESTADO='RESOLUCION'`). |
| `DW_M_DIM_PARAMETRO_UIT` | UIT del año, para leer montos en contexto. |

---

## Apoyo (no son la estrella)

| Tabla | Para qué |
|---|---|
| `DW_M_DQ_HALLAZGO` | Qué regla de calidad falló y en qué campo. La multa **no se borra** del fact. |
| `DW_M_AUD_*` | Foto 1:1 de lo que bajó Hop (Sheets y SISUD). Sirve para auditar la descarga, no para el tablero de negocio. |

No consultar en Oracle tablas `DW_M_FACT_MC_*`: son evidencia de corrida en memoria, no el entregable.

---

## Consulta mínima

```sql
SELECT
    f.N_RES_MC,
    f.MONTO_UIT,
    f.CUM,
    f.CAM,
    f.MEDIDA_ADMINISTRATIVA,
    f.MONTO_MULTA_REC,
    f.MONTO_MULTA_TFA,
    er.CODIGO AS ESTADO_RESOLUCION,  -- ACTIVO / INACTIVO; ND si ID = -1
    fu.NOMBRE AS FUENTE,             -- Sede central o OD
    o.SIGLA   AS ORGANO,
    od.NOMBRE AS OD,
    t.ANIO,
    t.TRIMESTRE
FROM DW_M_FACT_MULTA_COERCITIVA f
JOIN DW_M_DIM_FUENTE_REGISTRO fu ON fu.ID_FUENTE = f.ID_FUENTE
JOIN DW_M_DIM_ORGANO_UNIDAD   o  ON o.ID_ORGANO  = f.ID_ORGANO
JOIN DW_M_DIM_OD              od ON od.ID_OD     = f.ID_OD
JOIN DW_M_DIM_TIEMPO          t  ON t.ID_TIEMPO  = f.ID_TIEMPO_FIRMA
JOIN DW_M_DIM_ESTADO         er ON er.ID_ESTADO = f.ID_ESTADO_RESOLUCION;
```

Diccionario del fact y equivalencia vs planillas: [`diccionario-fact.md`](diccionario-fact.md).  
Anexo técnico campo a campo: [`../lineamientos/ANEXO_MAPEO_CAMPOS.md`](../lineamientos/ANEXO_MAPEO_CAMPOS.md).  
Cómo se construye el fact en código: [`../lineamientos/extra/manual-como-se-arma-el-fact.md`](../lineamientos/extra/manual-como-se-arma-el-fact.md).
