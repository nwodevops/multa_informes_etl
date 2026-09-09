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
4. Carga Sheets F1/F2 + Excel DIC + Oracle SISUD vía Hop / scripts (**sin MySQL**).
5. Ejecuta `python/main.py` (Fases 2–7) y comprueba salidas PROF/DIM/FACT evidencia/QA/INDICADOR.
6. Si Oracle DW está configurado, valida entre otros:
   - K1–K5 presentes; sin F3 (`MI_FACT_INFORME_SUPERVISION` / `ID_INFORME`)
   - sin VARCHAR `FUENTE_REGISTRO` en el hecho; `ID_TIEMPO_FIRMA` presente
   - conteos mínimos por evidencia (`MI_FACT_MC_CSEP` / `_OD` / `_SISUD`)
   - `MI_FACT_MULTA_COERCITIVA` = enrich SQL `07` (Sheets←SISUD); ≈ CSEP+OD
   - `MI_DIM_ORGANO_UNIDAD` ≤ 20 (~11 CSEP+ND)
   - vistas `VW_MC_CSEP` / `VW_MC_OD` / `VW_MC_SISUD` / `VW_MC_ENRIQUECIDA`
   - `MI_QA_AMARRE` y `MI_QA_AMARRE_DETALLE` con filas (puente `RES_MONTO_Sheets_vs_SISUD`)

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
-- Evidencia por universo (no sumar como un solo censo)
SELECT COUNT(*) FROM APP.VW_MC_CSEP;
SELECT COUNT(*) FROM APP.VW_MC_OD;
SELECT COUNT(*) FROM APP.VW_MC_SISUD;
-- Negocio enriquecido (= CSEP + OD; CUM/CAM desde SISUD)
SELECT COUNT(*) FROM APP.VW_MC_ENRIQUECIDA;

SELECT fu.CODIGO, COUNT(*)
FROM APP.MI_FACT_MULTA_COERCITIVA f
JOIN APP.MI_DIM_FUENTE_REGISTRO fu ON fu.ID_FUENTE = f.ID_FUENTE
GROUP BY fu.CODIGO ORDER BY 1;

SELECT COD_INDICADOR, COUNT(*) FROM APP.MI_INDICADOR_RESULTADO
GROUP BY COD_INDICADOR ORDER BY 1;

-- Amarre H9 usable
SELECT PUENTE, LADO, COUNT(*) FROM APP.MI_QA_AMARRE_DETALLE
GROUP BY PUENTE, LADO ORDER BY 1, 2;

-- Attrs operativos F2 (ejemplo)
SELECT COD_MA, JEFE, UF, ETA_REG_PROY_MC, CUM, CAM
FROM APP.VW_MC_ENRIQUECIDA
WHERE N_RES_MC LIKE '%0153-2026%';
```

Volúmenes de referencia (corrida local 2026-09-08): evidencia CSEP **990**, OD **281**, SISUD **534**; enriquecida **1271** (=990+281); órgano 11; QA detalle ~1.8k.

## Manual — reproducibilidad

Dos corridas seguidas con el mismo staging H2 deben dar los mismos conteos y valores de indicadores (Fase 7).

## Lo que init.sh no sustituye

- Validación visual de pipelines Hop (mapeos, transforms).
- Auditoría de secretos en git (revisar antes de commit).
