# Docs — índice

Orden de lectura recomendado:

1. [`vista-general.md`](vista-general.md) — flujo Fuentes → STG → Python → DW  
2. [`modelo-kimball.md`](modelo-kimball.md) — estrella DIM/FACT + tablas de apoyo  
3. [`TDR REQ 3629-2026.pdf`](TDR%20REQ%203629-2026.pdf) — requerimiento  
4. [`arquitectura.md`](arquitectura.md) — detalle Hop + H2 + Python  
5. [`lineamientos/PROPUESTA_ADAPTADA_ETL.md`](lineamientos/PROPUESTA_ADAPTADA_ETL.md) — lineamiento canónico  
6. [`verification.md`](verification.md) — cómo demostrar que funciona (`init.sh` / `init.bat`)

## Mapa de carpetas

| Ruta | Contenido |
|---|---|
| [`vista-general.md`](vista-general.md) | Flujo ETL resumido |
| [`modelo-kimball.md`](modelo-kimball.md) | Estrella Kimball + DET / DQ / KPI |
| [`arquitectura.md`](arquitectura.md) | Arquitectura técnica |
| [`verification.md`](verification.md) | Smoke / harness |
| [`glosario.md`](glosario.md) | Términos cortos |
| [`fases/`](fases/) | Status por fase + notas fase 1 |
| [`harness/`](harness/) | Roles y plataforma Hop/H2 |
| [`lineamientos/`](lineamientos/) | Propuesta, implementación F2–F7, DDL, anexos |
| [`lineamientos/ddl/`](lineamientos/ddl/) | DDL Oracle `MI_*` (usado por `cargar_dw.py`) |
| [`lineamientos/extra/fuentes_datos/`](lineamientos/extra/fuentes_datos/) | Inventario fuentes |
| [`credenciales/`](credenciales/) | Referencia humana local/remote (no secretos en git) |

## Fases y fuentes

- Status: [`fases/status.md`](fases/status.md)  
- Antes/durante fase 1: [`fases/antes-durante-fase1.md`](fases/antes-durante-fase1.md)  
- Fuentes detalle: [`lineamientos/extra/fuentes_datos/fuentes-detalle.md`](lineamientos/extra/fuentes_datos/fuentes-detalle.md)  
- Matriz correspondencia: [`lineamientos/extra/fuentes_datos/matriz-correspondencia.md`](lineamientos/extra/fuentes_datos/matriz-correspondencia.md)
