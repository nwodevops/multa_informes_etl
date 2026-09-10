"""Orquesta lineamientos Fase 2–7: perfil → integrar → calidad → dimensional → indicadores.

Analogía Java: un PipelineService.run() que encadena steps y devuelve un Map<String, DataFrame>.

Orden fijo (no reordenar sin revisar dependencias):
  1) perfilamiento / diccionario   — diagnóstico de inputs
  2) integrar                      — homologar + rename → 3 bloques canónicos (+ etapas)
  3) concat DF_MULTAS              — UNION auxiliar solo para calidad/KPIs (no es el fact)
  4) aplicar_calidad               — marca defectos; NO borra filas
  5) construir_modelo              — DIMs + 3 facts evidencia + DET etapas
  6) calcular_indicadores          — K1–K5 en memoria

El fact de negocio enriquecido (DW_M_FACT_MULTA_COERCITIVA) NO se construye aquí:
lo arma Oracle con docs/lineamientos/ddl/07_enrich_sheets_sisud.sql tras cargar_dw.
"""

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
    root: Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Ejecuta Fases 2–7 y devuelve todos los DataFrames de salida (clave = nombre lógico/tabla)."""
    tablas = {
        "GS1": gs1,
        "GS2": gs2,
        "ETAPAS": etapas,
        "ORA": ora,
        "DIC_TABLAS": dic_tablas if dic_tablas is not None else pd.DataFrame(),
        "DIC_VARIABLES": dic_variables if dic_variables is not None else pd.DataFrame(),
    }

    # STEP 1: diagnosticar las entradas y construir el diccionario.
    # Estas salidas describen las fuentes; todavía no modifican los hechos.
    prof_resumen, prof_hallazgo = perfilar_todas(tablas)
    diccionario = armar_diccionario(tablas, root=root)

    # STEP 2: homologar y llevar cada fuente a su bloque canónico.
    # CSEP, OD y SISUD permanecen separados; aquí no se hace JOIN entre fuentes.
    df_csep, df_od, df_sisud, df_etapas = integrar(gs1, gs2, etapas, ora)

    # STEP 3: formar una UNION auxiliar para calidad y KPIs.
    # DF_MULTAS no es el fact de negocio ni reemplaza los facts de evidencia.
    df_sheets = pd.concat([df_csep, df_od], ignore_index=True, sort=False)
    df_multas = pd.concat([df_sheets, df_sisud], ignore_index=True, sort=False)

    # STEP 4: aplicar calidad y amarre H9 con cuarentena blanda.
    # Se marcan defectos en DQ/FG_CONFORME; las filas no se eliminan.
    # Los facts evidencia se construyen desde df_csep/od/sisud (sin depender de FG_CONFORME).
    df_multas, dq_hallazgo, qa_amarre, qa_amarre_det = aplicar_calidad(df_multas, df_sisud)

    # STEP 5: construir dimensiones, facts de evidencia y detalle de etapas.
    modelo = construir_modelo(df_csep, df_od, df_sisud, df_etapas)

    # STEP 6: calcular indicadores en memoria usando evidencia y hallazgos.
    fact_evidencia = pd.concat(
        [
            modelo["DW_M_FACT_MC_CSEP"],
            modelo["DW_M_FACT_MC_OD"],
            modelo["DW_M_FACT_MC_SISUD"],
        ],
        ignore_index=True,
        sort=False,
    )
    indicadores = calcular_indicadores(
        fact_evidencia,
        df_multas,
        dq_hallazgo,
        qa_amarre,
        modelo.get("DW_M_DIM_ORGANO_UNIDAD"),
    )

    n_conf_m = int((df_multas.get("FG_CONFORME") == "S").sum()) if len(df_multas) else 0

    # STEP 7: crear el resumen obligatorio de la corrida.
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
                "N_DW_M_DQ_HALLAZGO": len(dq_hallazgo),
                "N_MULTAS_CONFORMES": n_conf_m,
                "N_FACT_CSEP": len(modelo["DW_M_FACT_MC_CSEP"]),
                "N_FACT_OD": len(modelo["DW_M_FACT_MC_OD"]),
                "N_FACT_SISUD": len(modelo["DW_M_FACT_MC_SISUD"]),
                "N_DET_ETAPAS": len(modelo["DW_M_DET_ETAPA_MC"]),
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
        "DW_M_DQ_HALLAZGO": dq_hallazgo,
        "DW_M_QA_AMARRE": qa_amarre,
        "DW_M_QA_AMARRE_DETALLE": qa_amarre_det,
        "DW_M_INDICADOR_RESULTADO": indicadores,
        "RESULTADO": resultado,
    }
    out.update(modelo)  # agrega DW_M_DIM_* + DW_M_FACT_MC_* + DW_M_DET_ETAPA_MC
    return out
