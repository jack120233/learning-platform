@echo off
setlocal

set "ROOT=E:\video_project\proj_ui"
set "BACKEND_ROOT=%ROOT%\project_code\backend"
set "UI_ROOT=%ROOT%\UI"
set "LOG_ROOT=%ROOT%\logs"
set "PYTHON_EXE=%ROOT%\project_code\.venv\Scripts\python.exe"
set "RELAY_EXE=C:\Users\Administrator\.agents\skills\autoglm-browser-agent\dist\relay.exe"
set "SQLITE_URL=sqlite+aiosqlite:///E:/video_project/proj_ui/project_code/backend/data/local-dev.db"

if not exist "%LOG_ROOT%" mkdir "%LOG_ROOT%"
if not exist "%BACKEND_ROOT%\data" mkdir "%BACKEND_ROOT%\data"

tasklist | findstr /i "relay.exe" >nul
if errorlevel 1 start "" /b "%RELAY_EXE%"

set "DATABASE_URL=%SQLITE_URL%"
set "ENVIRONMENT=development"
set "DEBUG=true"

pushd "%BACKEND_ROOT%"
"%PYTHON_EXE%" scripts\init_db.py
if errorlevel 1 exit /b 1
popd

netstat -ano | findstr ":8000" >nul
if errorlevel 1 (
  start "" /b cmd /c "set DATABASE_URL=%SQLITE_URL%&& set ENVIRONMENT=development&& set DEBUG=true&& cd /d ""%BACKEND_ROOT%""&& ""%PYTHON_EXE%"" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 1> ""%LOG_ROOT%\backend.out.log"" 2> ""%LOG_ROOT%\backend.err.log"""
)

netstat -ano | findstr ":3000" >nul
if errorlevel 1 (
  start "" /b cmd /c "cd /d ""%UI_ROOT%""&& npm.cmd run dev 1> ""%LOG_ROOT%\frontend.out.log"" 2> ""%LOG_ROOT%\frontend.err.log"""
)

timeout /t 12 /nobreak >nul

echo ---HTTP8000---
powershell -NoProfile -Command "try{(Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8000/api/v1/health').Content}catch{Write-Output $_.Exception.Message}"
echo ---HTTP3000---
powershell -NoProfile -Command "try{(Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:3000/login').StatusCode}catch{Write-Output $_.Exception.Message}"
echo ---NETSTAT---
netstat -ano | findstr ":8000 :3000"
