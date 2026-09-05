"""Catálogos de referencia (semillas ddl/01 + inventario de campos F1/F2/F4/F5)."""

from __future__ import annotations

# Semillas MI_DIM_ESTADO (ddl/01_dimensiones.sql) — pendiente aprobación CSEP
MI_DIM_ESTADO: list[tuple[str, str, str, str]] = [
    ("RESOLUCION", "ACTIVO", "Resolución activa", "VIGENTE"),
    ("RESOLUCION", "INACTIVO", "Resolución inactiva", "CERRADO"),
    ("MULTA", "ACTIVO", "Multa activa", "VIGENTE"),
    ("MULTA", "INACTIVO", "Multa inactiva", "CERRADO"),
    ("MULTA", "INCUMPLIDO", "No pagada / incumplida", "INCUMPLIDO"),
    ("PAGO", "PAGADO", "Multa pagada", "CUMPLIDO"),
    ("PAGO", "PENDIENTE", "Pago pendiente", "PENDIENTE"),
    ("PAGO", "EJECUCION_FORZOSA", "En ejecución forzosa", "INCUMPLIDO"),
    ("ETAPA", "TERMINADO", "Etapa terminada", "CUMPLIDO"),
    ("ETAPA", "PENDIENTE", "Etapa pendiente", "PENDIENTE"),
    ("DESCARGOS", "PRESENTO", "Presentó descargos", "CUMPLIDO"),
    ("DESCARGOS", "NO_PRESENTO", "No presentó descargos", "INCUMPLIDO"),
]

# UIT oficial MEF (ddl/01_dimensiones.sql)
MI_DIM_PARAMETRO_UIT: dict[int, float] = {
    2015: 3850.0,
    2016: 3950.0,
    2017: 4050.0,
    2018: 4150.0,
    2019: 4200.0,
    2020: 4300.0,
    2021: 4400.0,
    2022: 4600.0,
    2023: 4950.0,
    2024: 5150.0,
    2025: 5350.0,
}

