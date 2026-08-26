# Superset + oracledb — dashboards sobre MI_INDICADOR_RESULTADO (opción C Ubuntu)
# Conecta al Oracle DW local (APP@localhost:1524/BD_CURSOR) vía host.docker.internal.

FROM apache/superset:4.0.2

USER root

RUN pip install --no-cache-dir "oracledb>=2.0" "pandas>=2.0"

# Scripts de arranque (admin + ejemplo)
COPY docker/superset-init.sh /superset-init.sh
RUN chmod +x /superset-init.sh

USER superset

ENV SUPERSET_SECRET_KEY=cambia-esta-clave-en-produccion \
    SUPERSET_LOAD_EXAMPLES=no \
    TALISMAN_ENABLED=False

EXPOSE 8088

# init crea admin si no existe; luego arranca el webserver
ENTRYPOINT ["/bin/bash", "-c", "/superset-init.sh && /usr/bin/run-server.sh"]
