# impl_dw-solo-multas

**Fecha:** 2026-09-02  
**Feature:** `dw-solo-multas` → `done`

## Qué se hizo

F3 (INFORMES / `CSEP_INFORMES_VIEW`) sale de Hop, H2, Python, Kimball y Oracle. El DW queda **solo Multas** (F1, F2, F4, F5 + etapas). Fase 3 del lineamiento (`integracion.py`) se mantiene con `DF_MULTAS` + `DF_ETAPAS`.

- Hop: sin `pl_stage_informes.hpl`; `wf_main` / `wf_main_win` van de Stage Oracle VW a Stage MySQL.
- Python: sin `LECTURAS INFORMES`, `DF_INFORMES`, `MI_FACT_INFORME_SUPERVISION`, `ID_INFORME`, K1 `N_INFORMES`.
- Oracle vivo: `cargar_dw.py` hace DROP FK/tabla/índice/columna de informes antes del TRUNCATE.
- `init.sh` / `verify_dw.py`: fallan si reaparece el hecho informe o `ID_INFORME`.

## Evidencia

```bash
./switch-env.sh local
./init.sh          # → HARNESS OK
.venv/bin/python python/verify_dw.py
```

Hop **no** ejecuta `pl_stage_informes`. Staging:

| Pipeline | Filas |
|---|---|
| Excel GS1 multas / etapas / GS2 | 16 / 55 / 21 |
| `pl_stage_oracle` (`VW_MULTA_COERCITIVA`) | 530 |
| `pl_stage_mysql` | 4 |

Python (log `./init.sh`):

- `DF_MULTAS` 571 · `DF_ETAPAS` 55 · **cero** `DF_INFORMES`
- `MI_FACT_MULTA_COERCITIVA` 571 · `MI_DET_ETAPA_MC` 55 · **cero** `MI_FACT_INFORME_SUPERVISION`
- `MI_INDICADOR_RESULTADO` 152 (K1–K5; K1 solo `N_MULTAS`)

Oracle `app@localhost:1524/BD_CURSOR` esquema APP:

- `MI_FACT_MULTA_COERCITIVA` = 571
- `MI_INDICADOR_RESULTADO` = 152 (K1: 34, K2: 10, K3: 66, K4: 33, K5: 9)
- `MI_FACT_INFORME_SUPERVISION`: **inexistente**
- `MI_FACT_MULTA_COERCITIVA.ID_INFORME`: **inexistente**

Sandbox SISUD local: `localhost:1525/CSEP` (F5). DW: `localhost:1524/BD_CURSOR`.

## Archivos clave

- `inputs.yaml`, `workflows/wf_main.hwf`, `workflows/wf_main_win.hwf`, `init.sh`, `init.bat`
- `python/io/leer_h2.py`, `logica/dwh/*`, `python/io/cargar_dw.py`, `python/verify_dw.py`
- `docs/lineamientos/ddl/01_dimensiones.sql`, `02_hechos.sql`, `05_comentarios.sql`
- `docs/adjuntos/modelo-kimball.md`, `docs/inputs/README.md`
