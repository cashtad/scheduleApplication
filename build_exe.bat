@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ============================================================
REM  build_exe.bat - Vytvoření schedule_analyzer (onedir)
REM  Lokalizace: čeština
REM ============================================================

set "ROOT=%~dp0"
pushd "%ROOT%"

echo [1/3] Instaluji závislosti...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install --upgrade pyinstaller
if %ERRORLEVEL% NEQ 0 goto :fail

echo [2/3] Čistím staré build artefakty...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

call :build_onedir
if %ERRORLEVEL% NEQ 0 goto :fail
goto :done

:build_onedir
call :run_pyinstaller "schedule_analyzer.spec"
if %ERRORLEVEL% NEQ 0 goto :fail
call :post_onedir
if %ERRORLEVEL% NEQ 0 goto :fail

:run_pyinstaller
echo [3/3] Stavím aplikaci s %~1 ...
python -m PyInstaller %~1 --clean
exit /b %ERRORLEVEL%

:post_onedir
set "ONEDIR_EXE=dist\schedule_analyzer\schedule_analyzer.exe"
if not exist "%ONEDIR_EXE%" (
    echo CHYBA: Očekávaný soubor nenalezen: %ONEDIR_EXE%
    exit /b 1
)
if exist "src\rules_config.yaml" (
    copy /Y "src\rules_config.yaml" "dist\schedule_analyzer\rules_config.yaml" >nul
)
exit /b 0

:done
echo.
echo ============================================================
echo Úspěšně vytvořeno! Výstup buildu:
echo - schedule_analyzer.exe: dist\schedule_analyzer\schedule_analyzer.exe
echo ============================================================
popd
exit /b 0

:fail
echo.
echo Build selhal.
popd
exit /b 1
