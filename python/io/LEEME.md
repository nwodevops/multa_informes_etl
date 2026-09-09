# python/io/ — I/O de la capa post-staging

Hop ya cargó `STG_*`. Aquí solo se lee H2 y se escribe el destino.

- `leer_h2.py` — `LECTURAS` (contrato de entrada de `logica/` en la raíz)
- `cargar_dw.py` — wipe + DDL canónico + INSERT Oracle DW (`MI_*` / vistas `VW_MC_*`)

No crear `STG_*`. No introspectar Oracle/Excel/Sheets. Eso es `python/introspect/` vía `create_stg.py`.

No importar este paquete como `import io`: choca con la stdlib. `main.py` carga estos módulos por ruta.
