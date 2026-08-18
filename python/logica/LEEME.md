# Zona de pegado de logica Python

- Copia aqui **un solo** archivo `.py` con tu logica de negocio.
- `python/main.py` auto-descubre el unico `.py` de esta carpeta y lo ejecuta.
  Error si hay 0 o mas de 1 archivo.
- Entrada: DataFrames ya cargados (nombres = claves de `LECTURAS` en `python/io/leer_h2.py`).
- Salida: deja un DataFrame con el nombre `RESULTADO` (configurable en `main.py`, `SALIDA_DF`).
- No abrir conexiones/drivers aqui: el I/O vive en `python/io/`. `pandas` ya está inyectado.

Viene con un ejemplo (`ejemplo_demo.py`) para el smoke test. Al pegar tu lógica,
borra/reemplaza ese archivo (mantén un solo `.py`). Plantilla: `../plantilla_logica.py`.
