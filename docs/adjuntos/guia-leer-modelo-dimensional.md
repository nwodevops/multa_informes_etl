# Cómo leer el modelo dimensional (guía para quien llega por primera vez)

> Para alguien que **nunca ha visto Kimball** ni este data warehouse.  
> Objetivo: entender **cómo está organizado** el modelo OEFA de multas y **cómo buscar información** sin ahogarse en el ETL.
>
> Detalle técnico del esquema: [`modelo-kimball.md`](modelo-kimball.md).  
> Cómo se arma el fact enriquecido: [`../lineamientos/extra/manual-como-se-arma-el-fact.md`](../lineamientos/extra/manual-como-se-arma-el-fact.md).  
> De dónde sale cada columna: [`../lineamientos/ANEXO_MAPEO_CAMPOS.md`](../lineamientos/ANEXO_MAPEO_CAMPOS.md).  
> Fuentes de origen: [`../lineamientos/extra/fuentes_datos/01-fuentes-datos.md`](../lineamientos/extra/fuentes_datos/01-fuentes-datos.md).  
> Inventario runtime: [`../inputs/README.md`](../inputs/README.md).

---

## 1. ¿Qué problema resuelve este warehouse?

OEFA registra **multas coercitivas** en varios sistemas y planillas (Google Sheets de oficinas y de unidades CSEP, y Oracle SISUD). Cada uno habla un “idioma” distinto (columnas, códigos, estados).

El **data warehouse** reúne esas filas en un solo lugar (Oracle, tablas `MI_*`) con reglas claras, para poder preguntar cosas de negocio sin pelearse con cuatro fuentes a la vez:

- ¿Cuántas multas hay por unidad / oficina / año?
- ¿Cuánto se cobró (UIT y soles)?
- ¿Cuánto demora el ciclo (notificación → firma)?
- ¿Qué tan bien “amarra” una fuente con otra?

---

## 2. Kimball en una página (sin jerga de más)

Imagina una estrella:

- En el **centro** está lo que **ocurrió** (el evento que quieres medir): aquí, **una multa**.
- En las **puntas** están las **etiquetas** para cortar y filtrar ese evento: quién es el administrado, qué órgano o oficina, de qué fuente vino, qué estado, qué año UIT, etc.

| Idea Kimball | En español | En este proyecto |
|---|---|---|
| **Hecho (fact)** | Tabla de eventos medibles (conteos, montos, días) | Negocio: `MI_FACT_MULTA_COERCITIVA`; evidencia: `MI_FACT_MC_CSEP` / `_OD` / `_SISUD` |
| **Dimensión (dim)** | Catálogo de “cómo mirar” el hecho | `MI_DIM_*` (8 dimensiones) |
| **Grano** | “¿Qué representa **una fila**?” | **1 fila = 1 multa** (en enriquecido: 1 fila Sheet F1 o F2) |
| **Clave foránea** | Puente numérico hecho ↔ dimensión | `ID_ORGANO`, `ID_OD`, `ID_FUENTE`, `ID_ADMINISTRADO`, … |
| **Medidas** | Números que sumas o promedias | `MONTO_UIT`, `MONTO_S`, `DIAS_*`, flags |

Regla mental:

> Primero identifica el **grano** (¿estoy mirando multas?).  
> Luego elige **dimensiones** (¿por fuente? ¿por CMIN? ¿por OD? ¿por estado?).  
> Al final mira las **medidas** (¿cuántas? ¿cuánto dinero? ¿cuántos días?).

No hace falta memorizar todas las columnas: con el grano y 2–3 dims ya puedes leer casi cualquier reporte.

---

## 3. Cómo está organizado *este* modelo

Prefijo de tablas: **`MI_`**. Esquema típico: `APP` (local) o `REPOCSEP` (remoto).

