# Sesión activa — rama `linux_v2` / `windows_v2`

## Feature activa

Ninguna `in_progress`. Última cerrada: `fact-siete-campos`.

## Hecho reciente

- Siete campos en el fact (planilla + admin SISUD si `-1` + sombras res/UIT).
- Oracle flaco: enrich en pandas. Sin `DW_M_FACT_MC_*` publicadas.

## Siguiente

1. PC Win: `git checkout windows_v2` → `.\switch-env.ps1 remote` → `init.bat` (materializa las 6 columnas nuevas).
2. Si Win OK → retomar `fase-remote-deploy`.
3. Merge a `linux` / `windows` cuando se pida.
