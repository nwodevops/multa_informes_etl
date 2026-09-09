# python/io/ — I/O de la capa post-staging

Hop ya cargó `STG_*`. Aquí solo se lee H2 y se escribe el destino dimensional.

- `leer_h2.py` — `LECTURAS` (contrato de entrada de `logica/` en la raíz)
- `cargar_dw.py` — wipe canónico `MI_*`/`VW_*` + DDL `01`+`02`(+`05`) + INSERT estrella + enrich `07`

Foto cruda audit: [`../audit/cargar_aud.py`](../audit/cargar_aud.py) (`MI_AUD_*`), llamado desde `main.py` tras `cargar_dw`.

No crear `STG_*`. No introspectar Oracle/Excel/Sheets. Eso es `python/introspect/` vía `create_stg.py`.

No importar este paquete como `import io`: choca con la stdlib. `main.py` carga estos módulos por ruta.
