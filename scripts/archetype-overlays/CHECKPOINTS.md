# CHECKPOINTS — arquetipo mínimo

Criterios para marcar features `done` en [`feature_list.json`](feature_list.json).  
Verificación: [`./init.sh`](init.sh).

---

## Global

- [ ] `./init.sh` termina con **`HARNESS OK`**.
- [ ] Sin passwords reales en `project-config.json` / `environments/`.
- [ ] Log sin literales `${VAR}`.
- [ ] Un solo `.py` en `logica/`.
- [ ] Máximo **una** feature `in_progress`.

---

## Fase 1 — Entorno {#fase-1}

- [ ] H2 levanta en puerto 9092 (`reset_and_create.sh`).
- [ ] `python/create_stg.py` OK (puede ser no-op con `sources: []`).
- [ ] `python/main.py` OK con `logica/demo.py`.
- [ ] `wf_main.hwf` ejecutable en Hop GUI.

---

## Fase 2 — Fuentes STG {#fase-2}

- [ ] Al menos una fuente en `inputs.yaml`.
- [ ] Tabla `STG_*` creada en H2.
- [ ] Pipeline `pl_stage_*.hpl` cableado en `wf_main.hwf`.
- [ ] Hop carga filas en STG (conteo > 0 en log).

Ver skill `hop-python-etl` e [`inputs.example.yaml`](.agents/skills/hop-python-etl/inputs.example.yaml).

---

## Fase 3 — Lógica {#fase-3}

- [ ] Claves STG en `python/io/leer_h2.py`.
- [ ] `logica/<tu_logica>.py` produce `RESULTADO` con filas > 0.
- [ ] `output/resultado.xlsx` generado (si se usa salida Excel).

Contrato: [`python/CONTRATO.md`](python/CONTRATO.md).

---

## Fuera de alcance del arquetipo base

- Modelo dimensional Oracle (`cargar_dw.py`) → copiar desde repo OEFA.
- Indicadores K1–K5 → skill `phased-dwh-lineamiento`.
