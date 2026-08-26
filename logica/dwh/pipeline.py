"""Orquesta lineamientos Fase 2–7: perfil, diccionario, integración, calidad, dimensional, indicadores."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .calidad import aplicar_calidad
from .constantes import FECHA_CARGA, ID_CARGA
from .diccionario import armar_diccionario
from .dimensional import construir_modelo
from .indicadores import calcular_indicadores
from .integracion import integrar
from .perfilamiento import perfilar_todas


def ejecutar(
    gs1: pd.DataFrame,
    gs2: pd.DataFrame,
    etapas: pd.DataFrame,
    ora: pd.DataFrame,
    mysql: pd.DataFrame,
    informes: pd.DataFrame,
    dic_tablas: pd.DataFrame | None = None,
    dic_variables: pd.DataFrame | None = None,
    root: Path | None = None,
) -> dict[str, pd.DataFrame]:
    tablas = {
        "GS1": gs1,
        "GS2": gs2,
        "ETAPAS": etapas,
        "ORA": ora,
        "MYSQL": mysql,
        "INFORMES": informes,
        "DIC_TABLAS": dic_tablas if dic_tablas is not None else pd.DataFrame(),
        "DIC_VARIABLES": dic_variables if dic_variables is not None else pd.DataFrame(),
    }

    prof_resumen, prof_hallazgo = perfilar_todas(tablas)
    diccionario = armar_diccionario(tablas, root=root)

    df_multas, df_informes, df_etapas = integrar(gs1, gs2, etapas, ora, mysql, informes)
    df_multas, df_informes, dq_hallazgo, qa_amarre = aplicar_calidad(df_multas, df_informes)
    modelo = construir_modelo(df_multas, df_informes, df_etapas)
    indicadores = calcular_indicadores(
        modelo["MI_FACT_MULTA_COERCITIVA"],
        modelo["MI_FACT_INFORME_SUPERVISION"],
        df_multas,
        df_informes,
        dq_hallazgo,
        qa_amarre,
        modelo.get("MI_DIM_ORGANO_UNIDAD"),
    )

    n_conf_m = int((df_multas.get("FG_CONFORME") == "S").sum()) if len(df_multas) else 0
    n_conf_i = int((df_informes.get("FG_CONFORME") == "S").sum()) if len(df_informes) else 0

    resultado = pd.DataFrame(
        [
            {
                "ID_CARGA": ID_CARGA,
                "FECHA_CARGA": FECHA_CARGA,
                "FASE": "2-7",
                "N_PROF_CAMPOS": len(prof_resumen),
                "N_PROF_HALLAZGOS": len(prof_hallazgo),
                "N_DICCIONARIO": len(diccionario),
                "N_DF_MULTAS": len(df_multas),
                "N_DF_INFORMES": len(df_informes),
                "N_DF_ETAPAS": len(df_etapas),
                "N_MI_DQ_HALLAZGO": len(dq_hallazgo),
                "N_MULTAS_CONFORMES": n_conf_m,
                "N_INFORMES_CONFORMES": n_conf_i,
                "N_FACT_MULTAS": len(modelo["MI_FACT_MULTA_COERCITIVA"]),
                "N_FACT_INFORMES": len(modelo["MI_FACT_INFORME_SUPERVISION"]),
                "N_DET_ETAPAS": len(modelo["MI_DET_ETAPA_MC"]),
                "N_INDICADORES": len(indicadores),
            }
        ]
    )

    out = {
        "PROF_RESUMEN": prof_resumen,
        "PROF_HALLAZGO": prof_hallazgo,
        "DICCIONARIO": diccionario,
        "DF_MULTAS": df_multas,
        "DF_INFORMES": df_informes,
        "DF_ETAPAS": df_etapas,
        "MI_DQ_HALLAZGO": dq_hallazgo,
        "QA_AMARRE": qa_amarre,
        "MI_INDICADOR_RESULTADO": indicadores,
        "RESULTADO": resultado,
    }
    out.update(modelo)
    return out
