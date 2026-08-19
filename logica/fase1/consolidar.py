"""a) Consolidar: UNION auditable, sin filtrar filas."""

from __future__ import annotations

import pandas as pd

from .constantes import ID_CORRIDA


def con_control(df: pd.DataFrame, fuente: str) -> pd.DataFrame:
    out = df.copy()
    out.insert(0, "FUENTE", fuente)
    out.insert(0, "ID_CORRIDA", ID_CORRIDA)
    return out


def consolidar(
    gs1: pd.DataFrame,
    gs2: pd.DataFrame,
    etapas: pd.DataFrame,
    ora: pd.DataFrame,
    mysql: pd.DataFrame,
    informes: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    return {
        "INT_MC_EXCEL": pd.concat(
            [con_control(gs1, "GS1_CAGR"), con_control(gs2, "GS2_LAMBAYEQUE")],
            ignore_index=True,
            sort=False,
        ),
        "INT_MC_ETAPAS": con_control(etapas, "GS1_ETAPAS"),
        "INT_MC_SISUD": con_control(ora, "SISUD_VW_MULTA"),
        "INT_MC_GAPP": con_control(mysql, "GAPP_T_MVC"),
        "INT_INFORMES": con_control(informes, "SISUD_CSEP_INFORMES"),
    }
