@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
pushd "%ROOT%"

set "RUNS=%~1"
if "%RUNS%"=="" set "RUNS=1"

set "ONEDIR_EXE=dist\schedule_analyzer\schedule_analyzer.exe"
if not exist "%ONEDIR_EXE%" (
    echo [1/3] Onedir build not found. Building onedir first...
    call "%ROOT%build_exe.bat" onedir %RUNS%
    if %ERRORLEVEL% NEQ 0 goto :fail
) else (
    echo [1/3] Reusing existing onedir build: %ONEDIR_EXE%
)

set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC (
    for /f "delims=" %%I in ('where ISCC.exe 2^>nul') do (
        set "ISCC=%%I"
        goto :have_iscc
    )
)

:have_iscc
if not defined ISCC (
    echo ERROR: ISCC.exe was not found. Install Inno Setup 6 and retry.
    echo Expected: "%%ProgramFiles(x86)%%\Inno Setup 6\ISCC.exe"
    goto :fail
)

echo [2/3] Building installer with Inno Setup...
if not exist "artifacts\installer" mkdir "artifacts\installer"
"%ISCC%" "installer\schedule_analyzer.iss"
if %ERRORLEVEL% NEQ 0 goto :fail

echo [3/3] Success.
echo Installer output: artifacts\installer\schedule_analyzer_setup.exe
popd
exit /b 0

:fail
echo.
echo Installer build failed.
popd
exit /b 1

