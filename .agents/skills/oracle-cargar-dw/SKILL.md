---
name: oracle-cargar-dw
description: >-
  Carga del modelo dimensional a Oracle desde Python (oracledb): wipe DW_M_*/VW_*,
  DDL formal numerado, TABLESPACE con cuota, coerción de tipos, orden FK,
  identity skip. Usar al implementar cargar_dw.py, depurar ORA-01950/ORA-12899
  o extender tablas DIM_/FACT_/INDICADOR_*.
---

# Carga Oracle DW (Python)

Módulo: `python/io/cargar_dw.py`. Patrón **full refresh canónico**: cada corrida
borra el modelo `DW_M_*` / vistas `VW_MC_*` (y `VW_FCT_*` residuales), recrea desde
DDL `01`–`04`+`06`, INSERT tipado, enrich `07`, log `COUNT(*)`.

## Flujo `_prepare_schema` / `cargar_dw`

1. DROP vistas `VW_MC_%` / `VW_FCT_%` y tablas `DW_M_%` (orden hijos→padres).
2. Aplicar DDL `01`→`02`→`03`→`04` (con TABLESPACE).
3. Aplicar `06_vistas.sql` (`VW_MC_CSEP` / `_OD` / `_SISUD` / `VW_MC_ENRIQUECIDA`).
4. Aplicar `05_comentarios.sql` (`COMMENT ON`).
5. INSERT dims → facts evidencia → DET → DQ/QA → indicadores.
6. Ejecutar **`07_enrich_sheets_sisud.sql`** → `DW_M_FACT_MULTA_COERCITIVA`.

No hay migraciones ALTER ni `_ensure_*`: el esquema es siempre el DDL vigente.

## DDL desde Python

- Leer `docs/lineamientos/ddl/NN_*.sql`; split por `;`.
- **Omitir** `INSERT` del DDL en `01`–`04` (Python carga datos, incluido miembro `-1`).
- **Incluir** `INSERT`/`TRUNCATE` de `07` (el enrich es el INSERT).
- **Inyectar** `TABLESPACE <nombre>` en `CREATE TABLE`/`CREATE INDEX` si el usuario no tiene cuota en SYSTEM.

```python
cur.execute("SELECT tablespace_name FROM user_ts_quotas WHERE ...")
# Append antes del ';': ) TABLESPACE USERS;
```

## Orden INSERT

```
DIM_* → DW_M_FACT_MC_* → DET_* → DQ_* / QA_* → DW_M_INDICADOR_RESULTADO
luego: 07 enrich → DW_M_FACT_MULTA_COERCITIVA
```

## Coerción de tipos (`_coerce_for_oracle`)

| Tipo Oracle | Regla |
|---|---|
| VARCHAR2 | str(); truncar bytes UTF-8 al `data_length` |
| NUMBER | float/int; NA → NULL |
| DATE | `pd.Timestamp` → `datetime` |
| CHAR(1) | homologar SI/NO → S/N **antes** del insert |

No pasar float a columna VARCHAR (DPY-3013).

## Identity columns

- `ID_HALLAZGO`, `ID_RESULTADO`, `ID_AMARRE`, `ID_DETALLE`: omitir en INSERT (`skip_identity`).
- Claves de hechos (`ID_MC`): asignadas en Python antes del insert.

## Verificación

```
DW: DW_M_FACT_MC_CSEP: ~990 filas -> N en BD (OK)
DW: DW_M_FACT_MC_OD: ~281 filas -> N en BD (OK)
DW: DW_M_FACT_MC_SISUD: ~534 filas -> N en BD (OK)
# enrich 07 → DW_M_FACT_MULTA_COERCITIVA ~1271 (CSEP∪OD)
```

Criterio: `n_bd == n_df` por tabla de evidencia. Enriquecido se valida por COUNT post-07.
Script standalone: `python/verify_dw.py`.

## Errores frecuentes

| ORA / error | Fix |
|---|---|
| ORA-01950 no privileges on SYSTEM | TABLESPACE USERS en CREATE |
| ORA-00907 missing parenthesis | TABLESPACE mal insertado (ir antes de `;`, no dentro de `(…)`) |
| ORA-12899 value too large | truncar VARCHAR por bytes; homologar CHAR(1) |
| DPY-3013 float for VARCHAR | `_coerce_for_oracle` por metadata |

## No reutilizar

- Loaders VARCHAR auto-CREATE para `DIM_`/`FACT_` (eliminados del repo).
- Vistas `VW_FCT_*_VALIDADA` del modelo medallion viejo.
- MySQL/GAPP como fuente de filas (fuera de ingestión).

## Extender con tabla nueva

1. DDL en `01`–`04` (estructura) + `COMMENT ON` en `05_comentarios.sql`
2. Añadir a `INSERT_ORDEN` / `DROP_ORDEN` / `REQUIRED_CORE` en `cargar_dw.py`
3. `main.py`: incluir en `tablas_dw`
4. Si afecta el enriquecido: actualizar `07_enrich_sheets_sisud.sql` y `06_vistas.sql`
