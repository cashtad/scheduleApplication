@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ============================================================
REM  build_exe.bat - Build schedule_analyzer variants
REM  Usage:
REM    build_exe.bat onedir
REM    build_exe.bat onefile
REM    build_exe.bat all
REM ============================================================

set "ROOT=%~dp0"
pushd "%ROOT%"

set "VARIANT=%~1"
if "%VARIANT%"=="" set "VARIANT=all"

set "RUNS=%~2"
if "%RUNS%"=="" set "RUNS=3"

echo [1/4] Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install --upgrade pyinstaller
if %ERRORLEVEL% NEQ 0 goto :fail

echo [2/4] Cleaning old build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

set "ARTIFACTS_DIR=artifacts\builds"
if not exist "%ARTIFACTS_DIR%" mkdir "%ARTIFACTS_DIR%"

if /I "%VARIANT%"=="onedir" goto :build_onedir
if /I "%VARIANT%"=="onefile" goto :build_onefile
if /I "%VARIANT%"=="all" goto :build_all

echo ERROR: Unknown variant "%VARIANT%". Use onedir ^| onefile ^| all.
goto :fail

:build_all
call :run_pyinstaller "schedule_analyzer.spec"
if %ERRORLEVEL% NEQ 0 goto :fail
call :post_onedir
if %ERRORLEVEL% NEQ 0 goto :fail

call :run_pyinstaller "schedule_analyzer.onefile.spec"
if %ERRORLEVEL% NEQ 0 goto :fail
call :post_onefile
if %ERRORLEVEL% NEQ 0 goto :fail
goto :done

:build_onedir
call :run_pyinstaller "schedule_analyzer.spec"
if %ERRORLEVEL% NEQ 0 goto :fail
call :post_onedir
if %ERRORLEVEL% NEQ 0 goto :fail
goto :done

:build_onefile
call :run_pyinstaller "schedule_analyzer.onefile.spec"
if %ERRORLEVEL% NEQ 0 goto :fail
call :post_onefile
if %ERRORLEVEL% NEQ 0 goto :fail
goto :done

:run_pyinstaller
echo [3/4] Building with %~1 ...
python -m PyInstaller %~1 --clean
exit /b %ERRORLEVEL%

:post_onedir
set "ONEDIR_EXE=dist\schedule_analyzer\schedule_analyzer.exe"
if not exist "%ONEDIR_EXE%" (
    echo ERROR: Expected file not found: %ONEDIR_EXE%
    exit /b 1
)
if exist "src\rules_config.yaml" (
    copy /Y "src\rules_config.yaml" "dist\schedule_analyzer\rules_config.yaml" >nul
)

if exist "tools\benchmark_startup.py" (
    echo [4/4] Benchmark onedir startup, %RUNS% runs...
    python -u tools\benchmark_startup.py "%ONEDIR_EXE%" --runs %RUNS% --csv "artifacts\builds\startup_metrics.csv" --json "artifacts\builds\onedir_startup.json"
)

for %%F in ("%ONEDIR_EXE%") do echo ONEDIR_SIZE_BYTES=%%~zF
exit /b 0

:post_onefile
set "ONEFILE_EXE=dist\schedule_analyzer_onefile.exe"
if not exist "%ONEFILE_EXE%" (
    echo ERROR: Expected file not found: %ONEFILE_EXE%
    exit /b 1
)
if exist "src\rules_config.yaml" (
    copy /Y "src\rules_config.yaml" "dist\rules_config.yaml" >nul
)

if exist "tools\benchmark_startup.py" (
    echo [4/4] Benchmark onefile startup, %RUNS% runs...
    python -u tools\benchmark_startup.py "%ONEFILE_EXE%" --runs %RUNS% --csv "artifacts\builds\startup_metrics.csv" --json "artifacts\builds\onefile_startup.json"
)

for %%F in ("%ONEFILE_EXE%") do echo ONEFILE_SIZE_BYTES=%%~zF
exit /b 0

:done
echo.
echo ============================================================
echo Success. Build output:
echo - onedir:  dist\schedule_analyzer\schedule_analyzer.exe
echo - onefile: dist\schedule_analyzer_onefile.exe
echo Metrics:
echo - artifacts\builds\startup_metrics.csv
echo ============================================================
popd
exit /b 0

:fail
echo.
echo Build failed.
popd
exit /b 1
