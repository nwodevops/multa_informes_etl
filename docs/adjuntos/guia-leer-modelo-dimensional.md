# Cómo leer el modelo dimensional (guía para quien llega por primera vez)

> Para alguien que **nunca ha visto Kimball** ni este data warehouse.  
> Objetivo: entender **cómo está organizado** el modelo OEFA de multas y **cómo buscar información** sin ahogarse en el ETL.
>
> Detalle técnico del esquema: [`modelo-kimball.md`](modelo-kimball.md).  
> De dónde sale cada columna: [`../lineamientos/ANEXO_MAPEO_CAMPOS.md`](../lineamientos/ANEXO_MAPEO_CAMPOS.md).  
> Fuentes de origen: [`../lineamientos/extra/fuentes_datos/01-fuentes-datos.md`](../lineamientos/extra/fuentes_datos/01-fuentes-datos.md).  
> Inventario runtime: [`../inputs/README.md`](../inputs/README.md).

---

## 1. ¿Qué problema resuelve este warehouse?

OEFA registra **multas coercitivas** en varios sistemas y planillas (Google Sheets de oficinas y de unidades CSEP, MySQL GAPP, Oracle SISUD). Cada uno habla un “idioma” distinto (columnas, códigos, estados).

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
| **Hecho (fact)** | Tabla de eventos medibles (conteos, montos, días) | `MI_FACT_MULTA_COERCITIVA` |
| **Dimensión (dim)** | Catálogo de “cómo mirar” el hecho | `MI_DIM_*` (8 dimensiones) |
| **Grano** | “¿Qué representa **una fila**?” | En el hecho: **1 fila = 1 multa** |
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
                    ┌─ MI_DIM_ADMINISTRADO     (quién)
                    ├─ MI_DIM_ORGANO_UNIDAD    (unidad CSEP: CMIN, CRES, …)
                    ├─ MI_DIM_OD               (oficina desconcentrada F1)
                    ├─ MI_DIM_FUENTE_REGISTRO  (universo F1/F2/F4/F5)
                    ├─ MI_DIM_MATERIA_SUBSECTOR
   MI_FACT_MULTA ───┼─ MI_DIM_ESTADO           (resolución / multa / pago — misma tabla, roles distintos)
   COERCITIVA       ├─ MI_DIM_PARAMETRO_UIT    (valor UIT del año)
                    └─ (fechas del ciclo van como columnas DATE en el hecho)

   MI_FACT_MULTA ───< MI_DET_ETAPA_MC          (etapas internas 1:N, solo F2; también ID_FUENTE)

   Calidad / KPIs (no son la estrella, pero viven junto al modelo):
   · MI_DQ_HALLAZGO            defectos de datos (R01–R05)
   · MI_INDICADOR_RESULTADO    KPIs K1–K5 ya calculados
