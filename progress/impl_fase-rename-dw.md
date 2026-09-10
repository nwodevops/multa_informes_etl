# impl_fase-rename-dw

**Fecha:** 2026-08-25  
**Feature:** `fase-rename-dw` → `done`

## Qué se hizo

- Prefijo `DW_M_` en 11 tablas DW (DIM/FACT/DET/DQ/INDICADOR) en DDL, Python (`pipeline`, `cargar_dw`, `verify_dw`, `main`) y docs.
- Migración local: DROP tablas legacy sin `DW_M_` (`CASCADE CONSTRAINTS`) para evitar `ORA-02264`.
- Constraints restantes renombrados a `PK_DW_M_*` / `UQ_DW_M_*` / `FK_DW_M_*` / `CK_DW_M_*`.
- `main.py`: `_es_salida` y `tablas_dw` reconocen prefijos `DW_M_*`.
- `init.sh` / `init.bat`: greps de salidas `DW_M_DIM_` / `DW_M_FACT_` / `DW_M_INDICADOR_RESULTADO`.

## Evidencia

```bash
./switch-env.sh local
./init.sh   # → HARNESS OK
```

- Destino: `app@localhost:1524/BD_CURSOR` esquema APP
- `DW_M_FACT_INFORME_SUPERVISION` 53288, `DW_M_FACT_MULTA_COERCITIVA` 571, `DW_M_INDICADOR_RESULTADO` 585
- K1–K5 presentes

## Archivos clave

- `python/io/cargar_dw.py` — `TABLAS_LEGACY`, `_drop_legacy_tables`
- `python/main.py` — salidas / carga `DW_M_*`
- `docs/lineamientos/ddl/01_*.sql` … `04_*.sql`
- `init.sh`, `init.bat`
