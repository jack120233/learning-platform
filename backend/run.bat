@echo off
setlocal
cd /d "%~dp0"

echo Starting FastAPI service...
echo.

set "VENV_PATH=%~dp0..\.venv"
if exist "%VENV_PATH%\Scripts\python.exe" goto VENV_OK

set "VENV_PATH=%~dp0..\..\.venv"
if exist "%VENV_PATH%\Scripts\python.exe" goto VENV_OK

echo [ERROR] Virtual environment not found.
echo Checked:
echo   %~dp0..\.venv
echo   %~dp0..\..\.venv
echo Please verify the virtual environment location and try again.
pause
exit /b 1

:VENV_OK
set "PYTHON=%VENV_PATH%\Scripts\python.exe"

start "" powershell -NoProfile -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8000/docs'"
"%PYTHON%" -m uvicorn app.main:app --reload --port 8000

pause