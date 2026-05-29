@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "POWERSHELL_EXE=powershell.exe"

where pwsh.exe >nul 2>nul
if %ERRORLEVEL% EQU 0 set "POWERSHELL_EXE=pwsh.exe"

"%POWERSHELL_EXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%scripts\start_byulie.ps1" %*
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Byulie failed to start. See the error above.
    pause
)

exit /b %EXIT_CODE%
