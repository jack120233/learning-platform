@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "ROOT_DIR=%~dp0"
set "CONFIG_FILE=%ROOT_DIR%config\windows-local.env"
set "BACKEND_DIR=%ROOT_DIR%project_code\backend"
set "UI_DIR=%ROOT_DIR%UI"
set "PYTHON_EXE=%ROOT_DIR%project_code\.venv\Scripts\python.exe"
set "LOG_DIR=%BACKEND_DIR%\logs"
set "STARTUP_LOG=%LOG_DIR%\windows-local-startup.log"
set "STARTUP_ERROR_LOG=%LOG_DIR%\windows-local-startup-error.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo ==========================================
echo Windows Local Learning Platform
echo ==========================================
echo Workspace: %ROOT_DIR%
echo Logs: %LOG_DIR%
echo.

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python virtual environment not found:
    echo %PYTHON_EXE%
    echo Please prepare project_code\.venv before launching.
    >> "%STARTUP_ERROR_LOG%" echo [%date% %time%] Python virtual environment not found: %PYTHON_EXE%
    pause
    exit /b 1
)

if not exist "%CONFIG_FILE%" (
    echo [ERROR] Missing config file:
    echo %CONFIG_FILE%
    >> "%STARTUP_ERROR_LOG%" echo [%date% %time%] Missing config file: %CONFIG_FILE%
    pause
    exit /b 1
)

for /f "usebackq eol=# tokens=1,* delims==" %%a in ("%CONFIG_FILE%") do (
    if not "%%a"=="" set "%%a=%%b"
)

if not defined APP_EDITION set "APP_EDITION=windows_local"
if not defined HOST set "HOST=127.0.0.1"
if not defined PORT set "PORT=8000"
if not defined CACHE_BACKEND set "CACHE_BACKEND=auto"
set "PYTHONPATH=%BACKEND_DIR%"

if not exist "%UI_DIR%\dist\index.html" (
    echo Frontend production bundle not found. Building UI...
    if not exist "%UI_DIR%\package.json" (
        echo [ERROR] Frontend project not found: %UI_DIR%
        >> "%STARTUP_ERROR_LOG%" echo [%date% %time%] Frontend project not found: %UI_DIR%
        pause
        exit /b 1
    )
    pushd "%UI_DIR%"
    call npm.cmd run build
    set "BUILD_EXIT=%ERRORLEVEL%"
    popd
    if not "%BUILD_EXIT%"=="0" (
        echo [ERROR] Frontend build failed. See console output above.
        >> "%STARTUP_ERROR_LOG%" echo [%date% %time%] Frontend build failed, exit=%BUILD_EXIT%
        pause
        exit /b %BUILD_EXIT%
    )
)

set "PORT_PID="
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /c:":%PORT% " ^| findstr "LISTENING"') do set "PORT_PID=%%a"
if defined PORT_PID (
    echo [ERROR] Port %PORT% is already in use. PID=%PORT_PID%
    echo Please close the existing process and retry.
    >> "%STARTUP_ERROR_LOG%" echo [%date% %time%] Port %PORT% is already in use. PID=%PORT_PID%
    pause
    exit /b 1
)

>> "%STARTUP_LOG%" echo ==================================================
>> "%STARTUP_LOG%" echo [%date% %time%] Starting Windows local backend
>> "%STARTUP_LOG%" echo APP_EDITION=%APP_EDITION%, HOST=%HOST%, PORT=%PORT%, CACHE_BACKEND=%CACHE_BACKEND%

start "Learning Platform Backend" /D "%BACKEND_DIR%" cmd /d /s /c ""%PYTHON_EXE%" -m uvicorn app.main:app --host %HOST% --port %PORT% 1>>"%STARTUP_LOG%" 2>>"%STARTUP_ERROR_LOG%""

echo Waiting for backend health check...
set "READY="
for /l %%i in (1,1,40) do (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-WebRequest -UseBasicParsing 'http://%HOST%:%PORT%/' -TimeoutSec 2; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>nul
    if not errorlevel 1 (
        set "READY=1"
        goto READY
    )
    timeout /t 1 /nobreak >nul
)

:READY
if not defined READY (
    echo [ERROR] Backend did not become ready.
    echo Startup log: %STARTUP_LOG%
    echo Error log: %STARTUP_ERROR_LOG%
    >> "%STARTUP_ERROR_LOG%" echo [%date% %time%] Backend health check timed out.
    pause
    exit /b 1
)

echo Backend is ready. Opening browser...
start "" "http://%HOST%:%PORT%/"
echo.
echo Windows local edition is running.
echo URL: http://%HOST%:%PORT%/
echo Logs: %LOG_DIR%
echo.
pause
exit /b 0
