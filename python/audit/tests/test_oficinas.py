"""Pruebas del resolvedor PK_OFICINA (sin red ni Oracle).

    python python/audit/tests/test_oficinas.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from audit.oficinas import (
    PREFIJOS_CSEP,
    PREFIJOS_OD,
    indice_oficinas,
    mapa_f1,
    mapa_f2,
    resolver,
)
from config import project_root

ROOT = project_root()
MINERIA = "Coordinación de Supervisión Ambiental en Minería"
AMAZONAS = "Oficina Desconcentrada de Amazonas"


def test_sin_staging_degrada():
    m = resolver(pd.DataFrame(), ROOT)
    assert set(m) == {"GS1", "GS2"}
    assert all(v is None for v in m["GS2"].values()), "F1 debe quedar NULL sin staging"
    resueltos = {k: v for k, v in m["GS1"].items() if v}
    assert resueltos == {"CCAM": "COR068", "UFED": "COR095", "UFSAVC": "COR071"}, resueltos
    assert len(m["GS1"]) == 10 and len(m["GS2"]) == 31


def test_duplicado_en_codigo_consultado_falla():
    dup = pd.DataFrame({"PK_OFICINA": ["COR047", "COR099"], "TX_DESCRIPCION": [AMAZONAS] * 2})
    try:
        mapa_f1(indice_oficinas(dup), ROOT)
    except ValueError as e:
        assert "varias PK" in str(e), e
        return
    raise AssertionError("eligio una PK arbitraria ante nombre duplicado")


def test_duplicado_fuera_de_consulta_no_rompe():
    ruido = pd.DataFrame(
        {"PK_OFICINA": ["SUO00004", "UNO011"], "TX_DESCRIPCION": ["Logistica", "Logistica"]}
    )
    idx = indice_oficinas(ruido)
    assert mapa_f1(idx, ROOT)["AMAZONAS"] is None, "no debe resolver sin la fila real"
    mapa_f2(idx, ROOT)


def test_ambiguedad_real_falla():
    amb = pd.DataFrame({"PK_OFICINA": ["COR064", "SUO00004"], "TX_DESCRIPCION": [MINERIA] * 2})
    try:
        mapa_f2(indice_oficinas(amb), ROOT)
    except ValueError as e:
        assert "CMIN" in str(e) and "varias PK" in str(e), e
        return
    raise AssertionError("eligio una PK arbitraria ante ambiguedad real")


def test_columnas_faltantes_falla():
    try:
        indice_oficinas(pd.DataFrame({"PK_OFICINA": ["X"]}))
    except ValueError as e:
        assert "TX_DESCRIPCION" in str(e), e
        return
    raise AssertionError("acepto un DataFrame sin TX_DESCRIPCION")


def test_normalizacion():
    from audit.oficinas import _norm

    assert _norm("Oficina de Enlace de Talara") == _norm("OFICINA DE ENLACE DE TALARA")
    assert _norm("Huánuco") == _norm("HUANUCO")
    assert _norm("Oficina Desconcentrada de Arequipa ") == "OFICINADESCONCENTRADADEAREQUIPA"


def test_prefijos_ascii():
    assert all(s.isascii() for s in PREFIJOS_OD + PREFIJOS_CSEP)


if __name__ == "__main__":
    pruebas = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for prueba in pruebas:
        prueba()
        print(f"OK  {prueba.__name__}")
    print(f"\n{len(pruebas)}/{len(pruebas)} pruebas pasan")