```text
   Evidencia (qué se descargó):
   · MI_FACT_MC_CSEP   ← 10 Sheets F2
   · MI_FACT_MC_OD     ← Sheets F1 OD
   · MI_FACT_MC_SISUD  ← vista F5

   Negocio (Sheet manda + CUM/CAM SISUD a la derecha):
                    ┌─ MI_DIM_ADMINISTRADO     (quién)
                    ├─ MI_DIM_ORGANO_UNIDAD    (unidad CSEP: CMIN, CRES, …)
                    ├─ MI_DIM_OD               (oficina desconcentrada F1)
                    ├─ MI_DIM_FUENTE_REGISTRO  (universo F1/F2/F5 (+ semilla histórica GAPPS))
                    ├─ MI_DIM_MATERIA_SUBSECTOR
   MI_FACT_MULTA ───┼─ MI_DIM_ESTADO           (resolución / multa / pago — misma tabla, roles distintos)
   COERCITIVA       ├─ MI_DIM_PARAMETRO_UIT    (valor UIT del año)
   (enriquecida)    └─ (fechas del ciclo van como columnas DATE en el hecho)

   MI_FACT_MC_CSEP ─< MI_DET_ETAPA_MC          (etapas internas 1:N, solo F2; también ID_FUENTE)

   Audit (foto cruda STG, fuera de estrella):
   · MI_AUD_F1_OD_MULTAS / MI_AUD_F2_CSEP_MULTAS / MI_AUD_F2_CSEP_ETAPAS / MI_AUD_F5_SISUD_VW

   Calidad / KPIs: se calculan en la corrida Python (memoria / RESULTADO).
   Se publican a Oracle: `MI_DQ_HALLAZGO` (R01–R05). No se publican `MI_QA_*` ni `MI_INDICADOR_*`.
```

Cómo se arma el enriquecido (lookup): [`../lineamientos/extra/manual-como-se-arma-el-fact.md`](../lineamientos/extra/manual-como-se-arma-el-fact.md).

### Capas (de afuera hacia adentro)

| Capa | Qué es | ¿La usas para analizar? |
|---|---|---|
| Fuentes (Sheets, Oracle SISUD) | Origen crudo | Solo si depuras el ETL |
| Staging `STG_*` (H2, temporal) | Copia 1:1 de cada fuente | No; desaparece al reiniciar H2 |
| Modelo `MI_*` (Oracle) | Dims + facts evidencia + enriquecido + `MI_AUD_*` | **Sí — aquí consultas** |

El ETL (Hop + Python) es el “traductor”. Tú, como lector del modelo, trabajas sobre **`MI_DIM_*` / `MI_FACT_*`** (y `MI_AUD_*` si auditas la foto cruda).

---

## 4. Mapa de tablas en lenguaje de negocio

### El hecho (el centro)

Hay **tres facts de evidencia** (auditoría de lo bajado) y **uno de negocio**:

| Tabla | Una fila es… | Preguntas típicas |
|---|---|---|
| `MI_FACT_MC_CSEP` | Una multa del Sheet F2 | Evidencia CSEP |
| `MI_FACT_MC_OD` | Una multa del Sheet F1 | Evidencia OD |
| `MI_FACT_MC_SISUD` | Una multa de la vista SISUD | Evidencia F5 |
| `MI_FACT_MULTA_COERCITIVA` | Una multa Sheet (F1∪F2) + CUM/CAM si hay match SISUD | **Reportes de negocio** |
| `MI_AUD_F*` | Foto cruda 1:1 del STG | Auditoría fuente (fuera de estrella) |

Regla de negocio (Sheet←SISUD): el enriquecido **no** añade filas solo-SISUD; crece en vertical con más Sheets y en horizontal con CUM/CAM.

Columnas útiles para orientarte:

- **Identidad / cruce:** `COD_MA`, `CUM`, `CAM`, `NUMERO_EXPEDIENTE`, `N_RES_MC`
- **Gestión F2 (attrs operativos):** `JEFE`, `UF`, `N_PROY_MC`, `ETA_REG_PROY_MC`, `ETA_REG_MC`, `RESULT_PROY_MC`, `ESTADO_MC_TXT`, `ESTADO_PAGO_TXT` (NULL en OD/SISUD si no aplica)
- **De qué fuente vino la fila:** `ID_FUENTE` → `MI_DIM_FUENTE_REGISTRO` (filtrar por `CODIGO` o por tabla evidencia)
- **Territorio:** `ID_ORGANO` (unidades CSEP) y `ID_OD` (oficinas OD)
- **Calendario firma:** `ID_TIEMPO_FIRMA` → `MI_DIM_TIEMPO` (además de `F_FIRMA_RES_MC` DATE)
- **Montos:** `MONTO_UIT`, `MONTO_S`, `MONTO_S_CALC` (recalculado con UIT)
- **Tiempos del ciclo:** `F_NOTIF_DCG`, `F_FIRMA_RES_MC`, `F_VENC_MC`, … y `DIAS_*`
- **Semáforos:** `FLAG_PAGADA`, `FLAG_PRESENTO_DCG`, …

### Las dimensiones (las puntas)

