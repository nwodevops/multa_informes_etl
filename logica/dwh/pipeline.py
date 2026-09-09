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
    dic_tablas: pd.DataFrame | None = None,
    dic_variables: pd.DataFrame | None = None,
    gs2_ods: dict[str, pd.DataFrame] | None = None,
    root: Path | None = None,
) -> dict[str, pd.DataFrame]:
    extra_ods = gs2_ods or {}
    tablas = {
        "GS1": gs1,
        "GS2": gs2,
        "ETAPAS": etapas,
        "ORA": ora,
        "DIC_TABLAS": dic_tablas if dic_tablas is not None else pd.DataFrame(),
        "DIC_VARIABLES": dic_variables if dic_variables is not None else pd.DataFrame(),
    }
    tablas.update(extra_ods)

    prof_resumen, prof_hallazgo = perfilar_todas(tablas)
    diccionario = armar_diccionario(tablas, root=root)

    df_csep, df_od, df_sisud, df_etapas = integrar(gs1, gs2, etapas, ora, gs2_ods=extra_ods)
    df_sheets = pd.concat([df_csep, df_od], ignore_index=True, sort=False)
    df_multas = pd.concat([df_sheets, df_sisud], ignore_index=True, sort=False)

    df_multas, dq_hallazgo, qa_amarre, qa_amarre_det = aplicar_calidad(df_multas, df_sisud)
    # Conformidad también sobre los trozos por universo (misma lógica vía df_multas ya marcado)
    modelo = construir_modelo(df_csep, df_od, df_sisud, df_etapas)

    fact_evidencia = pd.concat(
        [
            modelo["MI_FACT_MC_CSEP"],
            modelo["MI_FACT_MC_OD"],
            modelo["MI_FACT_MC_SISUD"],
        ],
        ignore_index=True,
        sort=False,
    )
    indicadores = calcular_indicadores(
        fact_evidencia,
        df_multas,
        dq_hallazgo,
        qa_amarre,
        modelo.get("MI_DIM_ORGANO_UNIDAD"),
    )

    n_conf_m = int((df_multas.get("FG_CONFORME") == "S").sum()) if len(df_multas) else 0

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
                "N_DF_CSEP": len(df_csep),
                "N_DF_OD": len(df_od),
                "N_DF_SISUD": len(df_sisud),
                "N_DF_ETAPAS": len(df_etapas),
                "N_MI_DQ_HALLAZGO": len(dq_hallazgo),
                "N_MULTAS_CONFORMES": n_conf_m,
                "N_FACT_CSEP": len(modelo["MI_FACT_MC_CSEP"]),
                "N_FACT_OD": len(modelo["MI_FACT_MC_OD"]),
                "N_FACT_SISUD": len(modelo["MI_FACT_MC_SISUD"]),
                "N_DET_ETAPAS": len(modelo["MI_DET_ETAPA_MC"]),
                "N_INDICADORES": len(indicadores),
                "N_QA_AMARRE_DET": len(qa_amarre_det),
            }
        ]
    )

    out = {
        "PROF_RESUMEN": prof_resumen,
        "PROF_HALLAZGO": prof_hallazgo,
        "DICCIONARIO": diccionario,
        "DF_MULTAS": df_multas,
        "DF_CSEP": df_csep,
        "DF_OD": df_od,
        "DF_SISUD": df_sisud,
        "DF_ETAPAS": df_etapas,
        "MI_DQ_HALLAZGO": dq_hallazgo,
        "QA_AMARRE": qa_amarre,
        "MI_QA_AMARRE": qa_amarre,
        "MI_QA_AMARRE_DETALLE": qa_amarre_det,
        "MI_INDICADOR_RESULTADO": indicadores,
        "RESULTADO": resultado,
    }
    out.update(modelo)
    return out
