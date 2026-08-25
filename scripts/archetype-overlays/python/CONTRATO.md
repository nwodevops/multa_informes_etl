# Contrato logica/ (arquetipo mínimo)

## Flujo

```
python/main.py
  → io/leer_h2.py     (H2 → DataFrames)
  → logica/*.py       (un solo archivo)
  → io/escribir_excel.py
```

## Entrada

DataFrames con nombres = claves de `LECTURAS` en `python/io/leer_h2.py`.

Demo: `DEMO` ← `PUBLIC.DEMO_TABLA_EJEMPLO`.

## Salida obligatoria

| Nombre | Descripción |
|---|---|
| `RESULTADO` | DataFrame principal (default `SALIDA_DF` en main.py) |

Salidas opcionales reconocidas por main: prefijos `INT_`, `QA_`, `PROF_`, `DF_`.

## Reglas

- Un solo `.py` en `logica/`.
- Sin conexiones ni drivers en `logica/` (I/O en `python/io/`).
- `pandas` inyectado como `pd`.

Plantilla: `python/plantilla_logica.py`.
