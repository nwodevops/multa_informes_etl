# Zona de pegado de logica (capa post-staging). Fuera de python/.

- En la raiz de `logica/` hay **un solo** `.py`: `ejecutar.py`. `python/main.py` lo auto-descubre.
- El negocio de fase 1 vive en el paquete `fase1/` (no cuenta para el auto-descubrimiento).
  - `constantes.py` — llaves candidatas e `ID_CORRIDA`
  - `consolidar.py` — `INT_*` (UNION, sin filtrar)
  - `diagnostico.py` — `QA_CORRIDA` / `QA_EXCEPCION`
  - `pipeline.py` — orquesta a + c
- Entrada: DataFrames de `LECTURAS`. Salida: `RESULTADO` + `INT_*` + `QA_*`.
- No abrir conexiones aqui. No filtrar el landing `INT_`.
