# Audit Oracle — foto cruda (fuera de estrella)

Tablas `MI_AUD_*` en BD_CURSOR / REPOCSEP: copia 1:1 de staging H2, columnas VARCHAR.

| Tabla | Origen STG | Fuente |
|---|---|---|
| `MI_AUD_F1_OD_MULTAS` | `STG_GS2_OD_MULTAS` (`GS2`) | Sheets F1 |
| `MI_AUD_F2_CSEP_MULTAS` | `STG_GS1_CSEP_MULTAS` (`GS1`) | Sheets F2 |
| `MI_AUD_F2_CSEP_ETAPAS` | `STG_GS1_ETAPAS` (`ETAPAS`) | Sheets F2 etapas |
| `MI_AUD_F5_SISUD_VW` | `STG_ORA_VW_MULTA_COERCITIVA` (`ORA`) | Vista F5 |

Runtime: `python/audit/cargar_aud.py` (CREATE dinámico). No forma parte del wipe DDL `01`/`02`;
se regeneran **después** de `cargar_dw` (el wipe canónico borra todo `MI_%` y luego AUD se recrea).

No usar en KPIs ni enrich `07`. Solo auditoría de “qué se bajó”.
