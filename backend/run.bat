@echo off
chcp 65001 >nul
echo 正在启动 FastAPI 服务...
echo.

:: 激活虚拟环境
call ..\.venv\Scripts\activate

:: 启动服务
uvicorn app.main:app --reload --port 8000

pause