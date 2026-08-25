# Arquetipo Apache Hop + H2 in-memory + Python

Plantilla **mínima** para nuevos ETLs. Clonar con:

```bash
cp -r /ruta/a/etl_phyton_cursor/archetype/ ~/workspace/mi_etl/
cd ~/workspace/mi_etl/
```

## Bootstrap

```bash
# 1. Python venv
python3 -m venv .venv
.venv/bin/python -m pip install -r python/requirements.txt

# 2. Registrar proyecto en Hop (ajusta nombre y ruta)
~/apps/hop/hop-conf.sh --project-create \
  --project=mi_etl \
  --project-home="$(pwd)" \
  --project-keep-config-file

# 3. Completar credenciales en project-config.json o environments/*.json
#    (placeholders <HOST>, <PASSWORD>, etc.)

# 4. Smoke harness
chmod +x init.sh
./init.sh   # debe terminar en HARNESS OK
```

## Qué incluye

- **H2** in-memory `mem:csep` (reset en cada corrida)
- **Hop**: `wf_create_stg.hwf` (diseño STG), `wf_main.hwf` (demo)
- **Python**: `create_stg.py` (DDL), `main.py` + `logica/demo.py`
- **Harness**: `feature_list.json`, `CHECKPOINTS.md`, `init.sh`, `progress/`
- **Skill**: `.agents/skills/hop-python-etl/`

## Extender el proyecto

| Fase | Qué hacer |
|---|---|
| Fuentes STG | Entradas en `inputs.yaml` → `pl_stage_*.hpl` → cablear en `wf_main.hwf` |
| Lecturas | Claves en `python/io/leer_h2.py` |
| Lógica | Un solo `.py` en `logica/` (ver `python/plantilla_logica.py`) |
| MySQL salida | Copiar `python/io/escribir_mysql.py` del repo OEFA |

## Extender a consultoría OEFA (opcional)

El repo [`etl_phyton_cursor`](../) es la implementación de referencia. Copiar desde ahí:

- `logica/dwh/` + `logica/ejecutar.py`
- `python/io/cargar_dw.py`, `python/verify_dw.py`
- `docs/lineamientos/`
- Skills: `phased-dwh-lineamiento`, `auditable-soft-quarantine`, `oracle-cargar-dw`

Regenerar este arquetipo desde el repo padre:

```bash
./scripts/sync_archetype.sh
```

## Verificación

```bash
./init.sh
.venv/bin/python python/main.py   # → output/resultado.xlsx
```

Ver [`docs/verification.md`](docs/verification.md) y [`AGENTS.md`](AGENTS.md).
