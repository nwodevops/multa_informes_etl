@echo off
REM Descarga unidades CSEP F2 (Google Sheets) -> H2 STG_GS1_CSEP_MULTAS + STG_GS1_ETAPAS.
REM Windows: reemplaza scripts/stage_csep_sheets.sh (misma logica, python\stage_sheets.py).
setlocal
cd /d "%~dp0.."

set PY=python
if exist ".venv\Scripts\python.exe" set PY=.venv\Scripts\python.exe

echo ==^> Truncate STG_GS1_CSEP_MULTAS + STG_GS1_ETAPAS
"%PY%" "python\stage_sheets.py" csep
set RC=%errorlevel%

endlocal & exit /b %RC%