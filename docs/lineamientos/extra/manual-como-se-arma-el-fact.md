# Manual: cómo se arma el FACT (lógica del código)

> Audiencia: negocio + técnico. Explica **qué hace** el ETL y **dónde** está en el código.  
> Pedido de negocio: Sheet manda; CUM/CAM se pegan desde SISUD por resolución + monto (lookup a la derecha).  
> MySQL/GAPP: fuera del alcance.

Archivos canónicos:

| Paso | Archivo |
|---|---|
| Homologar / clave de join | `logica/dwh/homologacion.py` |
| Separar F1 / F2 / F5 | `logica/dwh/integracion.py` |
| Orquestar | `logica/dwh/pipeline.py` |
| Armar dims + 3 facts evidencia | `logica/dwh/dimensional.py` |
| Cargar Oracle + enrich | `python/io/cargar_dw.py` |
| SQL del lookup | `docs/lineamientos/ddl/07_enrich_sheets_sisud.sql` |

---

## 1. Idea en una frase

1. **Bajar** cada fuente a su propio fact de evidencia (para auditar qué se descargó).  
2. **Después**, en Oracle, armar el fact de negocio: filas de Sheets (F1+F2) y, a la derecha, CUM/CAM de SISUD si hay match.

```text
Hop (Sheets + SISUD) → H2 STG_*
        ↓
   Python integra (3 bloques, sin merge aún)
        ↓
   3 facts evidencia en Oracle
        ↓
   SQL 07: LEFT JOIN → MI_FACT_MULTA_COERCITIVA
```

| Tabla | Qué es | Crece… |
|---|---|---|
| `MI_FACT_MC_CSEP` | Evidencia F2 (10 Sheets CSEP) | Vertical (más multas CSEP) |
| `MI_FACT_MC_OD` | Evidencia F1 (Sheets OD) | Vertical (más multas OD) |
| `MI_FACT_MC_SISUD` | Evidencia F5 (vista Oracle) | Vertical (más filas SISUD) |
| `MI_FACT_MULTA_COERCITIVA` | Negocio enriquecido | Vertical = F1∪F2; **horizontal** = CUM/CAM |

Vistas: `VW_MC_CSEP` / `VW_MC_OD` / `VW_MC_SISUD` = evidencia; `VW_MC_ENRIQUECIDA` = negocio.

---

## 2. Reglas de negocio (implementadas)

1. **Manda el Sheet.** Si hay 2 filas (mismo `N_RES_MC`, distinto `COD_MA`), el enriquecido tiene **2 filas**.  
2. **No es UNION de SISUD.** SISUD no agrega filas al negocio; solo aporta columnas.  
3. **Clave de lookup:** resolución normalizada + `MONTO_UIT`  
   (`0153-2026-…` ≡ `00153-2026-…`; monto 64).  
4. **Sin match:** la fila Sheet queda; CUM/CAM en NULL.  
5. **Empate en SISUD:** se toma la primera fila (`ROW_NUMBER` por CUM/CAM).  
6. **MySQL:** no entra.

Ejemplo de reunión: resolución `0153-2026-OEFA/DSEM` + 64 UIT → 2 filas Sheet → 2 filas enriquecidas, con el mismo CUM/CAM si SISUD matchea.

---

## 3. Paso a paso en el código

### 3.1 Hop: staging

Apache Hop deja cada fuente en H2 (`STG_GS1_*`, `STG_GS2_*`, `STG_ORA_*`).  
Python solo lee esos `STG_*` (no vuelve a Google Sheets en este paso).

### 3.2 Integración: tres bloques, sin merge

En `integracion.integrar()` cada fuente se homologa y se deja en su propio dataframe:

```python
# logica/dwh/integracion.py — idea
def integrar(gs1, gs2, etapas, ora, gs2_ods=None):
    df_csep = _integrar_gs1(gs1)          # F2 CSEP
    df_od = concat(_integrar_gs2(...))    # F1 OD
    df_sisud = _integrar_ora(ora)         # F5
    df_etapas = _integrar_etapas(etapas)
    return df_csep, df_od, df_sisud, df_etapas
```

Ahí **aún no** se hace el lookup SISUD. Solo se unifica el “molde” de columnas (`COLS_MULTAS`: `N_RES_MC`, `MONTO_UIT`, `CUM`, `CAM`, atributos operativos F2 como `JEFE`/`UF`/`ETA_*`, …).

Rename típico Sheets: `MULTA_UIT` → `MONTO_UIT`, `MULTA_S` → `MONTO_S`.  
Rename SISUD: `RESOLUCION` → `N_RES_MC`, `MONTO_MULTA` → `MONTO_UIT`.

### 3.3 Homologación y clave (para amarre / mismo criterio que SQL)

En `homologacion.py`:

