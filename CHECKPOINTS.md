# CHECKPOINTS — estado final correcto

Criterios unificados para marcar una feature como `done` en [`feature_list.json`](feature_list.json).  
Verificación ejecutable: [`./init.sh`](init.sh) + checklist de la fase.

Referencia canónica: [`docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md`](docs/lineamientos/PROPUESTA_ADAPTADA_ETL.md).

---

## Global (todas las fases)

- [ ] `./init.sh` termina con código 0 y mensaje `HARNESS OK`.
- [ ] Ningún password real en archivos trackeados (`project-config.json`, `environments/*.json`).
- [ ] Log de Hop/Python sin literales `${VAR}` (variable no resuelta).
- [ ] Un solo `.py` en `logica/` (auto-descubierto por `python/main.py`).
- [ ] Como máximo **una** feature `in_progress` en `feature_list.json`.

---

## Fase 1 — Entorno {#fase-1}

- [ ] `./h2/scripts/reset_and_create.sh` levanta H2 en puerto 9092.
- [ ] `.venv/bin/python python/create_stg.py` crea tablas `STG_*` desde `inputs.yaml`.
- [ ] `workflows/wf_main.hwf` ejecutable en Hop GUI (proyecto `etl_cursor` o nombre de carpeta).
- [ ] `python/main.py` invocable desde Hop o shell.

---

## Fase 2 — Perfilamiento y diccionario {#fase-2}

- [ ] Salidas `PROF_RESUMEN`, `PROF_HALLAZGO`, `DICCIONARIO` con filas > 0.
- [ ] Campos de las 5 fuentes documentados; evidencia H1–H9 en hallazgos.

Módulo: `logica/dwh/perfilamiento.py`, `logica/dwh/diccionario.py`.

---

## Fase 3 — Homologación e integración {#fase-3}

- [ ] `DF_MULTAS`, `DF_INFORMES`, `DF_ETAPAS` tipificados en memoria.
- [ ] Columna `FUENTE_ORIGEN` en multas integradas.
- [ ] Cero errores de coerción no capturados en log.

Módulos: `logica/dwh/homologacion.py`, `logica/dwh/integracion.py`.

---

## Fase 4 — Calidad {#fase-4}

- [ ] `FG_CONFORME` en dataframes; reglas R01–R05 aplicadas.
- [ ] `DQ_HALLAZGO` append (cuarentena blanda: no se eliminan filas).
- [ ] `QA_AMARRE` con % puente H9 documentado.

Módulo: `logica/dwh/calidad.py`. Skill: `.agents/skills/auditable-soft-quarantine/`.

---

## Fase 5 — Modelo dimensional {#fase-5}

- [ ] Seis `DIM_*`, `FACT_MULTA_COERCITIVA`, `FACT_INFORME_SUPERVISION`, `DET_ETAPA_MC`.
- [ ] Miembro `-1` en dimensiones; ningún hecho con FK huérfana sin `-1`.

Módulo: `logica/dwh/dimensional.py`.

---

## Fase 6 — Carga Oracle {#fase-6}

- [ ] DDL formal aplicado (`docs/lineamientos/ddl/01`–`03`).
- [ ] Vistas legacy `VW_FCT_*` eliminadas si existían.
- [ ] Por cada tabla cargada: log `DW: <tabla>: N filas -> N en BD (OK)`.
- [ ] `COUNT(*)` Oracle = filas del DataFrame (excepto `DQ_HALLAZGO`: `>=`).

Módulo: `python/io/cargar_dw.py`. Skill: `.agents/skills/oracle-cargar-dw/`.

---

## Fase 7 — Indicadores {#fase-7}

- [ ] Tabla `INDICADOR_RESULTADO` con DDL `04_indicadores.sql`.
- [ ] Presencia de códigos K1, K2, K3, K4, K5.
- [ ] Segunda corrida con mismo staging → mismos `VALOR` / `NUMERADOR` / `DENOMINADOR`.
- [ ] Conteo típico de referencia: ~585 filas (depende del entorno de datos).

Módulo: `logica/dwh/indicadores.py`. Doc: `docs/lineamientos/implementacion-fase-7.md`.

Consulta Oracle:

```sql
SELECT COD_INDICADOR, METRICA, COUNT(*)
FROM APP.INDICADOR_RESULTADO
GROUP BY COD_INDICADOR, METRICA
ORDER BY 1, 2;
```

---

## Fase 8 — Power BI {#fase-8}

- [ ] `.pbix` conectado a Oracle BD_CURSOR (`oracle_dw` / `DB_ORA_DW_*`).
- [ ] Medidas/visualizaciones leen `INDICADOR_RESULTADO` y hechos validados.
- [ ] Validación manual documentada en `progress/impl_fase-8-powerbi.md`.

Fuera de la capa Python; no la cubre `./init.sh` completo.

---

## Qué no cubre init.sh

- Corrida GUI completa de `wf_main.hwf` (Hop visual).
- Validación Power BI (Fase 8).
- Staging Oracle/MySQL si credenciales son placeholders `<...>` (se omite con AVISO).

Para smoke con datos reales: `./init.sh` con Excel local + credenciales completas, o Play `wf_main.hwf` en Hop.
