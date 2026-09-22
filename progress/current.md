# Sesión activa — rama `linux_v2` / `windows_v2`

## Feature activa

`f4-mysql-aud-fact` (`in_progress`).

## Hecho reciente

- F4 cableado: STG_MYSQL_MULTAS → AUD_F4_GAPPS + filas GAPPS al fact (sin lookup SISUD).

## Siguiente

1. Corrida Hop/MySQL: `./switch-env.sh local` (o remote) + `./init.sh` → HARNESS OK.
2. Confirmar `enriquecida = AUD_F2+AUD_F1+AUD_F4` y `ID_FUENTE=GAPPS` en las filas nuevas.
