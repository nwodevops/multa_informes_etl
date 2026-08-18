@echo off
setlocal
echo Deteniendo H2 Server si existe...

REM Mata procesos Java cuyo comando incluye org.h2.tools.Server
for /f "tokens=2 delims==" %%P in ('wmic process where "CommandLine like '%%org.h2.tools.Server%%'" get ProcessId /value 2^>nul ^| findstr "ProcessId"') do (
  echo Kill PID %%P
  taskkill /F /PID %%P >nul 2>&1
)

ping -n 3 127.0.0.1 >nul
echo Stop H2 listo
endlocal
exit /b 0
