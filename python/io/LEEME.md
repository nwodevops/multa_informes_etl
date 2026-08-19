# python/io/ — I/O de la capa post-staging

Hop ya cargó `STG_*`. Aquí solo se lee H2 y se escribe el destino.

- `leer_h2.py` — `LECTURAS` (contrato de entrada de `logica/` en la raíz)
- `escribir_excel.py` — `output/fase1.xlsx` (multi-hoja)
- `escribir_dw.py` — Oracle BD_CURSOR (`INT_` refresh, `QA_` append)
- `escribir_mysql.py` / `escribir_oracle.py` — no los llama `main.py` en fase 1
  (MySQL es fuente; REPOCSEP es legado)

No crear `STG_*`. No introspectar Oracle/MySQL/Excel. Eso es `python/introspect/` vía `create_stg.py`.

No importar este paquete como `import io`: choca con la stdlib. `main.py` carga estos módulos por ruta.
