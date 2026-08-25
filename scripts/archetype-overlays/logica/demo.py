# Lógica demo — smoke del arquetipo

RESULTADO = DEMO[["ID", "TXNOMBRE", "FEALTA"]].copy()
RESULTADO["FEALTA"] = pd.to_datetime(RESULTADO["FEALTA"]).dt.date
