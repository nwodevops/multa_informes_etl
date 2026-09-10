# CHECKPOINTS — estado final correcto

Criterios unificados para marcar una feature como `done` en [`feature_list.json`](feature_list.json).  
Verificación ejecutable: [`./init.sh`](init.sh) (Linux) / `init.bat` (Windows) + checklist de la fase.

Referencia canónica: [`docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md`](docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md).  
Contrato runtime: [`python/CONTRATO.md`](python/CONTRATO.md).

**Oracle canónico (runtime):** dims + 3 facts evidencia + DET + `DW_M_FACT_MULTA_COERCITIVA` (enrich `07`) + `DW_M_DQ_HALLAZGO` + `DW_M_AUD_*`.  
**No se publican:** `DW_M_QA_*`, `DW_M_INDICADOR_*` (K1–K5 solo memoria), vistas `VW_MC_*` / `VW_FCT_*`.

---

## Global (todas las fases)

- [ ] `./init.sh` termina con código 0 y mensaje `HARNESS OK` (Linux local).
- [ ] Ningún password real en archivos trackeados (`project-config.json`, `environments/*.json`).
- [ ] Log de Hop/Python sin literales `${VAR}` (variable no resuelta).
- [ ] Un solo `.py` en `logica/` (auto-descubierto por `python/main.py`).
- [ ] Como máximo **una** feature `in_progress` en `feature_list.json`.

---

## Fase 1 — Entorno {#fase-1}

- [ ] `./h2/scripts/reset_and_create.sh` levanta H2 en puerto 9092.
- [ ] `.venv/bin/python python/create_stg.py` crea tablas `STG_*` desde `inputs.yaml`.
- [ ] `workflows/wf_main.hwf` ejecutable en Hop GUI (proyecto = nombre de carpeta).
- [ ] `python/main.py` invocable desde Hop o shell.

---

## Fase 2 — Perfilamiento y diccionario {#fase-2}

- [ ] Salidas `PROF_RESUMEN`, `PROF_HALLAZGO`, `DICCIONARIO` con filas > 0.
- [ ] Campos de las fuentes de multa (F1, F2, F5) documentados; evidencia H1–H9 en hallazgos.

Módulo: `logica/dwh/perfilamiento.py`, `logica/dwh/diccionario.py`.

---

## Fase 3 — Homologación e integración {#fase-3}

- [ ] Universos tipificados: CSEP / OD / SISUD (+ etapas) en memoria (`integracion.py`).
- [ ] Columna `FUENTE_ORIGEN` en multas integradas; molde `COLS_MULTAS` (incluye attrs F2: `JEFE`, `UF`, …).
- [ ] Cero errores de coerción no capturados en log.

Módulos: `logica/dwh/homologacion.py`, `logica/dwh/integracion.py`.

---

## Fase 4 — Calidad {#fase-4}

- [ ] `FG_CONFORME` en dataframes; reglas R01–R05 aplicadas.
- [ ] `DW_M_DQ_HALLAZGO` **publicado en Oracle** (cuarentena blanda: no se eliminan filas).
- [ ] `DW_M_QA_AMARRE` + `DW_M_QA_AMARRE_DETALLE` calculados en la corrida (memoria / log); **no** se publican a Oracle. Puente Sheets↔SISUD: `RES_MONTO_Sheets_vs_SISUD`.

Módulo: `logica/dwh/calidad.py`. Skill: `.agents/skills/auditable-soft-quarantine/`.

---

## Fase 5 — Modelo dimensional {#fase-5}

- [ ] Ocho `DW_M_DIM_*` (incluye `DW_M_DIM_OD`, `DW_M_DIM_FUENTE_REGISTRO`).
- [ ] **Tres facts evidencia:** `DW_M_FACT_MC_CSEP`, `DW_M_FACT_MC_OD`, `DW_M_FACT_MC_SISUD` + `DW_M_DET_ETAPA_MC`.
- [ ] `DW_M_FACT_MULTA_COERCITIVA` vacío en Python (lo llena Oracle SQL `07`).
- [ ] Linaje por `ID_FUENTE`; `ID_TIEMPO_FIRMA` poblado; attrs operativos F2 en CSEP/enriquecida.
- [ ] `DW_M_DIM_ORGANO_UNIDAD` solo CSEP+ND (~11); miembro `-1` en dims.

Módulo: `logica/dwh/dimensional.py`. Manual: `docs/lineamientos/extra/manual-como-se-arma-el-fact.md`.

---

## Fase 6 — Carga Oracle {#fase-6}

- [ ] Wipe canónico `DW_M_*` / `VW_*` → DDL `01`+`02` + `DW_M_DQ_HALLAZGO` (03 filtrado) (+`05`) → INSERT → enrich `07` → `DW_M_AUD_*`.
- [ ] **Sin** `04_indicadores` / `06_vistas` en runtime; sin vistas `VW_MC_*` en destino.
- [ ] Tras insert evidencia: `07_enrich_sheets_sisud.sql` → enriquecida COUNT = CSEP + OD.
- [ ] Log `DW: <tabla>: N filas -> N en BD (OK)` para dims/facts/DET/DQ.
- [ ] `DW_M_AUD_*` alineados a STG (F1/F2/F5); `python/verify_dw.py` OK.

Módulo: `python/io/cargar_dw.py` + `python/audit/cargar_aud.py`. Skill: `.agents/skills/oracle-cargar-dw/`.

---

## Fase 7 — Indicadores {#fase-7}

- [ ] K1–K5 calculados en `logica/dwh/indicadores.py` y visibles como salida `DW_M_INDICADOR_RESULTADO` **en el log** (memoria de corrida).
- [ ] **No** hay tabla `DW_M_INDICADOR_RESULTADO` en Oracle tras la carga.
- [ ] Segunda corrida con mismo staging → mismos valores en memoria / `RESULTADO`.

Módulo: `logica/dwh/indicadores.py`. Doc: `docs/lineamientos/implementacion-fase-7.md`.

Consulta de calidad en Oracle (bitácora publicada):

```sql
SELECT REGLA_CODIGO, SEVERIDAD, COUNT(*)
FROM APP.DW_M_DQ_HALLAZGO
GROUP BY REGLA_CODIGO, SEVERIDAD
ORDER BY 1, 2;
```

---

## Qué no cubre init.sh

- Corrida GUI completa de `wf_main.hwf` (Hop visual).

Para smoke con datos reales: `./switch-env.sh local` y `./init.sh` (Oracle SISUD + Sheets + Hop obligatorios; **sin MySQL**), o Play `wf_main.hwf` en Hop.