| Tabla | Responde | Origen principal (idea) |
|---|---|---|
| `MI_DIM_FUENTE_REGISTRO` | ¿De qué sistema/universo vino la fila? | Semilla F1…F5 (`CODIGO`) |
| `MI_DIM_ORGANO_UNIDAD` | ¿Qué unidad CSEP? (`SIGLA`, `DESCRIPCION`) | Solo las 10 del catálogo `f2_csep_sheets.json` (+ ND). Lookup hecho: `COORD` / `COD_UNIDAD` (o último token de expediente si es CSEP) |
| `MI_DIM_OD` | ¿Qué oficina desconcentrada? | F1 Sheets OD (`COD_OD`) |
| `MI_DIM_ADMINISTRADO` | ¿Quién es el administrado? | Sobre todo nombres de F5 |
| `MI_DIM_ESTADO` | ¿En qué estado? (varios roles) | Textos homologados de F1/F2/F5 |
| `MI_DIM_PARAMETRO_UIT` | ¿Cuánto valía la UIT ese año? | Catálogo MEF en el ETL |
| `MI_DIM_MATERIA_SUBSECTOR` | ¿Qué materia? | Semilla; a menudo `-1` si no hay dato |
| `MI_DIM_TIEMPO` | Calendario día a día | Generada; FK role-playing `ID_TIEMPO_FIRMA` |

#### Catálogo `MI_DIM_FUENTE_REGISTRO` (semillas)

| `ID_FUENTE` | `CODIGO` | `NOMBRE` | `FAMILIA_TDR` | Staging típico |
|---|---|---|---|---|
| −1 | `ND` | NO ESPECIFICADO | ND | — |
| 1 | `OD_SHEETS` | Sheets OD | F1 | `STG_GS2_OD_MULTAS` |
| 2 | `CAGR` | Sheets CSEP | F2 | `STG_GS1_CSEP_MULTAS` |
| 3 | `GAPPS` | MySQL GAPP (histórico) | F4 | fuera de ingestión |
| 4 | `SISUD_VW` | Oracle SISUD | F5 | `STG_ORA_*` |
| 5 | `OD_EXCEL` | Excel OD (legacy) | F1 | no se carga; el ETL normaliza a `OD_SHEETS` |

### Detalle y audit

| Tabla | Una fila es… | Cuándo mirarla |
|---|---|---|
| `MI_DET_ETAPA_MC` | Una etapa del flujo interno de un proyecto MC | Drill-down de F2; `ID_FUENTE` = CAGR |
| `MI_AUD_F1_OD_MULTAS` | Una fila cruda del Sheet OD | Auditoría 1:1 vs origen F1 |
| `MI_AUD_F2_CSEP_MULTAS` | Una fila cruda del Sheet CSEP | Auditoría 1:1 vs origen F2 |
| `MI_AUD_F2_CSEP_ETAPAS` | Una fila cruda de etapas CSEP | Auditoría 1:1 vs hoja etapas F2 |
| `MI_AUD_F5_SISUD_VW` | Una fila cruda de la vista SISUD | Auditoría 1:1 vs origen F5 |

> R01–R05 se materializan en Oracle como `MI_DQ_HALLAZGO`. QA amarre / KPIs K1–K5 se calculan en la corrida ETL (memoria). **No** hay tablas `MI_QA_*` / `MI_INDICADOR_*` en Oracle.

### Clave especial: `-1`

En casi todas las dims, **`ID_* = -1`** significa **“NO ESPECIFICADO”**: el hecho existe, pero no se pudo resolver esa etiqueta.  
Eso es a propósito (cuarentena blanda): el dato defectuoso **se marca**, no se tira.

---

## 5. Dos territorios que no debes mezclar

Es la duda más frecuente al abrir el modelo:

| Pregunta | Tabla / FK | Cómo filtrar |
|---|---|---|
| ¿Unidad sectorial CSEP? (Minería, Residuos, …) | `MI_DIM_ORGANO_UNIDAD` vía `ID_ORGANO` | `MI_FACT_MC_CSEP` o `fu.CODIGO = 'CAGR'` |
| ¿Oficina desconcentrada OD? (Ica, Puno, …) | `MI_DIM_OD` vía `ID_OD` | `MI_FACT_MC_OD` |

Una multa F2 suele tener órgano CSEP y `ID_OD = -1`.  
Una multa F1 suele tener OD y `ID_ORGANO` no resuelto (o solo por expediente).  
Por eso **acota siempre por fuente** (`ID_FUENTE` / tablas `MI_FACT_MC_*`) cuando compares mundos.

> **Nota:** `MI_DIM_ORGANO_UNIDAD` tiene **solo** las 10 unidades CSEP (+ ND). No se hincha con siglas de expediente. Filas sin `COORD`/`COD_UNIDAD` reconocido quedan en `ID_ORGANO = -1`.

---

## 6. Cómo buscar información (método)

### Paso a paso