```

### Capas (de afuera hacia adentro)

| Capa | Qué es | ¿La usas para analizar? |
|---|---|---|
| Fuentes (Sheets, MySQL, Oracle) | Origen crudo | Solo si depuras el ETL |
| Staging `STG_*` (H2, temporal) | Copia 1:1 de cada fuente | No; desaparece al reiniciar H2 |
| Modelo `MI_*` (Oracle) | Estrella Kimball + calidad + KPIs | **Sí — aquí consultas** |

El ETL (Hop + Python) es el “traductor”. Tú, como lector del modelo, trabajas sobre **`MI_*`**.

---

## 4. Mapa de tablas en lenguaje de negocio

### El hecho (el centro)

| Tabla | Una fila es… | Preguntas típicas |
|---|---|---|
| `MI_FACT_MULTA_COERCITIVA` | Una multa coercitiva integrada | Conteos, montos, plazos, flags de pago/verificación |

Columnas útiles para orientarte:

- **Identidad / cruce:** `COD_MA`, `CUM`, `CAM`, `NUMERO_EXPEDIENTE`, `N_RES_MC`
- **De qué fuente vino la fila:** `ID_FUENTE` → `MI_DIM_FUENTE_REGISTRO` (el texto `FUENTE_REGISTRO` es el mismo código, por comodidad)
- **Territorio:** `ID_ORGANO` (unidades CSEP) y `ID_OD` (oficinas OD)
- **Montos:** `MONTO_UIT`, `MONTO_S`, `MONTO_S_CALC` (recalculado con UIT)
- **Tiempos del ciclo:** `F_NOTIF_DCG`, `F_FIRMA_RES_MC`, `F_VENC_MC`, … y `DIAS_*`
- **Semáforos:** `FLAG_PAGADA`, `FLAG_PRESENTO_DCG`, …

### Las dimensiones (las puntas)

| Tabla | Responde | Origen principal (idea) |
|---|---|---|
| `MI_DIM_FUENTE_REGISTRO` | ¿De qué sistema/universo vino la fila? | Semilla F1…F5 (`CODIGO` = `FUENTE_REGISTRO`) |
| `MI_DIM_ORGANO_UNIDAD` | ¿Qué unidad CSEP? (`SIGLA`, `DESCRIPCION`) | F2 Sheets + catálogo `f2_csep_sheets.json` (`COORD` → `SIGLA`) |
| `MI_DIM_OD` | ¿Qué oficina desconcentrada? | F1 Sheets OD (`COD_OD`) |
| `MI_DIM_ADMINISTRADO` | ¿Quién es el administrado? | Sobre todo nombres de F5 |
| `MI_DIM_ESTADO` | ¿En qué estado? (varios roles) | Textos homologados de F1/F2/F4/F5 |
| `MI_DIM_PARAMETRO_UIT` | ¿Cuánto valía la UIT ese año? | Catálogo MEF en el ETL |
| `MI_DIM_MATERIA_SUBSECTOR` | ¿Qué materia? | Semilla; a menudo `-1` si no hay dato |
| `MI_DIM_TIEMPO` | Calendario día a día | Generada; no es FK obligatoria del hecho |

#### Catálogo `MI_DIM_FUENTE_REGISTRO` (semillas)

| `ID_FUENTE` | `CODIGO` | `NOMBRE` | `FAMILIA_TDR` | Staging típico |
|---|---|---|---|---|
| −1 | `ND` | NO ESPECIFICADO | ND | — |
| 1 | `OD_SHEETS` | Sheets OD | F1 | `STG_GS2_OD_MULTAS` |
| 2 | `CAGR` | Sheets CSEP | F2 | `STG_GS1_CSEP_MULTAS` |
| 3 | `GAPPS` | MySQL GAPP | F4 | `STG_MYSQL_*` |
| 4 | `SISUD_VW` | Oracle SISUD | F5 | `STG_ORA_*` |
| 5 | `OD_EXCEL` | Excel OD (legacy) | F1 | no se carga; el ETL normaliza a `OD_SHEETS` |

### Detalle y calidad

| Tabla | Una fila es… | Cuándo mirarla |
|---|---|---|
| `MI_DET_ETAPA_MC` | Una etapa del flujo interno de un proyecto MC | Drill-down de F2 (elaboración, revisión, …); `ID_FUENTE` = CAGR |
| `MI_DQ_HALLAZGO` | Un defecto detectado en un registro | Auditar calidad; no “borra” la multa |
| `MI_INDICADOR_RESULTADO` | Un KPI ya agregado (K1–K5) | Tableros / respuesta rápida sin recalcular |

### Clave especial: `-1`

En casi todas las dims, **`ID_* = -1`** significa **“NO ESPECIFICADO”**: el hecho existe, pero no se pudo resolver esa etiqueta.  
Eso es a propósito (cuarentena blanda): el dato defectuoso **se marca**, no se tira.

---

## 5. Dos territorios que no debes mezclar

Es la duda más frecuente al abrir el modelo:

| Pregunta | Tabla / FK | Cómo filtrar |
|---|---|---|
| ¿Unidad sectorial CSEP? (Minería, Residuos, …) | `MI_DIM_ORGANO_UNIDAD` vía `ID_ORGANO` | `ID_FUENTE` → `CAGR` (o `FUENTE_REGISTRO = 'CAGR'`) |
| ¿Oficina desconcentrada OD? (Ica, Puno, …) | `MI_DIM_OD` vía `ID_OD` | `ID_FUENTE` → `OD_SHEETS` |

Una multa F2 suele tener órgano CSEP y `ID_OD = -1`.  
Una multa F1 suele tener OD y `ID_ORGANO` no resuelto (o solo por expediente).  
Por eso **acota siempre por fuente** (`ID_FUENTE` / `FUENTE_REGISTRO`) cuando compares mundos.

> **Nota:** `MI_DIM_ORGANO_UNIDAD` también acumula siglas derivadas de expedientes (no solo las 10 CSEP). Para reportes CSEP limpios, filtra `FUENTE_REGISTRO = 'CAGR'` y cruza con `DESCRIPCION` del catálogo F2.

---

## 6. Cómo buscar información (método)

### Paso a paso

1. **Define el grano:** “quiero multas” → `MI_FACT_MULTA_COERCITIVA`.
2. **Acota la fuente:** join a `MI_DIM_FUENTE_REGISTRO` (o filtro `FUENTE_REGISTRO`).
3. **Elige el corte territorial:** unidad CSEP → `MI_DIM_ORGANO_UNIDAD`; OD → `MI_DIM_OD`.
4. **Elige la medida:** `COUNT(*)`, `SUM(MONTO_UIT)`, `AVG(DIAS_NOTIF_A_FIRMA)`, etc.
5. Si el número “no cuadra” entre sistemas: mira **amarre / calidad** (`MI_DQ_HALLAZGO`, KPI K5), no asumas un INNER JOIN mágico entre fuentes.

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
    SUM(f.MONTO_UIT) AS suma_uit
FROM APP.MI_FACT_MULTA_COERCITIVA f
JOIN APP.MI_DIM_FUENTE_REGISTRO fu
  ON fu.ID_FUENTE = f.ID_FUENTE AND fu.CODIGO = 'CAGR'
LEFT JOIN APP.MI_DIM_ORGANO_UNIDAD o
  ON o.ID_ORGANO = f.ID_ORGANO
GROUP BY o.SIGLA, o.DESCRIPCION
ORDER BY n_multas DESC;
```

