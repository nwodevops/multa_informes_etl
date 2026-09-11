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

- Smoke: `DW_M_INDICADOR_RESULTADO` ~585 filas en Oracle; segunda corrida reproducible.
- Docs: `docs/lineamientos/implementacion-fase-*.md`, `docs/fase1-3/status.md`.

**Siguiente feature pendiente:** `fase-8-powerbi` (Power BI; validación manual).

---

## 2026-08-19 — Fase 7 cerrada (regresión DW_M_INDICADOR_RESULTADO)

**Feature:** `fase-7-indicadores` → `done`

**Evidencia wf_main (21:57):**

- `DW_M_INDICADOR_RESULTADO: 585 filas -> 585 en BD (OK)`
- POST-CARGA APP.DW_M_INDICADOR_RESULTADO = 585; K1–K5 presentes
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

**Evidencia:** `./init.sh` → **HARNESS OK** (585 filas `DW_M_INDICADOR_RESULTADO`, K1–K5).

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

## 2026-08-25 — Rename DW DW_M_ cerrado

**Feature:** `fase-rename-dw` → `done`

**Cambios:**

- DROP legacy sin `DW_M_` + constraints renombrados (fix `ORA-02264`).
- `main.py` exporta/carga `DW_M_DIM_*` / `DW_M_FACT_*` / `DW_M_DQ_*`.
- `init.sh` greps alineados; evidencia Linux: **HARNESS OK**.

**Evidencia:** [`progress/impl_fase-rename-dw.md`](impl_fase-rename-dw.md) — 53288 informes, 571 multas, 585 indicadores, K1–K5.

**Siguiente:** backlog harness vacío (Fase 8 fuera de alcance).

---

## 2026-08-26 — Windows remote + docs reorg

**Rama:** `windows`

**Features done:**

- `docs-reorg` — `docs/fases/`, `docs/credenciales/`, `docs/vista-general.md`, `docs/modelo-kimball.md`, índice `docs/README.md`
- `fix-dw-schema-user` — `cargar_dw.py` / `verify_dw.py` usan Oracle USER (evita ORA-00942 APP vs REPOCSEP)
- `fase-win-compat` (refuerzo) — `init.bat` log `output/init_win_*.log`, Hop `D:\Eder\hop`, workflows Win usan `.venv`

**Feature in_progress:** `fase-remote-deploy` — lógica Win OK (~53k informes); falta re-corrida post schema-fix → HARNESS OK / Success DW.

**Comandos Win:** `.\switch-env.ps1 remote` + Hop `wf_main_win.hwf` o `init.bat`

---

## 2026-08-26 — Rama windows limpia (exclusiva Win)

**Hecho:**

- `python/io`: solo `leer_h2.py` + `cargar_dw.py` (borrados `escribir_*` legacy).
- `AGENTS.md` / `feature_list.json`: rama marcada Windows-exclusive; verificación = `init.bat` / `wf_main_win`.
- Feature `python-io-cleanup` → done.
- `fase-remote-deploy` sigue `in_progress` (re-corrida Win pendiente).

**Uso:** solo Windows. Linux → `main`.

---

## 2026-09-02 — DW solo Multas (F3 fuera)

**Feature:** `dw-solo-multas` → `done`

**Cambios:**

- F3 (`CSEP_INFORMES_VIEW`) fuera de Hop, H2, Python, Kimball y Oracle.
- Estrella única: `DW_M_FACT_MULTA_COERCITIVA` + `DW_M_DET_ETAPA_MC`. K1 solo `N_MULTAS`.
- Esquema vivo: DROP tabla informe, FK e `ID_INFORME`.

**Evidencia:** [`progress/impl_dw-solo-multas.md`](impl_dw-solo-multas.md) — `./init.sh` → **HARNESS OK**; 571 multas, 152 indicadores; hecho informe inexistente.

**Siguiente:** backlog harness vacío (Fase 8 fuera de alcance).

## 2026-09-06 — mejoras Kimball 2–7

- Vistas VW_MC_*, DW_M_QA_AMARRE(+DETALLE), DROP FUENTE_REGISTRO, ID_TIEMPO_FIRMA, alertas conteo init.sh, anti-patrones en guía.
- ./init.sh → HARNESS OK (QA detalle 3078; órgano 11; sin VARCHAR FUENTE_REGISTRO).
- Evidencia: progress/impl_mejoras-kimball-2-7.md

## 2026-09-06 — docs alineados al DW post backlog 2–7

- Actualizados verification, CHECKPOINTS, arquitectura, fase1-3/status, ddl/README, implementacion-fase-4/5-6/7, inputs, fuentes_datos, ANEXO, PROPUESTA (fila estado), CONTRATO, LEEME, skills.
- Punto de verdad de lectura: docs/modelo-kimball.md

## 2026-09-08 — facts evidencia + enrich Maggi

**Feature:** `facts-evidencia-enrich-sql` → `done`

- 3 facts evidencia + `07_enrich_sheets_sisud.sql`; caso 0153/64 con CUM/CAM tras backup SISUD 534 filas.
- Evidencia: `progress/impl_facts-evidencia-enrich-sql.md`

**Siguiente:** `fact-attrs-operativos-sheet` (P0 JEFE/UF/etapas).

## 2026-09-08 — attrs operativos Sheet (inicio)

**Feature:** `fact-attrs-operativos-sheet` → `in_progress`

- DDL + COLS + dimensional + 07 + `_ensure_fact_attrs_operativos`.
- Pendiente: corrida `wf_main` / `./init.sh` y check JEFE=MEJIA, HOMERO.

---

## 2026-09-08 — merge linux→windows (facts evidencia + wipe canónico)

**Feature:** `fase-remote-deploy` → `in_progress` (re-validar en PC Win)

- Trae `60673a1` + `a960432` desde linux.
- Conserva `stage_sheets.py` / `stage_*.cmd` / `wf_main_win.hwf`.
- `cargar_dw` canónico (wipe+DDL); attrs Sheet done en feature_list.

---

## 2026-09-11 — canónico flaco enrich pandas (`linux_v2`)

**Feature:** `canonico-flaco-enrich-py` → `done`

- `DW_M_FACT_MULTA_COERCITIVA` = F1∪F2 + lookup SISUD en `logica/dwh/enrich.py`.
- Oracle sin `DW_M_FACT_MC_*`. DET FK al enriquecido. SQL 07 deprecado.
- `./init.sh` → HARNESS OK: 1271 = 990+281; 0153/64 con CUM+CAM.
- Evidencia: `progress/impl_canonico-flaco-enrich-py.md`
- Siguiente: rama `windows_v2` + re-corrida Win.
