"""Carga audit 1:1 (foto cruda STG → DW_M_AUD_*).

Fuera de logica/dwh y de la estrella. Entry: cargar_aud.enriquecer + cargar_aud.cargar_aud
desde main.py. Excepción 1:1: PK_OFICINA derivada en GS1/GS2 (ver oficinas.py).
"""
