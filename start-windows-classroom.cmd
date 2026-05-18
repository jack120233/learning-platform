@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "ROOT_DIR=%~dp0"
set "CONFIG_FILE=%ROOT_DIR%config\windows-classroom.env"
set "BACKEND_DIR=%ROOT_DIR%project_code\backend"
set "UI_DIR=%ROOT_DIR%UI"
set "PYTHON_EXE=%ROOT_DIR%project_code\.venv\Scripts\python.exe"
set "LOG_DIR=%BACKEND_DIR%\logs"
set "STARTUP_LOG=%LOG_DIR%\windows-classroom-startup.log"
set "STARTUP_ERROR_LOG=%LOG_DIR%\windows-classroom-startup-error.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo ==========================================
echo Windows Classroom Learning Platform
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

if not defined APP_EDITION set "APP_EDITION=windows_classroom"
if not defined HOST set "HOST=0.0.0.0"
if not defined PORT set "PORT=8000"
if not defined CACHE_BACKEND set "CACHE_BACKEND=auto"
if not defined SQLITE_BUSY_TIMEOUT_MS set "SQLITE_BUSY_TIMEOUT_MS=30000"
set "PYTHONPATH=%BACKEND_DIR%"

if /I not "%APP_EDITION%"=="windows_classroom" (
    echo [ERROR] APP_EDITION must be windows_classroom for classroom launch.
    echo Current APP_EDITION=%APP_EDITION%
    >> "%STARTUP_ERROR_LOG%" echo [%date% %time%] Invalid APP_EDITION=%APP_EDITION%
    pause
    exit /b 1
)

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

set "LAN_IP="
for /f "usebackq delims=" %%a in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$ips = @(Get-NetIPAddress -AddressFamily IPv4 ^| Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' -and $_.AddressState -eq 'Preferred' } ^| Sort-Object InterfaceMetric ^| Select-Object -ExpandProperty IPAddress); if ($ips.Count -gt 0) { $ips[0] }"`) do (
    set "LAN_IP=%%a"
    goto LAN_IP_FOUND
)

:LAN_IP_FOUND
set "LOCAL_URL=http://127.0.0.1:%PORT%/"
if /I not "%HOST%"=="0.0.0.0" set "LOCAL_URL=http://%HOST%:%PORT%/"

if defined LAN_IP (
    set "LAN_URL=http://%LAN_IP%:%PORT%/"
) else (
    set "LAN_URL="
)

>> "%STARTUP_LOG%" echo ==================================================
>> "%STARTUP_LOG%" echo [%date% %time%] Starting Windows classroom backend
>> "%STARTUP_LOG%" echo APP_EDITION=%APP_EDITION%, HOST=%HOST%, PORT=%PORT%, CACHE_BACKEND=%CACHE_BACKEND%, SQLITE_BUSY_TIMEOUT_MS=%SQLITE_BUSY_TIMEOUT_MS%
if defined LAN_IP (
    >> "%STARTUP_LOG%" echo LAN_IP=%LAN_IP%
) else (
    >> "%STARTUP_LOG%" echo LAN_IP not detected
)

start "Learning Platform Classroom Backend" /D "%BACKEND_DIR%" cmd /d /s /c ""%PYTHON_EXE%" -m uvicorn app.main:app --host %HOST% --port %PORT% 1>>"%STARTUP_LOG%" 2>>"%STARTUP_ERROR_LOG%""

echo Waiting for backend health check...
set "READY="
for /l %%i in (1,1,40) do (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-WebRequest -UseBasicParsing '%LOCAL_URL%' -TimeoutSec 2; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>nul
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

echo.
echo Windows classroom edition is running.
echo Local URL: %LOCAL_URL%
if defined LAN_URL (
    echo LAN URL: %LAN_URL%
    echo Students must connect to the same LAN and open the LAN URL.
) else (
    echo [WARN] LAN IP was not detected.
    echo Please check Wi-Fi/Ethernet connection and Windows firewall rules.
)
echo Logs: %LOG_DIR%
echo.
echo If LAN devices cannot connect, allow port %PORT% through Windows Firewall.
echo.
start "" "%LOCAL_URL%"
pause
exit /b 0
