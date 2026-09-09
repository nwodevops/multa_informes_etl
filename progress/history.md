# Bitácora harness (append-only)

Registro de sesiones y features cerradas. No editar entradas pasadas.

---

## 2026-08-19 — Harness instalado; Fases 1–7 completadas

**Contexto:** Lineamiento PROPUESTA_ADAPTADA_ETL en rama `fase-1-lineamiento`.

**Entregado antes del harness:**

- Fases 2–4: perfil, homologación, calidad (`logica/dwh/`).
- Fases 5–6: modelo dimensional + carga Oracle (`dimensional.py`, `cargar_dw.py`).
- Fase 7: indicadores K1–K5 (`indicadores.py`, `ddl/04_indicadores.sql`).

**Evidencia:**

- Smoke: `MI_INDICADOR_RESULTADO` ~585 filas en Oracle; segunda corrida reproducible.
- Docs: `docs/lineamientos/implementacion-fase-*.md`, `docs/fase1-3/status.md`.

**Siguiente feature pendiente:** `fase-8-powerbi` (Power BI; validación manual).

---

## 2026-08-19 — Fase 7 cerrada (regresión MI_INDICADOR_RESULTADO)

**Feature:** `fase-7-indicadores` → `done`

**Evidencia wf_main (21:57):**

- `MI_INDICADOR_RESULTADO: 585 filas -> 585 en BD (OK)`
- POST-CARGA APP.MI_INDICADOR_RESULTADO = 585; K1–K5 presentes
- Destino: `app@localhost:1524/BD_CURSOR` esquema APP

**Notas:** Regresión «tabla vacía» resuelta — cliente SQL debe usar puerto **1524** (ver `impl_fase-7-indicadores.md`).

**Siguiente:** `fase-8-powerbi` (`pending`).

---

## 2026-08-25 — Staging directo sin wrappers

**Feature:** `infra-staging-directo` → `done`

**Cambios:**

- Eliminados `stage_if_configured.sh` y `should_stage_external.py`.
- `wf_main.hwf`: staging Oracle/Informes/MySQL como actions PIPELINE nativos.
- `init.sh`: `hop-run` directo; verificación Oracle DW obligatoria.
- Python: `require_live_conn()` en lugar de skips placeholder.
- `environments/remote.json` rellenado; `project-config.json` = local vía `./switch-env.sh local`.
- Plantillas `environments/*.example.json`; secretos en `.gitignore`.

**Evidencia:** `./init.sh` → **HARNESS OK** (585 filas `MI_INDICADOR_RESULTADO`, K1–K5).

**Siguiente:** `fase-8-powerbi` (`pending`).

---

## 2026-08-25 — Fase 8 cancelada (fuera de alcance)

**Feature:** `fase-8-powerbi` — **eliminada** del backlog (Power BI no se realizará).

**Cambios:**

- Quitada de `feature_list.json`.
- CHECKPOINTS / verification / status / docs de avance actualizados.
- Nota en `PROPUESTA_ADAPTADA_ETL.md` (sección Fase 8): fuera de alcance en esta implementación.

**Siguiente:** continuar `fase-rename-dw` (`in_progress`) si aplica; lineamiento Fases 1–7 cerrado.

---

## 2026-08-25 — Rename DW MI_ cerrado

**Feature:** `fase-rename-dw` → `done`

**Cambios:**

- DROP legacy sin `MI_` + constraints renombrados (fix `ORA-02264`).
- `main.py` exporta/carga `MI_DIM_*` / `MI_FACT_*` / `MI_DQ_*`.
- `init.sh` greps alineados; evidencia Linux: **HARNESS OK**.

**Evidencia:** [`progress/impl_fase-rename-dw.md`](impl_fase-rename-dw.md) — 53288 informes, 571 multas, 585 indicadores, K1–K5.

**Siguiente:** backlog harness vacío (Fase 8 fuera de alcance).

---

## 2026-09-02 — DW solo Multas (F3 fuera)

**Feature:** `dw-solo-multas` → `done`

**Cambios:**

- F3 (`CSEP_INFORMES_VIEW`) fuera de Hop, H2, Python, Kimball y Oracle.
- Estrella única: `MI_FACT_MULTA_COERCITIVA` + `MI_DET_ETAPA_MC`. K1 solo `N_MULTAS`.
- Esquema vivo: DROP tabla informe, FK e `ID_INFORME`.

**Evidencia:** [`progress/impl_dw-solo-multas.md`](impl_dw-solo-multas.md) — `./init.sh` → **HARNESS OK**; 571 multas, 152 indicadores; hecho informe inexistente.

**Siguiente:** backlog harness vacío (Fase 8 fuera de alcance).

## 2026-09-06 — mejoras Kimball 2–7

- Vistas VW_MC_*, MI_QA_AMARRE(+DETALLE), DROP FUENTE_REGISTRO, ID_TIEMPO_FIRMA, alertas conteo init.sh, anti-patrones en guía.
- ./init.sh → HARNESS OK (QA detalle 3078; órgano 11; sin VARCHAR FUENTE_REGISTRO).
- Evidencia: progress/impl_mejoras-kimball-2-7.md

## 2026-09-06 — docs alineados al DW post backlog 2–7

- Actualizados verification, CHECKPOINTS, arquitectura, fase1-3/status, ddl/README, implementacion-fase-4/5-6/7, inputs, fuentes_datos, ANEXO, PROPUESTA (fila estado), CONTRATO, LEEME, skills.
- Punto de verdad de lectura: docs/adjuntos/guia-leer-modelo-dimensional.md

## 2026-09-08 — facts evidencia + enrich Maggi

**Feature:** `facts-evidencia-enrich-sql` → `done`

- 3 facts evidencia + `07_enrich_sheets_sisud.sql`; caso 0153/64 con CUM/CAM tras backup SISUD 534 filas.
- Evidencia: `progress/impl_facts-evidencia-enrich-sql.md`

**Siguiente:** `fact-attrs-operativos-sheet` (P0 JEFE/UF/etapas).

## 2026-09-08 — attrs operativos Sheet (inicio)

**Feature:** `fact-attrs-operativos-sheet` → `in_progress`

- DDL + COLS + dimensional + 07 + `_ensure_fact_attrs_operativos`.
- Pendiente: corrida `wf_main` / `./init.sh` y check JEFE=MEJIA, HOMERO.
