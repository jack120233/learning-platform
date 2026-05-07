@echo off
setlocal
cd /d "%~dp0"

set "BACKEND_DIR=%~dp0"
set "LOG_DIR=%BACKEND_DIR%logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "STARTUP_LOG=%LOG_DIR%\startup.log"
set "STARTUP_ERROR_LOG=%LOG_DIR%\startup_error.log"

set "VENV_PATH=%~dp0..\.venv"
if exist "%VENV_PATH%\Scripts\python.exe" goto VENV_OK

set "VENV_PATH=%~dp0..\..\.venv"
if exist "%VENV_PATH%\Scripts\python.exe" goto VENV_OK

echo [ERROR] 未找到虚拟环境。
echo 已检查:
echo   %~dp0..\.venv
echo   %~dp0..\..\.venv
echo 请确认虚拟环境位置后重试。
>> "%STARTUP_ERROR_LOG%" echo [%date% %time%] 未找到虚拟环境。
pause
exit /b 1

:VENV_OK
set "PYTHON=%VENV_PATH%\Scripts\python.exe"
set "PYTHONPATH=%BACKEND_DIR%"

set "PORT_PID="
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /c:":8000 " ^| findstr "LISTENING"') do set "PORT_PID=%%a"

if defined PORT_PID (
    echo [ERROR] 端口 8000 已被占用 PID=%PORT_PID%
    echo 启动已取消，请先释放端口后重试。
    >> "%STARTUP_ERROR_LOG%" echo [%date% %time%] 端口 8000 被占用 PID=%PORT_PID%
    pause
    exit /b 1
)

echo 正在启动 FastAPI 服务...
echo 工作目录: %BACKEND_DIR%
echo Python: %PYTHON%
echo 启动日志: %STARTUP_LOG%
echo 错误摘要: %STARTUP_ERROR_LOG%
echo.

>> "%STARTUP_LOG%" echo ==================================================
>> "%STARTUP_LOG%" echo [%date% %time%] 启动命令: "%PYTHON%" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

"%PYTHON%" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ERROR] 服务启动失败，退出码: %EXIT_CODE%
    >> "%STARTUP_ERROR_LOG%" echo [%date% %time%] 服务启动失败，退出码: %EXIT_CODE%
    pause
    exit /b %EXIT_CODE%
)

echo.
echo 服务已退出。
pause
exit /b 0
