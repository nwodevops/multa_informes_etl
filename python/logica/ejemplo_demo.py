# =============================================================================
# logica/ejemplo_demo.py  --  EJEMPLO de logica (reemplazar por tu logica)
#
# Zona de pegado: este es el UNICO .py de python/logica/ al copiar el arquetipo.
# Para un ETL nuevo, borrar/reemplazar este archivo por <tu_logica>.py
# (recuerda: un solo .py en esta carpeta; ver LEEME.md y python/CONTRATO.md).
#
# Entrada: DataFrames con los nombres de LECTURAS en python/io/leer_h2.py (aqui: DEMO).
# Salida : DataFrame RESULTADO (SALIDA_DF en main.py).
# Aislamiento: sin conexiones, jars ni drivers dentro de esta carpeta. Solo pandas.
# =============================================================================

RESULTADO = DEMO[["ID", "TXNOMBRE", "FEALTA"]].copy()
RESULTADO["FEALTA"] = pd.to_datetime(RESULTADO["FEALTA"]).dt.date