1. **Define el grano:** evidencia → `MI_FACT_MC_CSEP|_OD|_SISUD`; negocio → `MI_FACT_MULTA_COERCITIVA`.
2. **Acota la fuente:** no sumar CSEP+OD+SISUD como un solo censo.
3. **Elige el corte territorial:** unidad CSEP → `MI_DIM_ORGANO_UNIDAD`; OD → `MI_DIM_OD`.
4. **Elige la medida:** `COUNT(*)`, `SUM(MONTO_UIT)`, `AVG(DIAS_NOTIF_A_FIRMA)`, etc.
5. Si el número “no cuadra” entre sistemas: compara evidencia (`MI_FACT_MC_*`) vs `MI_AUD_*` (foto cruda) y el enriquecido; el amarre H9 se calcula en la corrida (no queda tabla en Oracle).

### Conteos por universo (disciplina de reporte)

```sql
SELECT COUNT(*) FROM APP.MI_FACT_MC_CSEP;           -- evidencia F2
SELECT COUNT(*) FROM APP.MI_FACT_MC_OD;             -- evidencia F1
SELECT COUNT(*) FROM APP.MI_FACT_MC_SISUD;          -- evidencia F5
SELECT COUNT(*) FROM APP.MI_FACT_MULTA_COERCITIVA;  -- negocio (= CSEP + OD)
```

Filtrar por jefe (F2 en el enriquecido):

```sql
SELECT COD_MA, N_RES_MC, JEFE, UF, ETA_REG_PROY_MC, CUM, CAM, MONTO_UIT
FROM APP.MI_FACT_MULTA_COERCITIVA
WHERE UPPER(JEFE) LIKE '%MEJIA%'
FETCH FIRST 50 ROWS ONLY;
```

### Patrón SQL (esqueleto)

Conteo por universo de origen:

```sql
SELECT
    fu.CODIGO,
    fu.NOMBRE,
    fu.FAMILIA_TDR,
    COUNT(*) AS n_multas,
    SUM(f.MONTO_UIT) AS suma_uit
FROM APP.MI_FACT_MULTA_COERCITIVA f
LEFT JOIN APP.MI_DIM_FUENTE_REGISTRO fu
  ON fu.ID_FUENTE = f.ID_FUENTE
GROUP BY fu.CODIGO, fu.NOMBRE, fu.FAMILIA_TDR
ORDER BY 1;
```

Multas F2 por unidad CSEP:

```sql
SELECT
    o.SIGLA,
    o.DESCRIPCION,
    COUNT(*) AS n_multas,
    SUM(v.MONTO_UIT) AS suma_uit
FROM APP.MI_FACT_MC_CSEP v
LEFT JOIN APP.MI_DIM_ORGANO_UNIDAD o
  ON o.ID_ORGANO = v.ID_ORGANO
GROUP BY o.SIGLA, o.DESCRIPCION
ORDER BY n_multas DESC;
```

Multas firmadas en un trimestre (vía `ID_TIEMPO_FIRMA`):

```sql
SELECT t.ANIO, t.TRIMESTRE, COUNT(*) AS n
FROM APP.MI_FACT_MULTA_COERCITIVA f
JOIN APP.MI_DIM_TIEMPO t ON t.ID_TIEMPO = f.ID_TIEMPO_FIRMA
WHERE t.ANIO = 2024 AND t.TRIMESTRE = 3
GROUP BY t.ANIO, t.TRIMESTRE;
```

Comparar foto cruda audit vs evidencia (mismo universo F2):

```sql
SELECT COUNT(*) AS n_aud FROM APP.MI_AUD_F2_CSEP_MULTAS;
SELECT COUNT(*) AS n_fact FROM APP.MI_FACT_MC_CSEP;
```

Buscar una multa concreta (negocio):

```sql
SELECT f.COD_MA, f.N_RES_MC, f.JEFE, f.UF, f.CUM, f.CAM, f.MONTO_UIT, fu.NOMBRE AS FUENTE_NOMBRE
FROM APP.MI_FACT_MULTA_COERCITIVA f
LEFT JOIN APP.MI_DIM_FUENTE_REGISTRO fu ON fu.ID_FUENTE = f.ID_FUENTE
WHERE f.COD_MA = :cod_ma
;
```

Multas por oficina OD (F1):

```sql
SELECT
    d.COD_OD,
    d.NOMBRE,
    COUNT(*) AS n_multas
FROM APP.MI_FACT_MC_OD v
LEFT JOIN APP.MI_DIM_OD d
  ON d.ID_OD = v.ID_OD
GROUP BY d.COD_OD, d.NOMBRE
ORDER BY 1;
```

