"""Prueba del camino completo: MySQL real → resolver → _derivar → DataFrames.

Solo lectura. No escribe en H2 ni en Oracle, así que corre sin Hop.

    python python/audit/tests/test_oficinas_e2e.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import importlib.util
import re
import unicodedata

import mysql.connector
import pandas as pd

from audit.oficinas import resolver
from config import load_vars, project_root, require_live_conn

ROOT = project_root()

# Las 44 conversiones entregadas por negocio (PK_OFICINA → código).
CONVERSIONES_ESPERADAS = {
    "CELE": "COR062", "CMIN": "COR064", "CHID": "COR063", "CAGR": "COR065",
    "UFED": "COR095", "CPES": "COR067", "CIND": "COR066", "CRES": "COR069",
    "UFSAVC": "COR071", "CCAM": "COR068",
    "AMAZONAS": "COR047", "ANCASH": "COR042", "APURIMAC": "COR034",
    "AREQUIPA": "COR039", "AYACUCHO": "COR024", "CAJAMARCA": "COR031",
    "CUSCO": "COR040", "HUANUCO": "COR037", "HUANCAVELICA": "COR030",
    "ICA": "COR035", "JUNIN": "COR032", "LA_LIBERTAD": "COR013",
    "LAMBAYEQUE": "COR036", "LORETO": "COR048", "MADRE_DE_DIOS": "COR045",
    "MOQUEGUA": "COR049", "PASCO": "COR028", "PIURA": "COR025", "PUNO": "COR023",
    "SAN_MARTIN": "COR050", "TACNA": "COR051", "TUMBES": "COR041",
    "UCAYALI": "COR043", "VRAEM": "COR038", "CHIMBOTE": "COR033",
    "CORACORA": "COR087", "COTABAMBAS": "COR055", "TALARA": "COR091",
    "ESPINAR": "COR044", "LA_CONVENCION": "COR072", "PICHANAKI": "COR046",
}


def _cargar_cargar_aud():
    ruta = ROOT / "python" / "audit" / "cargar_aud.py"
    spec = importlib.util.spec_from_file_location("cargar_aud", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _oficinas_reales() -> pd.DataFrame:
    variables = load_vars(ROOT)
    cv = require_live_conn("mysql", variables)
    conn = mysql.connector.connect(
        host=cv["host"],
        port=int(cv["port"]),
        user=cv["username"],
        password=cv["password"],
        database="gappsdb",
        charset="utf8mb4",
    )
    try:
        cur = conn.cursor()
        cur.execute("SELECT PK_OFICINA, TX_DESCRIPCION FROM T_SEP_OFICINA")
        filas = cur.fetchall()
        cur.close()
    finally:
        conn.close()
    return pd.DataFrame(filas, columns=["PK_OFICINA", "TX_DESCRIPCION"])


def test_mapeo_completo_con_la_fuente():
    """Los 41 códigos de las conversiones de negocio deben resolver igual."""
    mapas = resolver(_oficinas_reales(), ROOT)
    combined = {**mapas["GS1"], **mapas["GS2"]}
    faltan = [c for c in CONVERSIONES_ESPERADAS if not combined.get(c)]
    assert not faltan, f"códigos sin PK_OFICINA: {faltan}"
    difieren = {
        c: (CONVERSIONES_ESPERADAS[c], combined[c])
        for c in CONVERSIONES_ESPERADAS
        if combined[c] != CONVERSIONES_ESPERADAS[c]
    }
    assert not difieren, f"PK_OFICINA distinta a la esperada: {difieren}"
    assert len(CONVERSIONES_ESPERADAS) == 41


def test_catalogo_completo():
    """Ningún código de los catálogos F1/F2 queda sin resolver contra la fuente real."""
    mapas = resolver(_oficinas_reales(), ROOT)
    assert len(mapas["GS2"]) == 31, len(mapas["GS2"])
    assert len(mapas["GS1"]) == 10, len(mapas["GS1"])
    sin = {k: v for k, v in mapas["GS2"].items() if not v}
    assert not sin, f"F1 COD_OD sin resolver: {sin}"
    sin = {k: v for k, v in mapas["GS1"].items() if not v}
    assert not sin, f"F2 COD_UNIDAD sin resolver: {sin}"


def test_derivar_sobre_dataframes():
    """El hook de cargar_aud agrega la columna y no pierde filas."""
    aud = _cargar_cargar_aud()
    mapas = resolver(_oficinas_reales(), ROOT)

    gs1 = pd.DataFrame(
        {
            "COD_MA": ["A", "B", "C", "D"],
            "COD_UNIDAD": ["CAGR", "CHID", "UFED", "CCAM"],
            "MULTA_S": [1, 2, 3, 4],
        }
    )
    gs2 = pd.DataFrame(
        {
            "COD_MA": ["E", "F", "G"],
            "COD_OD": ["AMAZONAS", "talara", "SAN_MARTIN"],
            "MULTA_S": [5, 6, 7],
        }
    )
    out1 = aud._derivar("GS1", gs1, mapas)
    out2 = aud._derivar("GS2", gs2, mapas)

    assert list(out1["PK_OFICINA"]) == ["COR065", "COR063", "COR095", "COR068"]
    assert list(out2["PK_OFICINA"]) == ["COR047", "COR091", "COR050"]
    assert len(out1) == len(gs1) and len(out2) == len(gs2)
    assert out1["COD_MA"].tolist() == gs1["COD_MA"].tolist()
    assert list(out1.columns)[-1] == "PK_OFICINA"


def test_codigo_desconocido_queda_null():
    """Un código sin PK_OFICINA queda NULL y la fila no se descarta."""
    aud = _cargar_cargar_aud()
    mapas = resolver(_oficinas_reales(), ROOT)
    gs2 = pd.DataFrame({"COD_MA": ["X", "Y"], "COD_OD": ["NO_EXISTE", "ICA"]})
    out = aud._derivar("GS2", gs2, mapas)
    assert len(out) == 2
    assert pd.isna(out["PK_OFICINA"].iloc[0])
    assert out["PK_OFICINA"].iloc[1] == "COR035"


def test_enriquecer_muta_stg_para_el_espejo():
    """enriquecer() deja PK_OFICINA dentro del dict `datos`.

    Es lo que hace que el espejo MySQL (cargar_aud_mysql, que arma sus columnas
    desde df.columns) publique la misma forma que Oracle, sin tocar ese archivo.
    """
    aud = _cargar_cargar_aud()
    stg = {
        "OFICINAS": _oficinas_reales(),
        "GS1": pd.DataFrame({"COD_UNIDAD": ["CAGR", "UFED"]}),
        "GS2": pd.DataFrame({"COD_OD": ["ICA", "TALARA"]}),
        "MYSQL": pd.DataFrame({"PK_MULTA": [1]}),
    }
    salida = aud.enriquecer(stg, ROOT)

    assert salida is stg, "enriquecer debe devolver el mismo dict que recibe"
    assert list(salida["GS1"]["PK_OFICINA"]) == ["COR065", "COR095"]
    assert list(salida["GS2"]["PK_OFICINA"]) == ["COR035", "COR091"]
    assert "PK_OFICINA" not in salida["MYSQL"].columns, "MYSQL no se deriva"
    assert salida["OFICINAS"].equals(stg["OFICINAS"]), "la fuente queda intacta"


def test_enriquecer_tolera_stg_incompleto():
    """Sin GS1/GS2 ni OFICINAS, enriquecer no revienta."""
    aud = _cargar_cargar_aud()
    salida = aud.enriquecer({"MYSQL": pd.DataFrame({"PK_MULTA": [1]})}, ROOT)
    assert list(salida) == ["MYSQL"]


def test_fuente_sin_acentos_sigue_resolviendo():
    """Si MySQL devuelve la columna sin tildes, el mapeo no cambia."""
    from audit.oficinas import indice_oficinas, mapa_f1

    real = _oficinas_reales()

    def sin_tildes(texto):
        d = unicodedata.normalize("NFKD", str(texto or ""))
        return "".join(c for c in d if not unicodedata.combining(c))

    plano = real.assign(TX_DESCRIPCION=real["TX_DESCRIPCION"].map(sin_tildes))
    completo = mapa_f1(indice_oficinas(real), ROOT)
    degradado = mapa_f1(indice_oficinas(plano), ROOT)
    assert completo == degradado


if __name__ == "__main__":
    pruebas = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for prueba in pruebas:
        prueba()
        print(f"OK  {prueba.__name__}")
    print(f"\n{len(pruebas)}/{len(pruebas)} pruebas pasan (MySQL real, solo lectura)")