# Oficinas desconcentradas F1 (Excel medidas administrativas). COD_OD = slug filename.
# ORDEN replica la lista fuente; CODE comparte 9 con HUANUCO (ID_OD surrogate evita choque).
ODS_OEFA: list[dict[str, str | int]] = [
    {"ORDEN": 1, "COD_OD": "AMAZONAS", "NOMBRE": "Amazonas", "TIPO": "OD"},
    {"ORDEN": 2, "COD_OD": "ANCASH", "NOMBRE": "Ancash", "TIPO": "OD"},
    {"ORDEN": 3, "COD_OD": "APURIMAC", "NOMBRE": "Apurimac", "TIPO": "OD"},
    {"ORDEN": 4, "COD_OD": "AREQUIPA", "NOMBRE": "Arequipa", "TIPO": "OD"},
    {"ORDEN": 5, "COD_OD": "AYACUCHO", "NOMBRE": "Ayacucho", "TIPO": "OD"},
    {"ORDEN": 6, "COD_OD": "CAJAMARCA", "NOMBRE": "Cajamarca", "TIPO": "OD"},
    {"ORDEN": 7, "COD_OD": "CUSCO", "NOMBRE": "Cusco", "TIPO": "OD"},
    {"ORDEN": 8, "COD_OD": "HUANCAVELICA", "NOMBRE": "Huancavelica", "TIPO": "OD"},
    {"ORDEN": 9, "COD_OD": "HUANUCO", "NOMBRE": "Huánuco", "TIPO": "OD"},
    {"ORDEN": 9, "COD_OD": "CODE", "NOMBRE": "CODE", "TIPO": "UNIDAD"},
    {"ORDEN": 10, "COD_OD": "ICA", "NOMBRE": "Ica", "TIPO": "OD"},
    {"ORDEN": 11, "COD_OD": "JUNIN", "NOMBRE": "Junin", "TIPO": "OD"},
    {"ORDEN": 12, "COD_OD": "LA_LIBERTAD", "NOMBRE": "La Libertad", "TIPO": "OD"},
    {"ORDEN": 13, "COD_OD": "LAMBAYEQUE", "NOMBRE": "Lambayeque", "TIPO": "OD"},
    {"ORDEN": 14, "COD_OD": "LORETO", "NOMBRE": "Loreto", "TIPO": "OD"},
    {"ORDEN": 15, "COD_OD": "MADRE_DE_DIOS", "NOMBRE": "Madre de Dios", "TIPO": "OD"},
    {"ORDEN": 16, "COD_OD": "MOQUEGUA", "NOMBRE": "Moquegua", "TIPO": "OD"},
    {"ORDEN": 17, "COD_OD": "PASCO", "NOMBRE": "Pasco", "TIPO": "OD"},
    {"ORDEN": 18, "COD_OD": "PIURA", "NOMBRE": "Piura", "TIPO": "OD"},
    {"ORDEN": 19, "COD_OD": "PUNO", "NOMBRE": "Puno", "TIPO": "OD"},
    {"ORDEN": 20, "COD_OD": "SAN_MARTIN", "NOMBRE": "San Martín", "TIPO": "OD"},
    {"ORDEN": 21, "COD_OD": "TACNA", "NOMBRE": "Tacna", "TIPO": "OD"},
    {"ORDEN": 22, "COD_OD": "TUMBES", "NOMBRE": "Tumbes", "TIPO": "OD"},
    {"ORDEN": 23, "COD_OD": "UCAYALI", "NOMBRE": "Ucayali", "TIPO": "OD"},
    {"ORDEN": 24, "COD_OD": "VRAEM", "NOMBRE": "Vraem", "TIPO": "ODES"},
    {"ORDEN": 25, "COD_OD": "CHIMBOTE", "NOMBRE": "Chimbote", "TIPO": "ODES"},
    {"ORDEN": 26, "COD_OD": "CORACORA", "NOMBRE": "Coracora", "TIPO": "ODES"},
    {"ORDEN": 27, "COD_OD": "COTABAMBAS", "NOMBRE": "Cotabambas", "TIPO": "ODES"},
    {"ORDEN": 28, "COD_OD": "TALARA", "NOMBRE": "Talara", "TIPO": "ODES"},
    {"ORDEN": 29, "COD_OD": "ESPINAR", "NOMBRE": "Espinar", "TIPO": "ODES"},
    {"ORDEN": 30, "COD_OD": "LA_CONVENCION", "NOMBRE": "La convención", "TIPO": "ODES"},
    {"ORDEN": 31, "COD_OD": "PICHANAKI", "NOMBRE": "Pichanaki", "TIPO": "ODES"},
]

