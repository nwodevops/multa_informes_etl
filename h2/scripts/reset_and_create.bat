@echo off
setlocal
cd /d "%~dp0\.."

set H2_JAR=lib\h2-2.4.240.jar
if not exist "%H2_JAR%" set H2_JAR=h2-2.4.240.jar
set "DB_H2_URL=jdbc:h2:tcp://localhost:9092/mem:csep;DB_CLOSE_DELAY=-1;MODE=Oracle;DATABASE_TO_UPPER=TRUE;DEFAULT_NULL_ORDERING=HIGH;AUTO_RECONNECT=TRUE"

REM H2 es in-memory (mem:csep): al parar el server se limpia sola.
REM Por eso el DDL se aplica por TCP DESPUES del start (no embedded como nefa_hop).

echo === Stop H2 (limpia mem) ===
call scripts\stop_h2.bat

echo === Start H2 TCP (mem:csep) ===
call scripts\start_h2.bat
if errorlevel 1 (
  echo FAIL start
  exit /b 1
)

echo === Aplicar DDL (sql\00_reset.sql) ===
java -cp "%H2_JAR%" org.h2.tools.RunScript -url "%DB_H2_URL%" -user sa -password csep -script "sql\00_reset.sql"
if errorlevel 1 (
  echo FAIL reset
  exit /b 1
)

echo === Aplicar DDL (sql\01_schema.sql) ===
java -cp "%H2_JAR%" org.h2.tools.RunScript -url "%DB_H2_URL%" -user sa -password csep -script "sql\01_schema.sql"
if errorlevel 1 (
  echo FAIL schema
  exit /b 1
)

echo === Reset+Create OK ===
echo Pipelines / R usan: %DB_H2_URL%
endlocal
exit /b 0
