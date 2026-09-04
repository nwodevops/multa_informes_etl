# Docker — dashboards indicadores (opción C)

Apache Superset en contenedor, con `oracledb`, para visualizar `MI_INDICADOR_RESULTADO`  
contra el **Oracle DW local** (`app@localhost:1524/BD_CURSOR`).  
Rama: `linux`. Windows / Power BI → rama `windows`.

## Requisitos

- Docker + Docker Compose
- Oracle local arriba (el mismo de `./switch-env.sh local` + `./init.sh`)
- Datos cargados: `APP.MI_INDICADOR_RESULTADO` (tras un ETL local OK)

## Arranque

```bash
cd /ruta/al/repo   # rama linux
docker compose -f docker/docker-compose.yml up --build
```

UI: http://localhost:8088  

Usuario / clave por defecto: `admin` / `admin`  
(Cambiar con `SUPERSET_ADMIN_PASSWORD` en el entorno o en `docker-compose.yml`.)

## Conectar Oracle en Superset

1. **Settings → Database connections → + Database**
2. Tipo: **Oracle** (o SQLAlchemy URI)
3. URI (desde el contenedor el host es `host.docker.internal`):

```text
oracle+oracledb://app:TU_PASSWORD@host.docker.internal:1524/?service_name=BD_CURSOR
```

Password = `DB_ORA_DW_PASSWORD` de `environments/local.json` (no commitear).

4. Test connection → Save.

## Dataset / gráfico

1. **Datasets → + Dataset** → base Oracle → schema `APP` → tabla `MI_INDICADOR_RESULTADO`
2. **Charts → + Chart** → Bar / Table  
   - Dimensiones: `COD_INDICADOR`, `ANIO`, `METRICA`  
   - Métrica: `SUM(VALOR)` o `AVG(VALOR)`
3. Guardar en un Dashboard.

SQL de prueba en SQL Lab:

```sql
SELECT COD_INDICADOR, METRICA, ANIO, ID_ORGANO, VALOR, UNIDAD
FROM APP.MI_INDICADOR_RESULTADO
ORDER BY COD_INDICADOR, ANIO, ID_ORGANO
```

## Parar

```bash
docker compose -f docker/docker-compose.yml down
```

Datos de Superset (usuarios, dashboards) viven en el volumen `superset_home`.

## Nota

Esto **no** reemplaza el ETL. Solo consume lo ya cargado en Oracle local.  
Tras cada `./init.sh`, refrescar el dataset / dashboard en Superset.
