"""Catálogos de referencia (semillas ddl/01 + inventario de campos F1–F5)."""

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
    ("INFORME", "EN_CUSTODIA", "En custodia", "VIGENTE"),
    ("INFORME", "EN_REVISION", "En revisión", "VIGENTE"),
    ("INFORME", "APROBADO", "Aprobado", "CERRADO"),
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
    # F3
    {"fuente": "F3", "dataset": "CSEP_INFORMES_VIEW", "campo": "IDACTIVIDAD", "tipo": "Número", "descripcion": "Id actividad supervisión"},
    {"fuente": "F3", "dataset": "CSEP_INFORMES_VIEW", "campo": "TXCUC", "tipo": "Texto", "descripcion": "Código único caso"},
    {"fuente": "F3", "dataset": "CSEP_INFORMES_VIEW", "campo": "TXNUMEXP", "tipo": "Texto", "descripcion": "Número expediente"},
    {"fuente": "F3", "dataset": "CSEP_INFORMES_VIEW", "campo": "TXESTADO", "tipo": "Texto", "descripcion": "Estado actividad"},
    {"fuente": "F3", "dataset": "CSEP_INFORMES_VIEW", "campo": "FEINICIO", "tipo": "Fecha", "descripcion": "Inicio supervisión"},
    {"fuente": "F3", "dataset": "CSEP_INFORMES_VIEW", "campo": "FEINFORME", "tipo": "Fecha", "descripcion": "Fecha informe"},
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
    "EN CUSTODIA": ("INFORME", "EN_CUSTODIA"),
    "EN REVISION": ("INFORME", "EN_REVISION"),
    "APROBADO": ("INFORME", "APROBADO"),
    "SI": ("DESCARGOS", "PRESENTO"),
    "NO": ("DESCARGOS", "NO_PRESENTO"),
}
