# Sesión activa — rama `linux_v2` / `windows_v2`

## Feature activa

Ninguna `in_progress`. Última cerrada: `canonico-flaco-enrich-py`.

## Hecho reciente

- Oracle flaco: enrich en pandas. Sin `DW_M_FACT_MC_*` publicadas.
- `./init.sh` HARNESS OK (1271 = 990+281; 0153/64).

## Siguiente

1. PC Win: `git checkout windows_v2` → `.\switch-env.ps1 remote` → `init.bat`.
2. Si Win OK → retomar `fase-remote-deploy` (criterio: enriquecida + AUD, sin facts evidencia).
3. Merge a `linux` / `windows` cuando se pida.
