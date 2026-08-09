@echo off
REM ============================================================
REM  ACTUALIZAR.bat  -  Rappi (un solo doble clic)
REM ------------------------------------------------------------
REM  IMPORTANTE: este .bat NUNCA borra los dias viejos.
REM  Solo AGREGA el CSV nuevo del dia a la carpeta scrapeos\.
REM  build_data.py lee TODOS los CSV de scrapeos\ -> historico completo.
REM
REM  Que hace:
REM   1) Toma el CSV que dejo tu scraper (rappi_cervezas.csv) desde tu
REM      carpeta de scraping y lo copia a scrapeos\ con la fecha de HOY.
REM   2) Regenera data.json con TODOS los dias.
REM   3) Sube a GitHub. La web se actualiza sola en ~1 min.
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ==========================================
echo   Actualizando Rappi (historico se conserva)
echo ==========================================
echo.

REM --- Fecha de hoy AAAAMMDD (tolera dd/MM/aaaa) ---
for /f "tokens=1-3 delims=/.- " %%a in ("%date%") do (
  set P1=%%a& set P2=%%b& set P3=%%c
)
REM si el ano quedo en P3 (formato dd/MM/aaaa)
if "%P3%" GEQ "2000" ( set AAAA=%P3%& set MM=%P2%& set DD=%P1% ) else ( set AAAA=%P1%& set MM=%P2%& set DD=%P3% )
set HOY=%AAAA%%MM%%DD%
echo [Fecha de hoy] %HOY%

REM --- 1) De donde tomo el CSV del scraper ---
REM  Ajusta esta ruta si tu scraper deja el CSV en otro lado.
set "SCRAPER_CSV=C:\Users\29036488\VS Code\rappi_cervezas.csv"

set "ORIGEN="
if exist "%SCRAPER_CSV%" set "ORIGEN=%SCRAPER_CSV%"
REM si no esta ahi, busca el mas nuevo en esta carpeta y en la de arriba
if not defined ORIGEN (
  for /f "delims=" %%f in ('dir /b /a-d /o-d "rappi_cervezas*.csv" 2^>nul') do if not defined ORIGEN set "ORIGEN=%%f"
)
if not defined ORIGEN (
  for /f "delims=" %%f in ('dir /b /a-d /o-d "..\rappi_cervezas*.csv" 2^>nul') do if not defined ORIGEN set "ORIGEN=..\%%f"
)
if not defined ORIGEN (
  echo [ERROR] No encontre rappi_cervezas.csv.
  echo         Corre tu scraper, o revisa la ruta SCRAPER_CSV arriba en este .bat
  echo.& pause & exit /b 1
)
echo [CSV del dia] %ORIGEN%

REM --- 2) Copiar a scrapeos con la fecha de hoy (NO borra nada) ---
if not exist "scrapeos" mkdir "scrapeos"
set "DESTINO=scrapeos\rappi_cervezas_%HOY%_120000.csv"
copy /y "%ORIGEN%" "%DESTINO%" >nul
echo [Agregado al historico] %DESTINO%

REM --- 3) Regenerar data.json con TODOS los dias ---
echo.
echo [Procesando historico completo...]
py build_data.py
if errorlevel 1 ( echo [ERROR] Fallo build_data.py.& echo.& pause & exit /b 1 )

REM --- 4) Subir a GitHub ---
echo.
echo [Subiendo a GitHub...]
git add -A
git commit -m "Actualizacion precios %HOY%" 1>nul 2>nul
git push
if errorlevel 1 (
  echo [AVISO] push normal fallo, intento forzar...
  git push --force
)

echo.
echo ==========================================
echo   LISTO. En ~1 min la web muestra el dia nuevo:
echo   https://mazurramiro-cyber.github.io/rappi-cmq/
echo ==========================================
echo.
pause
