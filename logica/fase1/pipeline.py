"""Orquesta fase 1: consolidar (a) + diagnosticar (c)."""

from __future__ import annotations

import pandas as pd

from .consolidar import consolidar
from .constantes import LLAVES
from .diagnostico import armar_qa


def ejecutar(
    gs1: pd.DataFrame,
    gs2: pd.DataFrame,
    etapas: pd.DataFrame,
    ora: pd.DataFrame,
    mysql: pd.DataFrame,
    informes: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    ints = consolidar(gs1, gs2, etapas, ora, mysql, informes)
    piezas = [
        (gs1, "STG_GS1_MULTAS_COERCITIVAS", "GS1_CAGR", "STG", LLAVES["GS1"]),
        (gs2, "STG_GS2_MULTAS_COERCITIVAS", "GS2_LAMBAYEQUE", "STG", LLAVES["GS2"]),
        (etapas, "STG_GS1_ETAPAS", "GS1_ETAPAS", "STG", LLAVES["ETAPAS"]),
        (ora, "STG_ORA_VW_MULTA_COERCITIVA", "SISUD_VW_MULTA", "STG", LLAVES["ORA"]),
        (mysql, "STG_MYSQL_T_MVC_MULTACOERCITIVA", "GAPP_T_MVC", "STG", LLAVES["MYSQL"]),
        (informes, "STG_ORA_CSEP_INFORMES", "SISUD_CSEP_INFORMES", "STG", LLAVES["INFORMES"]),
        (ints["INT_MC_EXCEL"], "INT_MC_EXCEL", "GS1+GS2", "INT", LLAVES["INT_MC_EXCEL"]),
        (ints["INT_MC_ETAPAS"], "INT_MC_ETAPAS", "GS1_ETAPAS", "INT", LLAVES["INT_MC_ETAPAS"]),
        (ints["INT_MC_SISUD"], "INT_MC_SISUD", "SISUD_VW_MULTA", "INT", LLAVES["INT_MC_SISUD"]),
        (ints["INT_MC_GAPP"], "INT_MC_GAPP", "GAPP_T_MVC", "INT", LLAVES["INT_MC_GAPP"]),
        (ints["INT_INFORMES"], "INT_INFORMES", "SISUD_CSEP_INFORMES", "INT", LLAVES["INT_INFORMES"]),
    ]
    qa_corrida, qa_exc = armar_qa(piezas)
    return {
        **ints,
        "QA_CORRIDA": qa_corrida,
        "QA_EXCEPCION": qa_exc,
        "RESULTADO": qa_corrida.copy(),
    }
