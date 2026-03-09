@echo off
REM ============================================================
REM  build_exe.bat  -  Собрать schedule_analyzer.exe
REM ============================================================

echo [1/3] Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install --upgrade pyinstaller


echo [2/3] Building.exe with PyInstaller...
python -m PyInstaller schedule_analyzer.spec --clean

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: PyInstaller failed to build the executable.
    pause
    exit /b 1
)

echo [3/3] Copying rules_config.yaml near to .exe...
if not exist "dist\rules_config.yaml" (
    copy "src\config\rules_config.yaml" "dist\rules_config.yaml"
    echo     Copied rules_config.yaml to dist\
) else (
    echo     dist\rules_config.yaml already exists, skipping copy.
)

echo.
echo ============================================================
echo  Success! Application is in dir dist\:
echo    dist\schedule_analyzer.exe   - app
echo    dist\rules_config.yaml       - config
echo.
echo  After running the app, you will find in dist\:
echo    dist\templates\              - templates for mapping
echo    dist\schedule_report_*.html  - generated reports
echo ============================================================
pause