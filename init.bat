@echo off
setlocal enabledelayedexpansion
REM Harness — verificacion e inicializacion del ETL (capa Python + staging Excel).
REM Equivalente Windows de init.sh (post-pull).
cd /d "%~dp0"

set RED=[91m
set GREEN=[92m
set YELLOW=[93m
set NC=[0m

REM --- Python ---
set PY=python
if exist ".venv\Scripts\python.exe" set PY=.venv\Scripts\python.exe

REM --- Hop ---
if not defined HOP_RUN set "HOP_RUN=%USERPROFILE%\apps\hop\hop-run.sh"
set HOP_PROJECT=multa_informes_etl

REM --- Temp log ---
set LOG=%TEMP%\etl_init_%RANDOM%.log
if exist "%LOG%" del "%LOG%"

echo %GREEN%==>%NC% Validando feature_list.json (max. una in_progress)
"%PY%" -c "import json,sys; d=json.loads(open('feature_list.json',encoding='utf-8').read()); act=[f for f in d.get('features',[]) if f.get('status')=='in_progress']; print(f'features: {len(d.get(\"features\",[]))}, in_progress: {len(act)}') if len(act)<=1 else sys.exit(f'mas de una feature in_progress: {[f[\"id\"] for f in act]}')"
if errorlevel 1 (
    echo %RED%FAIL:%NC% feature_list.json validation failed
    exit /b 1
)

echo %GREEN%==>%NC% Prerrequisitos (java, venv, inputs)
where java >nul 2>&1
if errorlevel 1 (
    echo %RED%FAIL:%NC% java no esta en PATH ^(requerido para H2^)
    exit /b 1
)
if not exist "inputs.yaml" (
    echo %RED%FAIL:%NC% inputs.yaml no encontrado
    exit /b 1
)
if not exist "h2\lib\h2-2.4.240.jar" (
    echo %RED%FAIL:%NC% jar H2 no encontrado en h2\lib\
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    echo %YELLOW%AVISO:%NC% venv ausente; crear con: python -m venv .venv ^&^& pip install -r python\requirements.txt
)

echo %GREEN%==>%NC% Reset H2 + DDL STG
call h2\scripts\reset_and_create.bat
if errorlevel 1 (
    echo %RED%FAIL:%NC% reset_and_create.bat failed
    exit /b 1
)

echo %GREEN%==>%NC% Python create STG (inputs.yaml -^> tablas STG_*)
"%PY%" python\create_stg.py
if errorlevel 1 (
    echo %RED%FAIL:%NC% create_stg.py failed
    exit /b 1
)

echo %GREEN%==>%NC% Staging Excel local (Hop pl_stage_excel)
where hop-run >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%AVISO:%NC% hop-run no encontrado; STG Excel puede quedar vacio
) else (
    hop-run -j "%HOP_PROJECT%" -f "%CD%\pipelines\pl_stage_excel.hpl" -r local
)

echo %GREEN%==>%NC% Staging Oracle / MySQL ^(Hop directo^)
where hop-run >nul 2>&1
if errorlevel 1 (
    echo %RED%FAIL:%NC% hop-run no encontrado; requerido para staging Oracle/MySQL
    exit /b 1
)
hop-run -j "%HOP_PROJECT%" -f "%CD%\pipelines\pl_stage_oracle.hpl" -r local
hop-run -j "%HOP_PROJECT%" -f "%CD%\pipelines\pl_stage_informes.hpl" -r local
hop-run -j "%HOP_PROJECT%" -f "%CD%\pipelines\pl_stage_mysql.hpl" -r local

echo %GREEN%==>%NC% Python main (logica Fases 2-7 + carga DW)
"%PY%" python\main.py > "%LOG%" 2>&1
set MAIN_RC=%errorlevel%
if not %MAIN_RC%==0 (
    echo %RED%FAIL:%NC% python/main.py termino con codigo %MAIN_RC%
    type "%LOG%"
    del "%LOG%"
    exit /b 1
)

echo %GREEN%==>%NC% Comprobando salidas minimas en log
findstr /C:"Salida PROF_" "%LOG%" >nul 2>&1
if errorlevel 1 (
    echo %RED%FAIL:%NC% no hay salida PROF_* en el log
    type "%LOG%"
    del "%LOG%"
    exit /b 1
)
findstr /C:"Salida MI_DIM_" "%LOG%" >nul 2>&1
if errorlevel 1 (
    echo %RED%FAIL:%NC% no hay salida MI_DIM_* en el log
    type "%LOG%"
    del "%LOG%"
    exit /b 1
)
findstr /C:"Salida MI_FACT_" "%LOG%" >nul 2>&1
if errorlevel 1 (
    echo %RED%FAIL:%NC% no hay salida MI_FACT_* en el log
    type "%LOG%"
    del "%LOG%"
    exit /b 1
)
findstr /C:"Salida MI_INDICADOR_RESULTADO" "%LOG%" >nul 2>&1
if errorlevel 1 (
    echo %RED%FAIL:%NC% no hay MI_INDICADOR_RESULTADO en el log
    type "%LOG%"
    del "%LOG%"
    exit /b 1
)

echo %GREEN%==>%NC% Verificando carga DW
findstr /C:"DW:" "%LOG%" >nul 2>&1
if errorlevel 1 (
    echo %RED%FAIL:%NC% sin lineas DW: en log ^(carga Oracle obligatoria^)
    type "%LOG%"
    del "%LOG%"
    exit /b 1
)
findstr /C:"REVISAR" "%LOG%" >nul 2>&1
if not errorlevel 1 (
    echo %RED%FAIL:%NC% carga DW con tablas en REVISAR
    type "%LOG%"
    del "%LOG%"
    exit /b 1
)
findstr /C:"(OK)" "%LOG%" >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%AVISO:%NC% carga DW sin lineas ^(OK^); revisar credenciales oracle_dw
)

echo %GREEN%==>%NC% Verificacion Oracle K1-K5
"%PY%" -c "import sys; sys.path.insert(0,'python'); from config import require_live_conn, load_vars; from pathlib import Path; require_live_conn('oracle_dw',load_vars(Path('.')))" >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%AVISO:%NC% Oracle DW omitido ^(credenciales placeholder^)
) else (
    echo %GREEN%==>%NC% Oracle DW configurado, verificando indicadores...
    "%PY%" -c "import sys; sys.path.insert(0,'python'); import oracledb; from config import require_live_conn, load_vars; from pathlib import Path; cv=require_live_conn('oracle_dw',load_vars(Path('.'))); dsn=oracledb.makedsn(cv['host'],int(cv['port'] or '1521'),service_name=cv['database']); conn=oracledb.connect(user=cv['username'],password=cv['password'],dsn=dsn); cur=conn.cursor(); cur.execute('SELECT COUNT(*) FROM APP.MI_INDICADOR_RESULTADO'); print(f'MI_INDICADOR_RESULTADO: {cur.fetchone()[0]} filas en Oracle'); cur.execute('SELECT DISTINCT COD_INDICADOR FROM APP.MI_INDICADOR_RESULTADO ORDER BY 1'); codes={r[0] for r in cur.fetchall()}; missing=sorted({'K1','K2','K3','K4','K5'}-codes); sys.exit(f'faltan indicadores en Oracle: {missing}') if missing else print('Indicadores K1-K5 presentes')"
    if errorlevel 1 (
        echo %RED%FAIL:%NC% Verificacion Oracle K1-K5 fallo
        del "%LOG%"
        exit /b 1
    )
)

del "%LOG%" >nul 2>&1
echo.
echo %GREEN%HARNESS OK%NC% — ver CHECKPOINTS.md y docs\verification.md
exit /b 0
