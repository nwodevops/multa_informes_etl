# Arquetipo Apache Hop + H2 in-memory

Plantilla base para crear proyectos **Apache Hop** en OEFA.

Reglas fijas del arquetipo:
- Siempre es un ETL **Apache Hop**.
- Siempre se usa **H2 in-memory** (`mem:csep`, puerto `9092`) como staging, con **reset clean en cada corrida** (stop + start + DDL). La infra de H2 se reutiliza de `etl_diego/h2`.

## Nuevo proyecto desde el arquetipo local

Plantilla mínima en [`archetype/README.md`](archetype/README.md) (generada con [`scripts/sync_archetype.sh`](scripts/sync_archetype.sh)):

```bash
cp -r archetype/ ~/workspace/mi_etl/
cd ~/workspace/mi_etl/
# ver archetype/README.md → venv, hop-conf, ./init.sh
```

Este repo (`etl_phyton_cursor`) **extiende** ese arquetipo con lógica OEFA (Fases 2–7, DW Oracle).

## Uso (desde arquetipo histórico)

1. **Copiar** la carpeta a un proyecto nuevo:
   `cp -r archetype/ <workspace>/<nombre_proyecto>`
2. **Registrar el proyecto** en Hop (no editar `hop-config.json` a mano; `--project-keep-config-file` evita que Hop sobrescriba las variables):

```bash
~/apps/hop/hop-conf.sh --project-create \
  --project=<nombre_proyecto> \
  --project-home=<ruta_absoluta> \
  --project-keep-config-file
```

3. **Completar variables** en `project-config.json`:
   - `DB_H2_*` ya vienen listas (in-memory `mem:csep`).
   - Oracle (2 conexiones) y MySQL tienen placeholders `<...>`: rellenar con las credenciales reales (usar `./switch-env.sh local|remote` con `environments/*.json` si se manejan entornos).
   - `DB_ORA_SISUD_*` → **Oracle oefabd** (SISUD, fuente).
   - `DB_ORA_REPO_*` → **Oracle BD_CURSOR** (destino).
   - `DB_MYSQL_*` → MySQL gapps.
4. **Escribir el DDL propio** en `h2/sql/01_schema.sql` (la tabla demo `DEMO_TABLA_EJEMPLO` es solo un smoke test).
5. **Poner la lógica**: en `pipelines/` y `workflows/` (partiendo de `wf_main.hwf` / `pl_demo.hpl`), o pegando un `.py` en `logica/` (zona de pegado aislada, fuera de `python/`; ver `python/plantilla_logica.py` y `python/CONTRATO.md`).

## Capa de lógica (Python, aislada)

- Dos capas: `python/create_stg.py` + `introspect/` (DDL STG, sin filas) y `python/main.py` + `io/` + `logica/` en la raíz (post-staging). Mapa: `python/LEEME.md`.
- Para un ETL nuevo: copiar `python/plantilla_logica.py` → `logica/<tu_logica>.py` (**un solo `.py`**), escribir la transformación con los DataFrames de entrada (nombres = claves de `LECTURAS` en `python/io/leer_h2.py`) y dejar el DataFrame `RESULTADO`. `main.py` lo auto-descubre y lo ejecuta.
- **Prerequisitos**: Java en PATH (H2), venv con `pip install -r python/requirements.txt` (incluye pandas y openpyxl). No se usa R ni `ojdbc11.jar`.
- **Smoke**: escribe `output/resultado.xlsx`. MySQL y Oracle se omiten si las credenciales son placeholders `<...>`.

## Plataforma

Portado a Linux: los workflows llaman a `h2/scripts/*.sh` y a `.venv/bin/python`. Los `.bat` y `switch-env.ps1` quedan solo como referencia para Windows.

Python va en un venv del proyecto porque el intérprete del sistema es *externally managed* (PEP 668):

```bash
python3 -m venv --without-pip .venv
curl -fsSL -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py && .venv/bin/python /tmp/get-pip.py
.venv/bin/python -m pip install -r python/requirements.txt
```

Los workflows usan `.venv/bin/python` si existe, y si no `python3`.

## Verificación

**Harness (recomendado):**

```bash
chmod +x init.sh   # una vez
./init.sh          # debe terminar en HARNESS OK
```

Criterios por fase: [`CHECKPOINTS.md`](CHECKPOINTS.md). Detalle: [`docs/verification.md`](docs/verification.md). Alcance de trabajo: [`feature_list.json`](feature_list.json).

Alternativa manual sin Hop GUI:

```bash
./h2/scripts/reset_and_create.sh && .venv/bin/python python/create_stg.py && .venv/bin/python python/main.py
```

Corrida completa con staging externo: `workflows/wf_main.hwf` en Apache Hop (`~/apps/hop/hop-gui.sh`).

## Notas

- La BD in-memory se llama `mem:csep` en el arquetipo (igual que `etl_diego`). Si se renombra, hay que cambiarla en 4 lugares: `h2/scripts/reset_and_create.sh`, `project-config.json`, `environments/*.json` y `metadata/rdbms/h2.json`.
- Los scripts usan rutas relativas al propio script, así que funcionan copiados tal cual. Requieren `java` en PATH.
- `h2-2.4.240.jar`, puerto `9092` (H2 TCP + WEB `8082`).
- Contraseñas de BDs van en texto plano en `project-config.json` / `environments/*.json`: no commitear ni propagar.
