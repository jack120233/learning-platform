@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

for %%I in ("%~dp0..") do set "APP_ROOT=%%~fI"
set "CONFIG_FILE=%APP_ROOT%\config\windows-release.env"
set "BACKEND_DIR=%APP_ROOT%\backend"
set "BACKEND_EXE=%BACKEND_DIR%\LearningPlatformBackend.exe"
set "FRONTEND_DIST_DIR=%APP_ROOT%\frontend\dist"
set "FRONTEND_INDEX_PATH=%FRONTEND_DIST_DIR%\index.html"
set "DATA_DIR=%APP_ROOT%\data"
set "CACHE_DIR=%DATA_DIR%\cache"
set "UPLOAD_DIR=%APP_ROOT%\uploads"
set "LOG_DIR=%APP_ROOT%\logs"
set "PID_FILE=%DATA_DIR%\backend.pid"
set "PORT_FILE=%DATA_DIR%\backend.port"
set "STARTUP_LOG=%LOG_DIR%\launcher.log"

if exist "%CONFIG_FILE%" (
    for /f "usebackq eol=# tokens=1,* delims==" %%a in ("%CONFIG_FILE%") do (
        if not "%%a"=="" set "%%a=%%b"
    )
)

if not defined HOST set "HOST=127.0.0.1"
if not defined PORT set "PORT=8000"
set "DEFAULT_PORT=%PORT%"
if not defined ENVIRONMENT set "ENVIRONMENT=production"
if not defined DEBUG set "DEBUG=false"
if not defined CACHE_BACKEND set "CACHE_BACKEND=auto"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%CACHE_DIR%" mkdir "%CACHE_DIR%"
if not exist "%UPLOAD_DIR%" mkdir "%UPLOAD_DIR%"

set "LEARNING_PLATFORM_RUNTIME_ROOT=%APP_ROOT%"
set "APP_RUNTIME_ROOT=%APP_ROOT%"
set "LOCAL_DATA_DIR=%DATA_DIR%"
set "LOCAL_CACHE_DIR=%CACHE_DIR%"
set "UPLOAD_DIR=%UPLOAD_DIR%"
set "LOG_DIR=%LOG_DIR%"
set "FRONTEND_DIST_DIR=%FRONTEND_DIST_DIR%"
set "FRONTEND_INDEX_PATH=%FRONTEND_INDEX_PATH%"
set "LOCAL_DATABASE_FILENAME=windows-local.db"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

call :log Launcher start: checking runtime state

if not exist "%BACKEND_EXE%" (
    call :show_error Backend executable was not found. Please reinstall the package.
    exit /b 1
)

if not exist "%FRONTEND_INDEX_PATH%" (
    call :show_error Frontend files were not found. Please reinstall the package.
    exit /b 1
)

if exist "%PID_FILE%" if exist "%PORT_FILE%" (
    set /p "EXISTING_PID="<"%PID_FILE%"
    set /p "EXISTING_PORT="<"%PORT_FILE%"
    if defined EXISTING_PORT (
        powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-WebRequest -UseBasicParsing 'http://%HOST%:!EXISTING_PORT!/' -TimeoutSec 2; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>nul
        if not errorlevel 1 (
            set "PORT=!EXISTING_PORT!"
            call :log Existing instance is healthy: PID=!EXISTING_PID!, PORT=!EXISTING_PORT!
            goto open_browser
        )
    )
    del /q "%PID_FILE%" >nul 2>nul
    del /q "%PORT_FILE%" >nul 2>nul
)

set "PORT="
for /f %%p in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$start=[int]'%DEFAULT_PORT%'; $end=$start+99; for($port=$start; $port -le $end; $port++){ $listener=$null; try { $listener=[System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse('%HOST%'), $port); $listener.Start(); $port; break } catch {} finally { if($listener){ $listener.Stop() } } }"') do (
    set "PORT=%%p"
)

if not defined PORT (
    call :show_error No available local port was found from %DEFAULT_PORT% to %DEFAULT_PORT%+99.
    exit /b 1
)

call :log Selected local port: %PORT% (default was %DEFAULT_PORT%)

start "" /D "%BACKEND_DIR%" "%BACKEND_EXE%"
>"%PORT_FILE%" echo %PORT%
call :log Backend launch requested. Waiting for health check.

set "READY="
for /l %%i in (1,1,40) do (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-WebRequest -UseBasicParsing 'http://%HOST%:%PORT%/' -TimeoutSec 2; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>nul
    if not errorlevel 1 (
        set "READY=1"
        goto startup_ready
    )
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 1" >nul 2>nul
)

:startup_ready
if not "%READY%"=="1" (
    call :log Health check timed out.
    del /q "%PID_FILE%" >nul 2>nul
    del /q "%PORT_FILE%" >nul 2>nul
    call :show_error Startup timed out. Check launcher.log and backend logs for details.
    exit /b 1
)

set "BACKEND_PID="
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /r /c:":%PORT% .*LISTENING"') do (
    if not defined BACKEND_PID set "BACKEND_PID=%%a"
)

if defined BACKEND_PID (
    >"%PID_FILE%" echo %BACKEND_PID%
    call :log Backend is listening: PID=%BACKEND_PID%, PORT=%PORT%.
) else (
    call :log Backend is listening on PORT=%PORT%, but PID could not be resolved.
)

call :log Service is ready. Opening login page.

:open_browser
start "" "http://%HOST%:%PORT%/login"
exit /b 0

:show_error
call :log ERROR: %*
powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('%*', 'Learning Platform') | Out-Null" >nul 2>nul
exit /b 0

:log
>>"%STARTUP_LOG%" echo [%date% %time%] %*
exit /b 0
