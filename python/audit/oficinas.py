"""Resuelve PK_OFICINA para las fotos AUD de F1 y F2 desde T_SEP_OFICINA.

La tabla gappsdb.T_SEP_OFICINA es la autoridad de PK_OFICINA; este modulo
solo la consulta. No lee filas de MySQL ni escribe en Oracle.

Orden de resolucion de un codigo de negocio (COD_UNIDAD / COD_OD):

    1. OVERRIDE  el catalogo declara pk_oficina para esa unidad
                 (CCAM / UFED / UFSAVC: su 'nombre' no permite derivarla).
    2. DERIVAR   se construye el nombre de oficina esperado y se busca
                 normalizado contra TX_DESCRIPCION.
                 0 coincidencias -> None (+ aviso en el log del pipeline)
                 >1 coincidencia  -> error: la fuente tiene nombres duplicados

Emparejar por nombre COMPLETO normalizado, nunca por prefijo ni subcadena,
garantiza que un cambio de nombre en GAPPS produzca NULL y no una PK
equivocada. _norm() colapsa mayusculas, acentos, signos y espacios, que es
lo que hace equivalentes HUANUCO/HUANUCO, CONVENCION/CONVENCIÓN y el "DE"
irregular de "Oficina de Enlace de Talara".

Este archivo es deliberadamente ASCII: los prefijos van sin tilde porque
_norm() las descarta, y asi ningun editor ni consola puede corromper la
comparacion con la fuente.

PK_OFICINA solo se agrega a DW_M_AUD_F2_CSEP_MULTAS y DW_M_AUD_F1_OD_MULTAS.
No participa de la estrella (DIM_/FACT_) ni del enriquecido.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

from f1_ods_catalog import load_catalog as load_f1_catalog
from f1_ods_catalog import nombre_por_cod
from f2_csep_catalog import descripcion_por_sigla, load_catalog as load_f2_catalog
from f2_csep_catalog import pk_oficina_por_sigla

# Columnas de T_SEP_OFICINA que interesan al mapeo.
COL_PK = "PK_OFICINA"
COL_DESCRIPCION = "TX_DESCRIPCION"

# Prefijos reales de T_SEP_OFICINA para oficinas desconcentradas y de enlace.
# Se prueban todos y se acepta el primero que exista en la tabla: la fuente usa
# "Oficina de Enlace de Talara" (COR091) pero "Oficina de Enlace Chimbote" (COR033).
PREFIJOS_OD = (
    "Oficina Desconcentrada de ",
    "Oficina de Enlace de ",
    "Oficina de Enlace ",
    "Oficina ",
)

# Prefijos reales de T_SEP_OFICINA para supervisiones/UF de sede central.
PREFIJOS_CSEP = (
    "Coordinacion de Supervision Ambiental en ",
    "Unidad Funcional Supervision Ambiental en ",
)


def _norm(texto) -> str:
    """Mayusculas, sin acentos y solo alfanumericos: clave de comparacion."""
    descompuesto = unicodedata.normalize("NFKD", str(texto or ""))
    sin_acentos = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]", "", sin_acentos.upper())


def indice_oficinas(oficinas: pd.DataFrame) -> dict[str, list[str]]:
    """TX_DESCRIPCION normalizado -> lista de PK_OFICINA que lo usan.

    T_SEP_OFICINA comparte nombres entre familias distintas (COR### de OD,
    SUO##### y UNO### de sede central), asi que un nombre puede tener varias
    PK. Se guardan todas; la ambiguedad se resuelve recien al buscar el codigo
    de negocio, que es el unico momento en que importa.
    """
    if oficinas is None or len(oficinas) == 0:
        return {}
    faltantes = [c for c in (COL_PK, COL_DESCRIPCION) if c not in oficinas.columns]
    if faltantes:
        raise ValueError(f"STG_MYSQL_OFICINAS sin columnas {faltantes}")

    indice: dict[str, list[str]] = {}
    for pk, descripcion in zip(oficinas[COL_PK], oficinas[COL_DESCRIPCION]):
        clave = _norm(descripcion)
        if not clave or pd.isna(pk):
            continue
        candidatos = indice.setdefault(clave, [])
        if str(pk) not in candidatos:
            candidatos.append(str(pk))

    repetidos = {c: p for c, p in indice.items() if len(p) > 1}
    if repetidos:
        print(
            f"AUD: T_SEP_OFICINA tiene {len(repetidos)} nombres de oficina compartidos "
            "entre PK (p. ej. sede central COR/SUO/UNO); se desambiguan por codigo",
            flush=True,
        )
    return indice


def _buscar(
    indice: dict[str, list[str]], nombres: tuple[str, ...], codigo: str, familia: str
) -> str | None:
    """PK del primer nombre de `nombres` que exista en el indice; None si ninguno.

    Si un nombre ya existe con varias PK, se falla: escribir una PK arbitraria
    seria peor que no escribirla, y un codigo ambiguo es un defecto de la fuente
    que hay que ver, no silenciar.
    """
    for nombre in nombres:
        candidatos = indice.get(_norm(nombre))
        if not candidatos:
            continue
        if len(candidatos) > 1:
            raise ValueError(
                f"{familia} '{codigo}': el nombre de oficina '{nombre}' corresponde a "
                f"varias PK en T_SEP_OFICINA {sorted(candidatos)}; no se puede resolver"
            )
        return candidatos[0]
    return None


def mapa_f1(indice: dict[str, list[str]], root: Path) -> dict[str, str]:
    """COD_OD -> PK_OFICINA, derivando 'Oficina (Desconcentrada de|De Enlace) {nombre}'."""
    nombres = nombre_por_cod(load_f1_catalog(root))
    return {
        cod: _buscar(indice, tuple(p + nombre for p in PREFIJOS_OD), cod, "F1 COD_OD")
        for cod, nombre in nombres.items()
    }


def mapa_f2(indice: dict[str, list[str]], root: Path) -> dict[str, str]:
    """COD_UNIDAD -> PK_OFICINA. Primero el override del catalogo, luego la derivacion."""
    catalog = load_f2_catalog(root)
    overrides = pk_oficina_por_sigla(catalog)
    nombres = descripcion_por_sigla(catalog)
    mapa: dict[str, str] = dict(overrides)
    for sigla, nombre in nombres.items():
        if sigla not in overrides:
            mapa[sigla] = _buscar(
                indice, tuple(p + nombre for p in PREFIJOS_CSEP), sigla, "F2 COD_UNIDAD"
            )
    return mapa


def auditar(mapa: dict[str, str], etiqueta: str) -> None:
    """Informa los codigos del catalogo que no__.__PK_OFICINA."""
    sin_pk = sorted(cod for cod, pk in mapa.items() if not pk)
    if sin_pk:
        print(
            f"AUD: AVISO {etiqueta}: {len(sin_pk)}/{len(mapa)} codigos de catalogo sin "
            f"PK_OFICINA: {sin_pk}",
            flush=True,
        )
    else:
        print(f"AUD: {etiqueta}: {len(mapa)}/{len(mapa)} codigos con PK_OFICINA", flush=True)


def resolver(oficinas: pd.DataFrame | None, root: Path) -> dict[str, dict[str, str]]:
    """Punto de entrada: los dos mapas COD -> PK_OFICINA que consume cargar_aud."""
    indice = indice_oficinas(oficinas)
    if not indice:
        print(
            "AUD: AVISO STG_MYSQL_OFICINAS vacio o ausente; PK_OFICINA solo se resolvera "
            "para las unidades con pk_oficina declarado en el catalogo F2",
            flush=True,
        )
    mapa_f1_od = mapa_f1(indice, root)
    mapa_f2_unidad = mapa_f2(indice, root)
    auditar(mapa_f1_od, "F1 COD_OD")
    auditar(mapa_f2_unidad, "F2 COD_UNIDAD")
    return {"GS2": mapa_f1_od, "GS1": mapa_f2_unidad}
