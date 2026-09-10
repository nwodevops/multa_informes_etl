# Verificación — cómo demostrar que funciona

## Automática (harness)

Desde la raíz del proyecto (rama **`linux`** local):

```bash
chmod +x init.sh   # una vez
./switch-env.sh local
./init.sh
.venv/bin/python python/verify_dw.py   # conteos Oracle (misma conexión que cargar_dw)
```

Debe terminar con **`HARNESS OK`**. El script:

1. Valida `feature_list.json` (máx. una `in_progress`).
2. Resetea H2 y aplica DDL (`reset_and_create.sh`).
3. Crea tablas `STG_*` (`python/create_stg.py`).
4. Carga Sheets F1/F2 + Excel DIC + Oracle SISUD vía Hop / scripts (**sin MySQL**).
5. Ejecuta `python/main.py` y comprueba salidas PROF/DIM/FACT evidencia + `DW_M_DQ_HALLAZGO` + INDICADOR (memoria).
6. Valida Oracle canónico:
   - hechos evidencia + enriquecida (= CSEP+OD); `ID_TIEMPO_FIRMA`; sin F3 / sin `FUENTE_REGISTRO` VARCHAR
   - `DW_M_DQ_HALLAZGO` presente; `DW_M_AUD_*` alineados a STG
   - **sin** `VW_MC_*`, **sin** `DW_M_QA_*`, **sin** `DW_M_INDICADOR_*` en Oracle
   - `DW_M_DIM_ORGANO_UNIDAD` ≤ 20 (~11 CSEP+ND)

Windows remoto: `.\switch-env.ps1 remote` + `init.bat` / `wf_main_win.hwf` → `python\verify_dw.py`.

Criterios: [`CHECKPOINTS.md`](../CHECKPOINTS.md).  
Modelo: [`modelo-kimball.md`](modelo-kimball.md).

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
SELECT COUNT(*) FROM APP.DW_M_FACT_MC_CSEP;
SELECT COUNT(*) FROM APP.DW_M_FACT_MC_OD;
SELECT COUNT(*) FROM APP.DW_M_FACT_MC_SISUD;
-- Negocio enriquecido (= CSEP + OD; CUM/CAM desde SISUD)
SELECT COUNT(*) FROM APP.DW_M_FACT_MULTA_COERCITIVA;

SELECT fu.CODIGO, COUNT(*)
FROM APP.DW_M_FACT_MULTA_COERCITIVA f
JOIN APP.DW_M_DIM_FUENTE_REGISTRO fu ON fu.ID_FUENTE = f.ID_FUENTE
GROUP BY fu.CODIGO ORDER BY 1;

-- Bitácora de calidad (publicada)
SELECT REGLA_CODIGO, COUNT(*) FROM APP.DW_M_DQ_HALLAZGO
GROUP BY REGLA_CODIGO ORDER BY 1;

-- Auditoría 1:1
SELECT COUNT(*) FROM APP.DW_M_AUD_F2_CSEP_MULTAS;
SELECT COUNT(*) FROM APP.DW_M_AUD_F1_OD_MULTAS;

-- Attrs operativos F2 (ejemplo)
SELECT COD_MA, JEFE, UF, ETA_REG_PROY_MC, CUM, CAM
FROM APP.DW_M_FACT_MULTA_COERCITIVA
WHERE N_RES_MC LIKE '%0153-2026%';
```

Volúmenes de referencia (corrida local): evidencia CSEP **≈990**, OD **≈281**, SISUD **≈534**; enriquecida **≈1271** (=990+281); órgano ~11.

## Manual — reproducibilidad

Dos corridas seguidas con el mismo staging H2 deben dar los mismos conteos de facts/AUD/DQ.

## Lo que init.sh no sustituye

- Validación visual de pipelines Hop (mapeos, transforms).
- Auditoría de secretos en git (revisar antes de commit).
