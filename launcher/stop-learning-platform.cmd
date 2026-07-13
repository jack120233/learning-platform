@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

for %%I in ("%~dp0..") do set "APP_ROOT=%%~fI"
set "BACKEND_EXE=%APP_ROOT%\backend\LearningPlatformBackend.exe"
set "DATA_DIR=%APP_ROOT%\data"
set "PID_FILE=%DATA_DIR%\backend.pid"
set "LOG_DIR=%APP_ROOT%\logs"
set "STOP_LOG=%LOG_DIR%\launcher.log"
set "PORT_FILE=%DATA_DIR%\backend.port"
set "HOST=127.0.0.1"
set "PORT=8000"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

if exist "%PORT_FILE%" (
    set /p "PORT="<"%PORT_FILE%"
)

set "TARGET_PID="
if exist "%PID_FILE%" (
    set /p "TARGET_PID="<"%PID_FILE%"
)

if not defined TARGET_PID (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr /r /c:":%PORT% .*LISTENING"') do (
        if not defined TARGET_PID set "TARGET_PID=%%a"
    )
)

if not defined TARGET_PID (
    >>"%STOP_LOG%" echo [%date% %time%] No running Learning Platform process was found.
    if exist "%PID_FILE%" del /q "%PID_FILE%" >nul 2>nul
    if exist "%PORT_FILE%" del /q "%PORT_FILE%" >nul 2>nul
    exit /b 0
)

taskkill /PID %TARGET_PID% /T /F >nul 2>nul
if exist "%PID_FILE%" del /q "%PID_FILE%" >nul 2>nul
if exist "%PORT_FILE%" del /q "%PORT_FILE%" >nul 2>nul
>>"%STOP_LOG%" echo [%date% %time%] Stopped Learning Platform process PID=%TARGET_PID%
exit /b 0
