@echo off
REM Descarga las 31 ODs F1 (Google Sheets) -> H2 STG_GS2_OD_MULTAS.
REM Windows: reemplaza scripts/stage_ods_sheets.sh (misma logica, python\stage_sheets.py).
setlocal
cd /d "%~dp0.."

set PY=python
if exist ".venv\Scripts\python.exe" set PY=.venv\Scripts\python.exe

echo ==^> Truncate STG_GS2_OD_MULTAS
"%PY%" "python\stage_sheets.py" ods
set RC=%errorlevel%

endlocal & exit /b %RC%