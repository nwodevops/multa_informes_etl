# impl `fact-siete-campos`

Rama: `linux_v2`.

## Qué cambió

Siete datos al fact de negocio `DW_M_FACT_MULTA_COERCITIVA`. Sin AUX, sin pisar Sheet.

| Fact | Origen | Regla |
|---|---|---|
| `N_CARTA_DCG` | F1/F2 `N_CARTA_DCG` | Copiar |
| `DOC_SIGED_DESCARGOS` | F1/F2 `DOC_SIGED` | Rename; no mezclar con `SIGED` de cobranza |
| `F_VERIF_CAMPO` | F1/F2 `F_VERIF_CAMPO` | Distinta de `F_VERIF_POST_MC` |
| `MOTIVO_NO_AMERIT` | F1/F2 `MOTIVO_NO_AMERIT` | Copiar |
| `ID_ADMINISTRADO` | SISUD `ADMINISTRADO` | `_tomar_si_nd`: solo si la planilla quedó `-1` |
| `N_RES_SISUD` | SISUD `RESOLUCION` | Sombra; no pisa `N_RES_MC` |
| `MONTO_UIT_SISUD` | SISUD `MONTO_MULTA` | Sombra; no pisa `MONTO_UIT` |

Clave de match sin cambios (`norm(N_RES_MC)|MONTO_UIT`).

## Archivos

- `logica/dwh/integracion.py` — molde `COLS_MULTAS` + rename `DOC_SIGED`
- `logica/dwh/dimensional.py` — copia de los 4 de planilla en `_build_fact_multas`
- `logica/dwh/enrich.py` — `ID_ADMINISTRADO` si `-1`; sombras SISUD
- `docs/lineamientos/ddl/02_hechos.sql`, `05_comentarios.sql`
- `docs/adjunto/diccionario-fact.md`, `diccionario-fact-gmail.html`, `fuera-del-fact.md`
- `docs/lineamientos/ANEXO_MAPEO_CAMPOS.md`

## Verificación

Smoke unitario de `enriquecer_sheets_sisud`: sede central conserva `ID_ADMINISTRADO`; OD `-1` recibe SISUD; `N_RES_MC`/`MONTO_UIT` no se pisan.

Sin `./init.sh` en esta sesión. Las 6 columnas nuevas salen en el próximo wipe+DDL.
