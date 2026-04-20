@echo off
setlocal
cd /d "%~dp0"

set "BACKEND_DIR=%~dp0"
set "VENV_PATH=%~dp0..\.venv"
if exist "%VENV_PATH%\Scripts\python.exe" goto VENV_OK

set "VENV_PATH=%~dp0..\..\.venv"
if exist "%VENV_PATH%\Scripts\python.exe" goto VENV_OK

echo [ERROR] 未找到虚拟环境。
echo 已检查:
echo   %~dp0..\.venv
echo   %~dp0..\..\.venv
echo 请确认虚拟环境位置后重试。
pause
exit /b 1

:VENV_OK
set "PYTHON=%VENV_PATH%\Scripts\python.exe"
set "PYTHONPATH=%BACKEND_DIR%"

echo 正在启动 FastAPI 服务...
echo 工作目录: %BACKEND_DIR%
echo Python: %PYTHON%
echo.

"%PYTHON%" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ERROR] 服务启动失败，退出码: %EXIT_CODE%
    echo 上面的输出就是实际报错信息。
    pause
    exit /b %EXIT_CODE%
)

echo.
echo 服务已退出。
pause
exit /b 0