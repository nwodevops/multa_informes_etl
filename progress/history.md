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

- Smoke: `INDICADOR_RESULTADO` ~585 filas en Oracle; segunda corrida reproducible.
- Docs: `docs/lineamientos/implementacion-fase-*.md`, `docs/fase1-3/status.md`.

**Siguiente feature pendiente:** `fase-8-powerbi` (Power BI; validación manual).

---

## 2026-08-19 — Fase 7 cerrada (regresión INDICADOR_RESULTADO)

**Feature:** `fase-7-indicadores` → `done`

**Evidencia wf_main (21:57):**

- `INDICADOR_RESULTADO: 585 filas -> 585 en BD (OK)`
- POST-CARGA APP.INDICADOR_RESULTADO = 585; K1–K5 presentes
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

**Evidencia:** `./init.sh` → **HARNESS OK** (585 filas `INDICADOR_RESULTADO`, K1–K5).

**Siguiente:** `fase-8-powerbi` (`pending`).
