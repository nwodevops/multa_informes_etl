# Verificación — cómo demostrar que funciona

## Automática (harness)

Desde la raíz del proyecto:

```bash
chmod +x init.sh   # una vez
./init.sh
.venv/bin/python python/verify_dw.py   # conteos Oracle (misma conexión que cargar_dw)
```

Debe terminar con **`HARNESS OK`**. El script:

1. Valida `feature_list.json` (máx. una `in_progress`).
2. Resetea H2 y aplica DDL (`reset_and_create.sh`).
3. Crea tablas STG (`python/create_stg.py`).
4. Carga Excel vía Hop (`pl_stage_excel.hpl`) si `hop-run` está disponible.
5. Carga Oracle/MySQL vía Hop directo (`pl_stage_oracle.hpl`, `pl_stage_mysql.hpl`).
6. Ejecuta `python/main.py` y comprueba salidas PROF/DIM/FACT/INDICADOR.
7. Si Oracle DW está configurado: cuenta filas y presencia K1–K5.

Criterios detallados: [`CHECKPOINTS.md`](../CHECKPOINTS.md).

## Manual — Hop GUI

1. Proyecto activo en Hop: nombre de carpeta del repo (p. ej. `etl_phyton_cursor`).
2. Play [`workflows/wf_main.hwf`](../workflows/wf_main.hwf).
3. Revisar log: sin `${VAR}` literal; pipelines `pl_stage_*` OK; Python Success.

## Manual — Oracle

Tras corrida con credenciales `DB_ORA_DW_*` (local: **puerto 1524**, service `BD_CURSOR`, usuario `app`):

```bash
.venv/bin/python python/verify_dw.py
```

Si el log Hop dice 585 filas pero tu cliente SQL muestra 0, casi siempre estás en **otra instancia** (p. ej. 1521). Usa la misma conexión que imprime `verify_dw.py`.

```sql
SELECT tabla, num_rows
FROM all_tables
WHERE owner = 'APP'
  AND table_name IN (
    'MI_FACT_MULTA_COERCITIVA',
    'MI_INDICADOR_RESULTADO', 'MI_DQ_HALLAZGO'
  );

SELECT COD_INDICADOR, COUNT(*) FROM APP.MI_INDICADOR_RESULTADO
GROUP BY COD_INDICADOR ORDER BY 1;
```

## Manual — reproducibilidad

Dos corridas seguidas con el mismo staging H2 deben dar los mismos conteos y valores de indicadores (Fase 7).

## Lo que init.sh no sustituye

- Validación visual de pipelines Hop (mapeos, transforms).
- Auditoría de secretos en git (revisar antes de commit).
