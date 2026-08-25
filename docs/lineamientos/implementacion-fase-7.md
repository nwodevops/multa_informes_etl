# Implementación lineamientos — Fase 7

Referencia: [`PROPUESTA_ADAPTADA_ETL.md`](PROPUESTA_ADAPTADA_ETL.md) secciones 5 y 6 (Fase 7).

## Código

| Módulo | Fase | Entregable |
|---|---|---|
| `logica/dwh/indicadores.py` | 7 | K1–K5 → `INDICADOR_RESULTADO` en memoria |
| `docs/lineamientos/ddl/04_indicadores.sql` | 7 | DDL Oracle |
| `python/io/cargar_dw.py` | 6–7 | TRUNCATE+INSERT incluye indicadores |
| `logica/dwh/pipeline.py` | 2–7 | Orquestación extendida |

## Indicadores

| Código | Métrica(s) | Grano |
|---|---|---|
| K1 | `N_MULTAS`, `N_INFORMES` | `(ANIO, ID_ORGANO)` + fila `TOTAL` |
| K2 | `PROM_DIAS_NOTIF_FIRMA` | idem (solo casos con días válidos) |
| K3 | `RATIO_COBRANZA_SOLES`, `RATIO_COBRANZA_UIT` | idem (multas con resolución) |
| K4 | `TASA_VERIF_POST_MC` | idem |
| K5 | `PCT_CONFORME`, `PCT_AMARRE` | global / por regla R01–R05 / por puente H9 |

Entrada: hechos y dataframes post-calidad en memoria (no re-lectura Oracle).

## Criterio de avance

- Tabla `INDICADOR_RESULTADO` en BD_CURSOR con DDL formal (`04_indicadores.sql`).
- `COUNT(*)` Oracle = filas del DataFrame.
- Presencia de K1–K5; segunda corrida con mismo H2 → mismos `VALOR`/`NUMERADOR`/`DENOMINADOR`.

## Verificación

```bash
.venv/bin/python python/main.py
```

Consulta Oracle:

```sql
SELECT COD_INDICADOR, METRICA, COUNT(*)
FROM APP.INDICADOR_RESULTADO
GROUP BY COD_INDICADOR, METRICA
ORDER BY 1, 2;
```

## Pendiente (Fase 8)

- Conectar/validar Power BI contra `INDICADOR_RESULTADO` y tablas del modelo.
