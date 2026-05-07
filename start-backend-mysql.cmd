@echo off
setlocal

set "ROOT=E:\video_project\proj_ui"
set "BACKEND_ROOT=%ROOT%\project_code\backend"
set "LOG_ROOT=%ROOT%\logs"
set "PYTHON_EXE=%ROOT%\project_code\.venv\Scripts\python.exe"

if not exist "%LOG_ROOT%" mkdir "%LOG_ROOT%"

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
  taskkill /PID %%a /F >nul 2>nul
)

start "" /b cmd /c "cd /d ""%BACKEND_ROOT%""&& ""%PYTHON_EXE%"" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 1> ""%LOG_ROOT%\backend-mysql.out.log"" 2> ""%LOG_ROOT%\backend-mysql.err.log"""

timeout /t 8 /nobreak >nul
curl -s http://127.0.0.1:8000/api/v1/health
