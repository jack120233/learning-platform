@echo off
setlocal
cd /d "%~dp0"

set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%project_code\backend"
set "FRONTEND_DIR=%ROOT_DIR%UI"
set "BACKEND_RUN=%BACKEND_DIR%\run.bat"

if not exist "%BACKEND_RUN%" (
    echo [ERROR] Backend script not found:
    echo %BACKEND_RUN%
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%\package.json" (
    echo [ERROR] Frontend project not found:
    echo %FRONTEND_DIR%
    pause
    exit /b 1
)

echo ==========================================
echo Project Startup Launcher
echo ==========================================
echo.
echo Workspace: %CD%
echo.
echo 1. Start backend service
echo 2. Start frontend service
echo 3. Start both services
echo.
choice /c 123 /n /m "Select 1, 2, or 3: "

if errorlevel 3 goto BOTH
if errorlevel 2 goto FRONTEND
if errorlevel 1 goto BACKEND

:BACKEND
echo [Backend] Starting in a new window...
start "Learning-Backend" /D "%BACKEND_DIR%" cmd /k "call run.bat"
goto END

:FRONTEND
echo [Frontend] Starting in a new window...
start "Learning-Frontend" /D "%FRONTEND_DIR%" cmd /k "npm run dev"
goto END

:BOTH
echo [Backend] Starting in a new window...
start "Learning-Backend" /D "%BACKEND_DIR%" cmd /k "call run.bat"
echo [Frontend] Starting in a new window...
start "Learning-Frontend" /D "%FRONTEND_DIR%" cmd /k "npm run dev"
goto END

:END
echo.
echo Startup commands have been sent.
echo.
pause
