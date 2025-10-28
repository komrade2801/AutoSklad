@echo off
setlocal enabledelayedexpansion

REM AutoSklad Virtual Environment Setup Script
REM Deletes and recreates virtual environments, installs requirements

echo.
echo AutoSklad Virtual Environment Setup Script
echo ===========================================
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
echo Setting up components: %COMPONENTS%
echo.

REM Check if directories exist
if "%COMPONENTS%"=="both" (
    if not exist "client" (
        echo ERROR: client directory not found
        goto :eof
    )
    if not exist "server" (
        echo ERROR: server directory not found
        goto :eof
    )
    set COMPONENT_LIST=server client
) else if "%COMPONENTS%"=="client" (
    if not exist "client" (
        echo ERROR: client directory not found
        goto :eof
    )
    set COMPONENT_LIST=client
) else if "%COMPONENTS%"=="server" (
    if not exist "server" (
        echo ERROR: server directory not found
        goto :eof
    )
    set COMPONENT_LIST=server
)

echo This will delete and recreate virtual environments in:
for %%c in (%COMPONENT_LIST%) do (
    echo   - %%c\venv\
)
echo.

set /p CONFIRM="Proceed? (y/N): "
if /i not "!CONFIRM!"=="y" goto :cancel

echo.
echo Starting setup...

set SUCCESS_COUNT=0
set FAIL_COUNT=0

for %%c in (%COMPONENT_LIST%) do (
    echo.
    echo Processing %%c...
    
    REM Change to component directory
    cd %%c
    
    REM Remove existing venv if it exists
    if exist venv (
        echo Removing existing venv...
        rmdir /s /q venv >nul
    )
    
    REM Create new venv
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create venv for %%c
        set /a FAIL_COUNT+=1
        cd ..
        goto :continue
    )
    
    REM Activate and upgrade pip
    echo Activating venv and upgrading pip...
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        echo ERROR: Failed to activate venv for %%c
        set /a FAIL_COUNT+=1
        cd ..
        goto :continue
    )
    
    python -m pip install --upgrade pip wheel
    if errorlevel 1 (
        echo ERROR: Failed to upgrade pip for %%c
        set /a FAIL_COUNT+=1
        cd ..
        goto :continue
    )
    
    REM Install requirements
    if exist requirements.txt (
        echo Installing requirements...
        pip install -r requirements.txt
        if errorlevel 1 (
            echo ERROR: Failed to install requirements for %%c
            set /a FAIL_COUNT+=1
            cd ..
            goto :continue
        )
    ) else (
        echo WARNING: requirements.txt not found in %%c, skipping installation
    )
    
    echo SUCCESS: %%c setup completed
    set /a SUCCESS_COUNT+=1
    
    cd ..
    
    :continue
)

echo.
echo Setup Summary:
echo - Successful: %SUCCESS_COUNT%
echo - Failed: %FAIL_COUNT%

if %FAIL_COUNT% equ 0 (
    echo SUCCESS: All components setup successfully!
) else (
    echo WARNING: Some components failed to setup
)

goto :eof

:cancel
echo Operation cancelled.
goto :eof
