# impl_fase-rename-dw

**Fecha:** 2026-08-25  
**Feature:** `fase-rename-dw` → `done`

## Qué se hizo

- Prefijo `MI_` en 11 tablas DW (DIM/FACT/DET/DQ/INDICADOR) en DDL, Python (`pipeline`, `cargar_dw`, `verify_dw`, `main`) y docs.
- Migración local: DROP tablas legacy sin `MI_` (`CASCADE CONSTRAINTS`) para evitar `ORA-02264`.
- Constraints restantes renombrados a `PK_MI_*` / `UQ_MI_*` / `FK_MI_*` / `CK_MI_*`.
- `main.py`: `_es_salida` y `tablas_dw` reconocen prefijos `MI_*`.
- `init.sh` / `init.bat`: greps de salidas `MI_DIM_` / `MI_FACT_` / `MI_INDICADOR_RESULTADO`.

## Evidencia

```bash
./switch-env.sh local
./init.sh   # → HARNESS OK
```

- Destino: `app@localhost:1524/BD_CURSOR` esquema APP
- `MI_FACT_INFORME_SUPERVISION` 53288, `MI_FACT_MULTA_COERCITIVA` 571, `MI_INDICADOR_RESULTADO` 585
- K1–K5 presentes

## Archivos clave

- `python/io/cargar_dw.py` — `TABLAS_LEGACY`, `_drop_legacy_tables`
- `python/main.py` — salidas / carga `MI_*`
- `docs/lineamientos/ddl/01_*.sql` … `04_*.sql`
- `init.sh`, `init.bat`