```python
def normalizar_resolucion(val):
    # "0153-2026-OEFA/DSEM" y "00153-2026-OEFA/DSEM" → mismo correlativo
    ...

def clave_join_res_monto(n_res, monto_uit):
    # "153-2026-OEFA/DSEM|64.0000"
    ...
```

Esa clave se usa en calidad (puente H9 `RES_MONTO_Sheets_vs_SISUD`) y es el **mismo criterio** que el SQL 07 en Oracle.

### 3.4 Dimensional: 3 facts evidencia

`dimensional.construir_modelo()`:

1. Arma dimensiones compartidas (`MI_DIM_*`).  
2. Llama `_build_fact_multas` **tres veces** (CSEP, OD, SISUD).  
3. Deja `MI_FACT_MULTA_COERCITIVA` **vacío** en Python (lo llena Oracle después).

```python
# logica/dwh/dimensional.py — idea
fact_csep = _build_fact_multas(df_csep, ...)
fact_od = _build_fact_multas(df_od, ...)
fact_sisud = _build_fact_multas(df_sisud, ...)
# MI_FACT_MULTA_COERCITIVA = DataFrame vacío  → se llena en SQL 07
```

`_build_fact_multas` resuelve FKs (`ID_ORGANO`, `ID_OD`, `ID_FUENTE`, montos, flags, etc.) fila a fila del dataframe de esa fuente.

### 3.5 Carga Oracle + enrich

`cargar_dw.py`:

1. Wipe `MI_*` / `VW_*` y recrea DDL `01`–`04` + vistas `06`.  
2. `INSERT` de dims y de los **3 facts evidencia**.  
3. Ejecuta `_run_enrich_sheets_sisud()` → corre `07_enrich_sheets_sisud.sql`.

Ese SQL hace, en esencia:

```sql
-- Sheets (vertical F1∪F2)
SELECT * FROM MI_FACT_MC_CSEP
UNION ALL
SELECT * FROM MI_FACT_MC_OD

-- LEFT JOIN SISUD (horizontal: CUM/CAM)
LEFT JOIN (SISUD deduplicado por clave) 
  ON clave = norm(resolución) || '|' || monto
```

Resultado → `MI_FACT_MULTA_COERCITIVA` (vista de negocio: `VW_MC_ENRIQUECIDA`).

---

## 4. Horizontal vs vertical (para explicar en reunión)

| Operación | Dónde | Efecto |
|---|---|---|
| Más multas en F1 o F2 | Evidencia + enriquecido | Crece **en vertical** (más filas) |
| Lookup SISUD OK | Solo enriquecido | Crece **en horizontal** (CUM/CAM en la misma fila) |
| Fila solo en SISUD | Solo `MI_FACT_MC_SISUD` | **No** entra al enriquecido |

Caso F1 + F2:

- Multa F1 → 1 fila enriquecida (+ CUM/CAM si hay match).  
- Multa F2 → 1 fila enriquecida (+ CUM/CAM si hay match).  
- Total enriquecido = filas F1 + filas F2 (no F1+F2+SISUD).

---

## 5. Calidad y amarre

- `calidad.py`: reglas R01–R05 (no borra filas; marca hallazgos).  
- CUM/CAM vacío en Sheet tras el diseño enriquecido = esperado si no hubo match (advertencia).  
- Puente H9: `RES_MONTO_Sheets_vs_SISUD` compara conjuntos de claves Sheet vs SISUD → `MI_QA_AMARRE` / `_DETALLE` y K5.

---

## 6. Qué mirar en Oracle (demo rápida)

```sql
-- Evidencia
SELECT COUNT(*) FROM APP.MI_FACT_MC_CSEP;
SELECT COUNT(*) FROM APP.MI_FACT_MC_OD;
SELECT COUNT(*) FROM APP.MI_FACT_MC_SISUD;

-- Negocio (debe ≈ CSEP + OD)
SELECT COUNT(*) FROM APP.MI_FACT_MULTA_COERCITIVA;
-- o: SELECT COUNT(*) FROM APP.VW_MC_ENRIQUECIDA;

-- Caso 0153 / 64 UIT
SELECT COD_MA, N_RES_MC, MONTO_UIT, CUM, CAM
FROM APP.MI_FACT_MULTA_COERCITIVA
WHERE N_RES_MC LIKE '%153-2026-OEFA/DSEM%'
  AND MONTO_UIT = 64;
```

Esperado: **2 filas**; CUM/CAM llenos si SISUD tiene esa combinación.

---

## 7. Checklist para explicar

- [ ] Sé decir: evidencia = lo bajado; enriquecido = Sheet + CUM/CAM.  
- [ ] Sé decir: vertical = más multas Sheet; horizontal = lookup SISUD.  
- [ ] Sé apuntar a `integracion.py` (3 bloques) y a `07_enrich_sheets_sisud.sql` (LEFT JOIN).  
- [ ] Sé el caso 0153/64 → 2 filas.  
- [ ] Sé que MySQL no forma parte del modelo.
