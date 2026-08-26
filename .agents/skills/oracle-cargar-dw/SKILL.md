---
name: oracle-cargar-dw
description: >-
  Carga TRUNCATE+INSERT del modelo dimensional a Oracle desde Python (oracledb):
  DDL formal numerado, TABLESPACE con cuota, coerción de tipos, orden FK,
  esquema incompleto, identity skip. Usar al implementar cargar_dw.py, depurar
  ORA-01950/ORA-12899/ORA-00907 o extender tablas DIM_/FACT_/INDICADOR_*.
---

# Carga Oracle DW (Python)

Módulo tipo: `python/io/cargar_dw.py`. Patrón **full refresh**: TRUNCATE hijos → padres → INSERT tipado → log `COUNT(*)`.

## Flujo `_prepare_schema`

1. DROP vistas legacy (`VW_FCT_*`) si existen.
2. Si falta modelo core (`MI_DIM_TIEMPO`…`MI_DQ_HALLAZGO`): aplicar DDL `01`→`02`→`03`→`04`.
3. Si core existe pero falta `MI_INDICADOR_RESULTADO`: solo DDL `04` (**no** droppear todo el modelo).
4. Si `MI_DQ_HALLAZGO` es esquema VARCHAR legacy: DROP + recrear `03`.
5. Tras schema listo: aplicar `05_comentarios.sql` (`COMMENT ON TABLE/COLUMN`) en cada corrida.

## DDL desde Python

- Leer `docs/lineamientos/ddl/NN_*.sql`; split por `;`.
- **Omitir** `INSERT` del DDL (Python carga todo, incluido miembro `-1`).
- **Inyectar** `TABLESPACE <nombre>` en `CREATE TABLE`/`CREATE INDEX` si el usuario no tiene cuota en SYSTEM.

```python
# Usuario APP suele tener cuota en USERS, default_tablespace SYSTEM
cur.execute("SELECT tablespace_name FROM user_ts_quotas WHERE ...")
# Append antes del ';': ) TABLESPACE USERS;
```

## Orden TRUNCATE / INSERT

```
MI_INDICADOR_RESULTADO → DET_* → FACT_* → DIM_* → MI_DQ_HALLAZGO
INSERT: DIM_* → FACT_* → DET_* → DQ_* → MI_INDICADOR_RESULTADO
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

- `ID_HALLAZGO`, `ID_RESULTADO`: omitir en INSERT (`skip_identity=True`).
- Claves de hechos (`ID_MC`, `ID_INFORME`): asignadas en Python antes del insert.

## Verificación

```
DW: MI_FACT_MULTA_COERCITIVA: 571 filas -> 571 en BD (OK)
```

Criterio: `n_bd == n_df` por tabla (excepto identity auto-generada no usada).

## Errores frecuentes

| ORA / error | Fix |
|---|---|
| ORA-01950 no privileges on SYSTEM | TABLESPACE USERS en CREATE |
| ORA-00907 missing parenthesis | TABLESPACE mal insertado (ir antes de `;`, no dentro de `(…)`) |
| ORA-12899 value too large | truncar VARCHAR por bytes; homologar CHAR(1) |
| DPY-3013 float for VARCHAR | `_coerce_for_oracle` por metadata |
| Esquema parcial tras fallo | `_model_complete` solo core; drop parcial si incompleto |

## No reutilizar

- Vistas `VW_FCT_*_VALIDADA` del modelo medallion viejo.
- Escritores legacy VARCHAR (`escribir_dw` / `escribir_oracle`) — eliminados; solo `cargar_dw.py`.

## Extender con tabla nueva

1. DDL en `01`–`04` (estructura) + `COMMENT ON` en `05_comentarios.sql`
2. `REQUIRED_CORE` o lista aparte; `TRUNCATE_ORDEN` / `INSERT_ORDEN`
3. `_prepare_schema`: aplicar DDL nuevo si falta
4. `_apply_column_comments`: añadir `COMMENT ON` de la tabla/columnas
5. `main.py`: incluir en `tablas_dw`