Multas por oficina OD (F1):

```sql
SELECT
    d.COD_OD,
    d.NOMBRE,
    COUNT(*) AS n_multas
FROM APP.MI_FACT_MULTA_COERCITIVA f
JOIN APP.MI_DIM_FUENTE_REGISTRO fu
  ON fu.ID_FUENTE = f.ID_FUENTE AND fu.CODIGO = 'OD_SHEETS'
LEFT JOIN APP.MI_DIM_OD d
  ON d.ID_OD = f.ID_OD
GROUP BY d.COD_OD, d.NOMBRE
ORDER BY 1;
```

Buscar una multa concreta:

```sql
SELECT f.*, fu.NOMBRE AS FUENTE_NOMBRE
FROM APP.MI_FACT_MULTA_COERCITIVA f
LEFT JOIN APP.MI_DIM_FUENTE_REGISTRO fu ON fu.ID_FUENTE = f.ID_FUENTE
WHERE f.COD_MA = :cod_ma          -- o CUM / CAM / NUMERO_EXPEDIENTE
;
```

Etapas de un proyecto (F2):

```sql
SELECT e.*
FROM APP.MI_DET_ETAPA_MC e
WHERE e.COD_PROY_MC = :cod_proy
ORDER BY e.NRO_ETAPA;
```

### Si solo quieres el KPI ya cocinado

Mira `MI_INDICADOR_RESULTADO` (códigos K1…K5) antes de reinventar el cálculo en SQL.

