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
4. Carga Sheets F1/F2 + Excel DIC + Oracle/MySQL vía Hop / scripts.
5. Ejecuta `python/main.py` (Fases 2–7) y comprueba salidas PROF/DIM/FACT/QA/INDICADOR.
6. Si Oracle DW está configurado, valida entre otros:
   - K1–K5 presentes; sin F3 (`MI_FACT_INFORME_SUPERVISION` / `ID_INFORME`)
   - sin VARCHAR `FUENTE_REGISTRO` en el hecho; `ID_TIEMPO_FIRMA` presente
   - conteos mínimos por fuente (`CAGR` / `OD_SHEETS` / `SISUD_VW`)
   - `MI_DIM_ORGANO_UNIDAD` ≤ 20 (~11 CSEP+ND)
   - vistas `VW_MC_CSEP` / `VW_MC_OD` / `VW_MC_SISUD`
   - `MI_QA_AMARRE` y `MI_QA_AMARRE_DETALLE` con filas

Criterios detallados: [`CHECKPOINTS.md`](../CHECKPOINTS.md).  
Modelo mental: [`adjuntos/guia-leer-modelo-dimensional.md`](adjuntos/guia-leer-modelo-dimensional.md).

## Manual — Hop GUI

1. Proyecto activo en Hop: nombre de carpeta del repo.
2. Play [`workflows/wf_main.hwf`](../workflows/wf_main.hwf).
3. Revisar log: sin `${VAR}` literal; pipelines `pl_stage_*` OK; Python Success.

## Manual — Oracle

Tras corrida con credenciales `DB_ORA_DW_*` (local: **puerto 1524**, service `BD_CURSOR`, usuario `app`):

```bash
.venv/bin/python python/verify_dw.py
```

Si el log Hop dice N filas pero tu cliente SQL muestra 0, casi siempre estás en **otra instancia** (p. ej. 1521). Usa la misma conexión que imprime `verify_dw.py`.

```sql
-- Universos (no sumar como uno solo)
SELECT COUNT(*) FROM APP.VW_MC_CSEP;
SELECT COUNT(*) FROM APP.VW_MC_OD;
SELECT COUNT(*) FROM APP.VW_MC_SISUD;

SELECT fu.CODIGO, COUNT(*)
FROM APP.MI_FACT_MULTA_COERCITIVA f
JOIN APP.MI_DIM_FUENTE_REGISTRO fu ON fu.ID_FUENTE = f.ID_FUENTE
GROUP BY fu.CODIGO ORDER BY 1;

SELECT COD_INDICADOR, COUNT(*) FROM APP.MI_INDICADOR_RESULTADO
GROUP BY COD_INDICADOR ORDER BY 1;

-- Amarre H9 usable
SELECT PUENTE, LADO, COUNT(*) FROM APP.MI_QA_AMARRE_DETALLE
GROUP BY PUENTE, LADO ORDER BY 1, 2;
```

Volúmenes de referencia (corrida local típica): hecho ~1801; CAGR ~986; SISUD ~530; OD ~281; órgano 11; QA detalle ~3k.

## Manual — reproducibilidad

Dos corridas seguidas con el mismo staging H2 deben dar los mismos conteos y valores de indicadores (Fase 7).

## Lo que init.sh no sustituye

- Validación visual de pipelines Hop (mapeos, transforms).
- Auditoría de secretos en git (revisar antes de commit).
