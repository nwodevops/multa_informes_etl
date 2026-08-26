# impl_fase-7-indicadores — regresión «tabla vacía»

**Fecha:** 2026-08-19  
**Feature:** `fase-7-indicadores` (`in_progress`)  
**Reporte:** wf_main terminó OK; log muestra `MI_INDICADOR_RESULTADO: 585 -> 585 (OK)` pero usuario ve tabla vacía.

## Diagnóstico

### 1. Verificación directa (misma conexión que `cargar_dw.py`)

```
Destino: app@localhost:1524/BD_CURSOR  esquema APP
APP.MI_INDICADOR_RESULTADO: 585 filas
APP.MI_FACT_MULTA_COERCITIVA: 571 filas
Indicadores: K1, K2, K3, K4, K5 presentes
```

**Conclusión:** la carga Python **sí persiste** los datos. No hay bug de TRUNCATE sin INSERT ni de commit.

### 2. Causa probable del «vacío» en el cliente SQL

| Síntoma | Causa habitual |
|---|---|
| Log Hop OK, SQL vacío | Cliente SQL apunta a **otra instancia** (p. ej. puerto 1521 XE vs **1524** BD_CURSOR) |
| Solo INDICADOR vacío | Consulta sin prefijo `APP.` y existe homónimo vacío en otro esquema (no aplica aquí: solo existe APP) |
| Power BI vacío | Conexión distinta o modelo importado desactualizado |

### 3. Conexión correcta (local)

Desde `project-config.json` / `environments/local.json`:

- Host: `localhost`
- Puerto: **1524** (no 1521)
- Service: `BD_CURSOR`
- Usuario: `app`

Consulta de control:

```sql
SELECT COUNT(*) FROM APP.MI_INDICADOR_RESULTADO;
SELECT COD_INDICADOR, COUNT(*) FROM APP.MI_INDICADOR_RESULTADO GROUP BY COD_INDICADOR;
```

## Cambios en repo

| Archivo | Cambio |
|---|---|
| `feature_list.json` | Fase 7 reabierta `in_progress` |
| `python/io/cargar_dw.py` | Log `DW: destino ...` + `POST-CARGA` + SQL de verificación |
| `python/verify_dw.py` | Script standalone para conteos DW |

## Verificación post-fix

```bash
.venv/bin/python python/verify_dw.py
./init.sh   # debe terminar HARNESS OK
```

En el log de Hop debe aparecer ahora:

```
DW: destino app@localhost:1524/BD_CURSOR esquema APP
DW: POST-CARGA APP.MI_INDICADOR_RESULTADO = 585 filas (esperado 585)
DW: indicadores presentes: K1, K2, K3, K4, K5
```

## Cierre (2026-08-19 21:57)

- [x] wf_main OK: POST-CARGA APP.MI_INDICADOR_RESULTADO = 585, K1–K5.
- [x] `fase-7-indicadores` → `done` en `feature_list.json`.