Etapas de un proyecto (F2):

```sql
SELECT e.*
FROM APP.MI_DET_ETAPA_MC e
WHERE e.COD_PROY_MC = :cod_proy
ORDER BY e.NRO_ETAPA;
```

### KPIs (solo en corrida ETL)

Los códigos K1…K5 se calculan en Python durante la corrida (`RESULTADO` / logs). **No** consultar `MI_INDICADOR_RESULTADO` en Oracle (ya no se publica).

| Código | Idea |
|---|---|
| K1 | Cobertura (conteos) |
| K2 | Oportunidad / tiempos |
| K3 | Cobranza |
| K4 | Verificación post-MC |
| K5 | Calidad / amarre entre fuentes |

---

## 7. De dónde “nacen” los datos (vista rápida)

| `CODIGO` (dim fuente) | Origen | Staging Hop | Tabla evidencia |
|---|---|---|---|
| `OD_SHEETS` | 31 Google Sheets OD | `STG_GS2_OD_MULTAS` | `MI_FACT_MC_OD` |
| `CAGR` | 10 Google Sheets CSEP | `STG_GS1_CSEP_MULTAS` (+ etapas) | `MI_FACT_MC_CSEP` |
| `SISUD_VW` | Vista Oracle SISUD | `STG_ORA_*` | `MI_FACT_MC_SISUD` |

Inventario de campos crudos: carpeta [`../lineamientos/extra/fuentes_datos/`](../lineamientos/extra/fuentes_datos/).

---

## 8. Volúmenes de referencia (corrida local reciente)

Cifras orientativas tras `./init.sh` (esquema `APP`). Cambian con cada corrida.

| Objeto | Filas (aprox.) |
|---|---|
| `MI_FACT_MC_CSEP` | ~990 |
| `MI_FACT_MC_OD` | ~281 |
| `MI_FACT_MC_SISUD` | ~534 |
| `MI_FACT_MULTA_COERCITIVA` | ~1 271 (= CSEP+OD) |
| `MI_DET_ETAPA_MC` | ~2 070 |
| `MI_AUD_F2_CSEP_MULTAS` | ≈ CSEP STG |
| `MI_AUD_F2_CSEP_ETAPAS` | ≈ etapas STG |
| `MI_AUD_F1_OD_MULTAS` | ≈ OD STG |
| `MI_AUD_F5_SISUD_VW` | ≈ SISUD STG |
| `MI_DIM_FUENTE_REGISTRO` | 6 (semilla) |
| `MI_DIM_OD` | 33 |
| `MI_DIM_ORGANO_UNIDAD` | ~11 (10 CSEP + ND) |

Detalle y diagramas: [`modelo-kimball.md`](modelo-kimball.md) §7.

---

## 9. Errores típicos y anti-patrones (no hacer)

1. **Sumar F1+F2+F5** sin acotar por `MI_FACT_MC_*` / `ID_FUENTE` → doble conteo.
2. **Usar `ID_ORGANO` para ODs** (o al revés) → territorio incorrecto.
3. **INNER JOIN entre fuentes “para que cuadre”** → el diseño no fuerza cruce; compara evidencia / AUD.
4. **Ignorar `-1`** → “faltan” atribuciones que son “no especificado”.
5. **Creer que staging `STG_*` es el DW** → destino = `MI_DIM_*` / `MI_FACT_*` (+ `MI_AUD_*`).
6. **Volver a meter F3 (informes)** en este DW → fuera de alcance.
7. **Buscar vistas `VW_MC_*` o tablas DQ/QA/K en Oracle** → deprecadas / no publicadas.
8. **Fusionar OD y órgano en una sola dim** → territorios distintos (F1 vs F2).

---

## 10. Orden sugerido para estudiar el modelo

1. Este documento (mapa mental).
2. [`modelo-kimball.md`](modelo-kimball.md) — diagrama de estrella y volúmenes.
3. DDL runtime [`../lineamientos/ddl/`](../lineamientos/ddl/) — `01` dims, `02` hechos, `07` enrich; audit en [`../lineamientos/ddl/audit/`](../lineamientos/ddl/audit/).
4. [`../lineamientos/ANEXO_MAPEO_CAMPOS.md`](../lineamientos/ANEXO_MAPEO_CAMPOS.md) — origen campo a campo.
5. Corrida real: `MI_FACT_*`, `MI_AUD_*`; conteos por `SIGLA` / `COD_OD`.

Con eso ya puedes **navegar** el warehouse sin haber visto Kimball antes: hecho en el centro, dimensiones para cortar, fuente etiquetada; audit aparte para foto cruda.
