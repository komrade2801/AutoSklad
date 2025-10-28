@echo off
setlocal enabledelayedexpansion

REM AutoSklad Application Startup Script
REM Launches server and/or client in new CMD windows

echo.
echo AutoSklad Application Startup Script
echo ====================================
echo.

if "%~1"=="" (
    set COMPONENTS=both
    goto :get_components
)

if "%~1"=="client" (
    set COMPONENTS=client
) else if "%~1"=="server" (
    set COMPONENTS=server
) else if "%~1"=="both" (
    set COMPONENTS=both
) else (
    echo ERROR: Invalid component. Use 'client', 'server', or 'both'
    goto :eof
)

:get_components
echo Starting components: %COMPONENTS%

REM Handle mocks flag
set MOCKS=0
if "%~2"=="mocks" set MOCKS=1
if "%~3"=="mocks" set MOCKS=1

if %MOCKS% equ 1 (
    echo Client mock mode: Enabled
)
echo.

REM Check components
if "%COMPONENTS%"=="both" (
    if not exist "server\venv" (
        echo ERROR: server\venv not found. Run venv_setup.bat first.
        goto :eof
    )
    if not exist "client\venv" (
        echo ERROR: client\venv not found. Run venv_setup.bat first.
        goto :eof
    )
    set COMPONENT_LIST=server client
) else if "%COMPONENTS%"=="client" (
    if not exist "client\venv" (
        echo ERROR: client\venv not found. Run venv_setup.bat first.
        goto :eof
    )
    set COMPONENT_LIST=client
) else if "%COMPONENTS%"=="server" (
    if not exist "server\venv" (
        echo ERROR: server\venv not found. Run venv_setup.bat first.
        goto :eof
    )
    set COMPONENT_LIST=server
)

echo This will start the following in new CMD windows:
for %%c in (%COMPONENT_LIST%) do (
    echo   - %%c application
)
if %MOCKS% equ 1 if "%COMPONENTS%"=="client" echo   - Mock mode for client
if %MOCKS% equ 1 if "%COMPONENTS%"=="both" echo   - Mock mode for client
echo.

set /p CONFIRM="Proceed? (y/N): "
if /i not "!CONFIRM!"=="y" goto :cancel

echo.
echo Starting applications...

set STARTED_COUNT=0

for %%c in (%COMPONENT_LIST%) do (
    echo Starting %%c...
    
    if "%%c"=="server" (
        REM Start server in new CMD window
        start "AutoSklad Server" cmd /k "cd /d %CD%\server && call venv\Scripts\activate.bat && python main.py"
        set /a STARTED_COUNT+=1
    ) else if "%%c"=="client" (
        REM Start client in new CMD window
        if %MOCKS% equ 1 (
            start "AutoSklad Client (Mock)" cmd /k "cd /d %CD%\client && call venv\Scripts\activate.bat && set AUTOSKLAD_USE_MOCKS=1 && python main.py"
        ) else (
            start "AutoSklad Client" cmd /k "cd /d %CD%\client && call venv\Scripts\activate.bat && python main.py"
        )
        set /a STARTED_COUNT+=1
    )
    
    REM Small delay between starts
    timeout /t 2 /nobreak >nul
)

echo.
echo Startup Summary:
echo - Applications started: %STARTED_COUNT%

echo SUCCESS: Applications launched in new CMD windows!
echo Check the new windows for application output.

goto :eof

:cancel
echo Operation cancelled.
goto :eof