# Inventario mínimo por fuente (fallback H6 — docs/lineamientos/extra/fuentes_datos/)
CATALOGO_CAMPOS: list[dict[str, str]] = [
    # F1 GS2
    {"fuente": "F1", "dataset": "5) Multas Coercitivas", "campo": "COD_MA", "tipo": "Texto", "descripcion": "Código medida administrativa"},
    {"fuente": "F1", "dataset": "5) Multas Coercitivas", "campo": "EXP_INF_INCUMP", "tipo": "Texto", "descripcion": "Expediente informe incumplimiento"},
    {"fuente": "F1", "dataset": "5) Multas Coercitivas", "campo": "FN_MC", "tipo": "Fecha", "descripcion": "Notificación carta descargos"},
    {"fuente": "F1", "dataset": "5) Multas Coercitivas", "campo": "MULTA_UIT", "tipo": "Decimal", "descripcion": "Multa en UIT"},
    {"fuente": "F1", "dataset": "5) Multas Coercitivas", "campo": "MULTA_S", "tipo": "Decimal", "descripcion": "Multa en soles"},
    {"fuente": "F1", "dataset": "5) Multas Coercitivas", "campo": "ESTADO_MC", "tipo": "Texto", "descripcion": "Estado multa"},
    # F2 GS1
    {"fuente": "F2", "dataset": "1) Multas coercitivas", "campo": "COD_MA", "tipo": "Texto", "descripcion": "Código medida administrativa"},
    {"fuente": "F2", "dataset": "1) Multas coercitivas", "campo": "COD_PROY_MC", "tipo": "Texto", "descripcion": "Código proyecto multa"},
    {"fuente": "F2", "dataset": "1) Multas coercitivas", "campo": "ESTADO_PAGO_MC", "tipo": "Texto", "descripcion": "Estado de pago"},
    {"fuente": "F2", "dataset": "2) Etapas", "campo": "COD_PROY_MC", "tipo": "Texto", "descripcion": "Proyecto multa"},
    {"fuente": "F2", "dataset": "2) Etapas", "campo": "NRO_ETAPA_MC", "tipo": "Entero", "descripcion": "Número etapa"},
    {"fuente": "F2", "dataset": "2) Etapas", "campo": "EST_ETAPA_MC", "tipo": "Texto", "descripcion": "Estado etapa"},
    # F4
    {"fuente": "F4", "dataset": "T_MVC_MULTACOERCITIVA_MC", "campo": "NU_IDINFORMACIONMC", "tipo": "Número", "descripcion": "Id información MC"},
    {"fuente": "F4", "dataset": "T_MVC_MULTACOERCITIVA_MC", "campo": "TX_IDCUM", "tipo": "Texto", "descripcion": "CUM"},
    {"fuente": "F4", "dataset": "T_MVC_MULTACOERCITIVA_MC", "campo": "TX_IDCAM", "tipo": "Texto", "descripcion": "CAM"},
    {"fuente": "F4", "dataset": "T_MVC_MULTACOERCITIVA_MC", "campo": "NU_MONTOMCUIT", "tipo": "Decimal", "descripcion": "Monto UIT"},
    {"fuente": "F4", "dataset": "T_MVC_MULTACOERCITIVA_MC", "campo": "FG_ESTADOMULTA", "tipo": "Texto", "descripcion": "Estado multa flag"},
    # F5
    {"fuente": "F5", "dataset": "VW_MULTA_COERCITIVA", "campo": "NUMERO_EXPEDIENTE", "tipo": "Texto", "descripcion": "Expediente"},
    {"fuente": "F5", "dataset": "VW_MULTA_COERCITIVA", "campo": "CUM", "tipo": "Texto", "descripcion": "CUM"},
    {"fuente": "F5", "dataset": "VW_MULTA_COERCITIVA", "campo": "CAM", "tipo": "Texto", "descripcion": "CAM"},
    {"fuente": "F5", "dataset": "VW_MULTA_COERCITIVA", "campo": "RESOLUCION", "tipo": "Texto", "descripcion": "Resolución"},
    {"fuente": "F5", "dataset": "VW_MULTA_COERCITIVA", "campo": "ESTADO_MULTA", "tipo": "Texto", "descripcion": "Estado multa"},
    {"fuente": "F5", "dataset": "VW_MULTA_COERCITIVA", "campo": "MONTO_MULTA", "tipo": "Decimal", "descripcion": "Monto multa UIT"},
]

# Sinónimos de estado observados → (TIPO_ESTADO, CODIGO homologado)
MAPEO_ESTADO: dict[str, tuple[str, str]] = {
    "INCUMPLIDO": ("MULTA", "INCUMPLIDO"),
    "PAGADO": ("PAGO", "PAGADO"),
    "ACTIVO": ("MULTA", "ACTIVO"),
    "INACTIVO": ("MULTA", "INACTIVO"),
    "TERMINADO": ("ETAPA", "TERMINADO"),
    "PENDIENTE": ("ETAPA", "PENDIENTE"),
    "SI": ("DESCARGOS", "PRESENTO"),
    "NO": ("DESCARGOS", "NO_PRESENTO"),
}
