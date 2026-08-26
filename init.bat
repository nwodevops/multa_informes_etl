@echo off
setlocal enabledelayedexpansion
REM Harness — verificacion e inicializacion del ETL (capa Python + staging Excel).
REM Equivalente Windows de init.sh (post-pull).
REM Log persistente: output\init_win_YYYYMMDD_HHMMSS.log
cd /d "%~dp0"

set RED=[91m
set GREEN=[92m
set YELLOW=[93m
set NC=[0m

REM --- Log de corrida Windows (no se borra al final) ---
if not exist "output" mkdir output
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set STAMP=%%i
set "RUN_LOG=%CD%\output\init_win_%STAMP%.log"
set "LOG=%RUN_LOG%"
(
  echo === init.bat Windows harness ===
  echo start: %DATE% %TIME%
  echo cwd: %CD%
  echo computer: %COMPUTERNAME%
  echo user: %USERNAME%
  echo.
) > "%RUN_LOG%"
echo %GREEN%==>%NC% Log de corrida: %RUN_LOG%

REM --- Python ---
set PY=python
if exist ".venv\Scripts\python.exe" set PY=.venv\Scripts\python.exe

REM --- Hop (Windows: hop-run.bat; override con set HOP_RUN=...) ---
REM Orden: HOP_RUN env > D:\Eder\hop > %USERPROFILE%\apps\hop > PATH
if not defined HOP_RUN (
    if exist "D:\Eder\hop\hop-run.bat" (
        set "HOP_RUN=D:\Eder\hop\hop-run.bat"
    ) else if exist "%USERPROFILE%\apps\hop\hop-run.bat" (
        set "HOP_RUN=%USERPROFILE%\apps\hop\hop-run.bat"
    ) else if exist "%USERPROFILE%\apps\hop\hop-run.cmd" (
        set "HOP_RUN=%USERPROFILE%\apps\hop\hop-run.cmd"
    ) else (
        set "HOP_RUN=hop-run"
    )
)
set HOP_PROJECT=multa_informes_etl
echo PY=%PY%>> "%RUN_LOG%"
echo HOP_RUN=%HOP_RUN%>> "%RUN_LOG%"
echo HOP_PROJECT=%HOP_PROJECT%>> "%RUN_LOG%"
echo.>> "%RUN_LOG%"
echo %GREEN%==>%NC% HOP_RUN=%HOP_RUN%

call :step "Validando feature_list.json (max. una in_progress)"
"%PY%" -c "import json,sys; d=json.loads(open('feature_list.json',encoding='utf-8').read()); act=[f for f in d.get('features',[]) if f.get('status')=='in_progress']; print(f'features: {len(d.get(\"features\",[]))}, in_progress: {len(act)}') if len(act)<=1 else sys.exit(f'mas de una feature in_progress: {[f[\"id\"] for f in act]}')" >> "%RUN_LOG%" 2>&1
if errorlevel 1 (
    type "%RUN_LOG%"
    call :fail "feature_list.json validation failed"
    exit /b 1
)
findstr /C:"features:" "%RUN_LOG%"

call :step "Prerrequisitos (java, venv, inputs)"
where java >nul 2>&1
if errorlevel 1 (
    call :fail "java no esta en PATH (requerido para H2)"
    exit /b 1
)
if not exist "inputs.yaml" (
    call :fail "inputs.yaml no encontrado"
    exit /b 1
)
if not exist "h2\lib\h2-2.4.240.jar" (
    call :fail "jar H2 no encontrado en h2\lib\"
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    call :warn "venv ausente; crear con: python -m venv .venv && .venv\Scripts\pip install -r python\requirements.txt"
)

call :step "Reset H2 + DDL STG"
call h2\scripts\reset_and_create.bat >> "%RUN_LOG%" 2>&1
if errorlevel 1 (
    call :fail "reset_and_create.bat failed"
    exit /b 1
)

call :step "Python create STG (inputs.yaml -> tablas STG_*)"
"%PY%" python\create_stg.py >> "%RUN_LOG%" 2>&1
if errorlevel 1 (
    call :fail "create_stg.py failed"
    exit /b 1
)

call :step "Staging Excel local (Hop pl_stage_excel)"
if /I "%HOP_RUN%"=="hop-run" (
    where hop-run >nul 2>&1
    if errorlevel 1 (
        call :warn "hop-run no encontrado; STG Excel puede quedar vacio"
        goto :after_excel
    )
) else if not exist "%HOP_RUN%" (
    call :warn "hop-run no encontrado (%HOP_RUN%); STG Excel puede quedar vacio"
    goto :after_excel
)
call "%HOP_RUN%" -j "%HOP_PROJECT%" -f "%CD%\pipelines\pl_stage_excel.hpl" -r local >> "%RUN_LOG%" 2>&1
:after_excel

call :step "Staging Oracle / MySQL (Hop directo)"
if /I "%HOP_RUN%"=="hop-run" (
    where hop-run >nul 2>&1
    if errorlevel 1 (
        call :fail "hop-run no encontrado; requerido para staging Oracle/MySQL"
        exit /b 1
    )
) else if not exist "%HOP_RUN%" (
    call :fail "hop-run no encontrado (%HOP_RUN%); requerido para staging Oracle/MySQL"
    exit /b 1
)
call "%HOP_RUN%" -j "%HOP_PROJECT%" -f "%CD%\pipelines\pl_stage_oracle.hpl" -r local >> "%RUN_LOG%" 2>&1
if errorlevel 1 (
    call :fail "pl_stage_oracle.hpl failed"
    exit /b 1
)
call "%HOP_RUN%" -j "%HOP_PROJECT%" -f "%CD%\pipelines\pl_stage_informes.hpl" -r local >> "%RUN_LOG%" 2>&1
if errorlevel 1 (
    call :fail "pl_stage_informes.hpl failed"
    exit /b 1
)
call "%HOP_RUN%" -j "%HOP_PROJECT%" -f "%CD%\pipelines\pl_stage_mysql.hpl" -r local >> "%RUN_LOG%" 2>&1
if errorlevel 1 (
    call :fail "pl_stage_mysql.hpl failed"
    exit /b 1
)

call :step "Python main (logica Fases 2-7 + carga DW)"
echo --- python\main.py --->> "%RUN_LOG%"
"%PY%" python\main.py >> "%RUN_LOG%" 2>&1
set MAIN_RC=%errorlevel%
if not %MAIN_RC%==0 (
    call :fail "python/main.py termino con codigo %MAIN_RC%"
    exit /b 1
)

call :step "Comprobando salidas minimas en log"
findstr /C:"Salida PROF_" "%LOG%" >nul 2>&1
if errorlevel 1 (
    call :fail "no hay salida PROF_* en el log"
    exit /b 1
)
findstr /C:"Salida MI_DIM_" "%LOG%" >nul 2>&1
if errorlevel 1 (
    call :fail "no hay salida MI_DIM_* en el log"
    exit /b 1
)
findstr /C:"Salida MI_FACT_" "%LOG%" >nul 2>&1
if errorlevel 1 (
    call :fail "no hay salida MI_FACT_* en el log"
    exit /b 1
)
findstr /C:"Salida MI_INDICADOR_RESULTADO" "%LOG%" >nul 2>&1
if errorlevel 1 (
    call :fail "no hay MI_INDICADOR_RESULTADO en el log"
    exit /b 1
)

call :step "Verificando carga DW"
findstr /C:"DW:" "%LOG%" >nul 2>&1
if errorlevel 1 (
    call :fail "sin lineas DW: en log (carga Oracle obligatoria)"
    exit /b 1
)
findstr /C:"REVISAR" "%LOG%" >nul 2>&1
if not errorlevel 1 (
    call :fail "carga DW con tablas en REVISAR"
    exit /b 1
)
findstr /C:"(OK)" "%LOG%" >nul 2>&1
if errorlevel 1 (
    call :warn "carga DW sin lineas (OK); revisar credenciales oracle_dw"
)

call :step "Verificacion Oracle K1-K5"
"%PY%" -c "import sys; sys.path.insert(0,'python'); from config import require_live_conn, load_vars; from pathlib import Path; require_live_conn('oracle_dw',load_vars(Path('.')))" >nul 2>&1
if errorlevel 1 (
    call :warn "Oracle DW omitido (credenciales placeholder)"
) else (
    echo %GREEN%==>%NC% Oracle DW configurado, verificando indicadores...
    echo ==> Oracle DW configurado, verificando indicadores...>> "%RUN_LOG%"
    "%PY%" -c "import sys; sys.path.insert(0,'python'); import oracledb; from config import require_live_conn, load_vars; from pathlib import Path; cv=require_live_conn('oracle_dw',load_vars(Path('.'))); dsn=oracledb.makedsn(cv['host'],int(cv['port'] or '1521'),service_name=cv['database']); conn=oracledb.connect(user=cv['username'],password=cv['password'],dsn=dsn); cur=conn.cursor(); cur.execute('SELECT COUNT(*) FROM APP.MI_INDICADOR_RESULTADO'); print(f'MI_INDICADOR_RESULTADO: {cur.fetchone()[0]} filas en Oracle'); cur.execute('SELECT DISTINCT COD_INDICADOR FROM APP.MI_INDICADOR_RESULTADO ORDER BY 1'); codes={r[0] for r in cur.fetchall()}; missing=sorted({'K1','K2','K3','K4','K5'}-codes); sys.exit(f'faltan indicadores en Oracle: {missing}') if missing else print('Indicadores K1-K5 presentes')" >> "%RUN_LOG%" 2>&1
    if errorlevel 1 (
        call :fail "Verificacion Oracle K1-K5 fallo"
        exit /b 1
    )
    findstr /C:"MI_INDICADOR_RESULTADO:" "%RUN_LOG%"
    findstr /C:"Indicadores K1-K5" "%RUN_LOG%"
)

(
  echo.
  echo === HARNESS OK ===
  echo end: %DATE% %TIME%
  echo log: %RUN_LOG%
) >> "%RUN_LOG%"
echo.
echo %GREEN%HARNESS OK%NC% — ver CHECKPOINTS.md y docs\verification.md
echo %GREEN%==>%NC% Log guardado: %RUN_LOG%
exit /b 0

REM ---------- helpers ----------
:step
echo %GREEN%==>%NC% %~1
echo.>> "%RUN_LOG%"
echo ==^> %~1>> "%RUN_LOG%"
goto :eof

:warn
echo %YELLOW%AVISO:%NC% %~1
echo AVISO: %~1>> "%RUN_LOG%"
goto :eof

:fail
echo %RED%FAIL:%NC% %~1
echo FAIL: %~1>> "%RUN_LOG%"
echo end: %DATE% %TIME%>> "%RUN_LOG%"
echo Log guardado: %RUN_LOG%
echo --- tail log ---
powershell -NoProfile -Command "Get-Content -LiteralPath '%RUN_LOG%' -Tail 40"
goto :eof
