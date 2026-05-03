@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ============================================================
REM  build_exe.bat - Creating schedule_analyzer (onedir)
REM ============================================================

set "ROOT=%~dp0"
pushd "%ROOT%"

echo [1/3] Installing required Python packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install --upgrade pyinstaller
if %ERRORLEVEL% NEQ 0 goto :fail

echo [2/3] Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo [3/3] Running PyInstaller with spec file: schedule_analyzer.spec
python -m PyInstaller "schedule_analyzer.spec" --clean
if %ERRORLEVEL% NEQ 0 goto :fail

set "ONEDIR_EXE=dist\schedule_analyzer\Schedule Analyzer.exe"
if not exist "%ONEDIR_EXE%" (
    echo ERROR: Build failed, executable not found at %ONEDIR_EXE%
    goto :fail
)

echo.
echo ============================================================
echo Successfully built. Output executable:
echo - Schedule Analyzer.exe: dist\schedule_analyzer\Schedule Analyzer.exe
echo ============================================================
popd
exit /b 0

:fail
echo.
echo Build failed.
popd
exit /b 1