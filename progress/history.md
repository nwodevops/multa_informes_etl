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
