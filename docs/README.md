# Docs — índice

Orden de lectura recomendado:

1. [`modelo-kimball.md`](modelo-kimball.md) — estrella DIM/FACT + evidencia / enriquecido  
2. [`arquitectura.md`](arquitectura.md) — detalle Hop + H2 + Python  
3. [`inputs/README.md`](inputs/README.md) — fuentes vigentes F1/F2/F5  
4. [`lineamientos/extra/manual-como-se-arma-el-fact.md`](lineamientos/extra/manual-como-se-arma-el-fact.md) — cómo se arma el FACT  
5. [`lineamientos/PROPUESTA_ADAPTADA_ETL.md`](lineamientos/PROPUESTA_ADAPTADA_ETL.md) — lineamiento canónico  
6. [`verification.md`](verification.md) — smoke (`init.sh` / `init.bat`)  
7. [`TDR REQ 3629-2026.pdf`](TDR%20REQ%203629-2026.pdf) — requerimiento  

> Guías de entrega / informe viven fuera del repo en `workspace_etl/adjuntos/` (no versionadas aquí).

## Mapa de carpetas

| Ruta | Contenido |
|---|---|
| [`modelo-kimball.md`](modelo-kimball.md) | Estrella Kimball + DET / DQ / KPI |
| [`arquitectura.md`](arquitectura.md) | Arquitectura técnica |
| [`verification.md`](verification.md) | Smoke / harness |
| [`glosario.md`](glosario.md) | Términos cortos |
| [`inputs/`](inputs/) | Inventario runtime + catálogos Sheets |
| [`fases/`](fases/) | Status por fase |
| [`harness/`](harness/) | Roles y plataforma Hop/H2 |
| [`lineamientos/`](lineamientos/) | Propuesta, implementación F2–F7, DDL, anexos |
| [`lineamientos/ddl/`](lineamientos/ddl/) | DDL Oracle `MI_*` (usado por `cargar_dw.py`) |
| [`lineamientos/extra/`](lineamientos/extra/) | Manual fact + inventario fuentes |
| [`credenciales/`](credenciales/) | Referencia humana local/remote (no secretos en git) |

## Fases y fuentes

- Status: [`fases/status.md`](fases/status.md)  
- Fuentes runtime: [`inputs/README.md`](inputs/README.md)  
- Fuentes detalle: [`lineamientos/extra/fuentes_datos/fuentes-detalle.md`](lineamientos/extra/fuentes_datos/fuentes-detalle.md)  
- Matriz correspondencia: [`lineamientos/extra/fuentes_datos/matriz-correspondencia.md`](lineamientos/extra/fuentes_datos/matriz-correspondencia.md)
