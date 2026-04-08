@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo 正在启动 FastAPI 服务...
echo.

:: 激活虚拟环境
call ..\.venv\Scripts\activate.bat

:: 延时打开 Swagger 文档，避免浏览器早于服务启动
start "" powershell -NoProfile -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8000/docs'"

:: 启动服务
uvicorn app.main:app --reload --port 8000

pause