| Código | Idea |
|---|---|
| K1 | Cobertura (conteos) |
| K2 | Oportunidad / tiempos |
| K3 | Cobranza |
| K4 | Verificación post-MC |
| K5 | Calidad / amarre entre fuentes |

---

## 7. De dónde “nacen” los datos (vista rápida)

| `CODIGO` / `FUENTE_REGISTRO` | Origen | Staging Hop |
|---|---|---|
| `OD_SHEETS` | 31 Google Sheets OD | `STG_GS2_OD_MULTAS` |
| `CAGR` | 10 Google Sheets CSEP | `STG_GS1_CSEP_MULTAS` (+ etapas) |
| `GAPPS` | MySQL GAPP | `STG_MYSQL_*` |
| `SISUD_VW` | Vista Oracle SISUD | `STG_ORA_*` |

Inventario de campos crudos: carpeta [`../lineamientos/extra/fuentes_datos/`](../lineamientos/extra/fuentes_datos/).

---

## 8. Volúmenes de referencia (corrida local reciente)

Cifras orientativas tras `./init.sh` (esquema `APP`). Cambian con cada corrida.

| Objeto | Filas (aprox.) |
|---|---|
| `MI_FACT_MULTA_COERCITIVA` | ~1 801 |
| · `CAGR` (F2) | ~986 |
| · `SISUD_VW` (F5) | ~530 |
| · `OD_SHEETS` (F1) | ~281 |
| · `GAPPS` (F4) | ~4 |
| `MI_DET_ETAPA_MC` | ~2 070 |
| `MI_DIM_FUENTE_REGISTRO` | 6 (semilla) |
| `MI_DIM_OD` | 33 |
| `MI_DIM_ORGANO_UNIDAD` | cientos (10 CSEP + siglas de expediente) |
| `MI_DQ_HALLAZGO` | ~200 |
| `MI_INDICADOR_RESULTADO` | ~690 |

Detalle y diagramas: [`modelo-kimball.md`](modelo-kimball.md) §7.

---

## 9. Errores típicos al leer el modelo (primera vez)

1. **Sumar F1+F2+F4+F5 como si fueran el mismo universo** sin mirar `ID_FUENTE` / `FUENTE_REGISTRO` → doble conteo o mundos distintos.
2. **Usar `ID_ORGANO` para ODs** (o al revés) → territorio incorrecto.
3. **INNER JOIN entre fuentes** esperando 100 % de match → las claves no amarran completo; el diseño **mide** el amarre (H9 / K5).
4. **Ignorar `-1`** → “faltan” atribuciones que en realidad son “no especificado”.
5. **Creer que staging `STG_*` es el DW** → el destino analítico son las tablas `MI_*` en Oracle.
6. **Contar todas las filas de `MI_DIM_ORGANO_UNIDAD` como “unidades CSEP”** → la dim también tiene siglas de expediente; las 10 CSEP están en el catálogo F2 / `DESCRIPCION`.

---

## 10. Orden sugerido para estudiar el modelo

1. Este documento (mapa mental).
2. [`modelo-kimball.md`](modelo-kimball.md) — diagrama de estrella, KPIs y volúmenes.
3. DDL [`../lineamientos/ddl/01_dimensiones.sql`](../lineamientos/ddl/01_dimensiones.sql) y [`02_hechos.sql`](../lineamientos/ddl/02_hechos.sql) — columnas exactas.
4. [`../lineamientos/ANEXO_MAPEO_CAMPOS.md`](../lineamientos/ANEXO_MAPEO_CAMPOS.md) — origen campo a campo.
5. Corrida real en Oracle: conteos por `MI_DIM_FUENTE_REGISTRO` y por `SIGLA` / `COD_OD`.

Con eso ya puedes **navegar** el warehouse sin haber visto Kimball antes: hecho en el centro, dimensiones para cortar, fuente etiquetada, y calidad aparte.
