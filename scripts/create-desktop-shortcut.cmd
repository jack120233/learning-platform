@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "REPO_ROOT=%%~fI"

set "DESKTOP_PATH=%~1"
set "SHORTCUT_NAME=%~2"
set "BUNDLE_ROOT=%~3"

if not defined SHORTCUT_NAME set "SHORTCUT_NAME=__DEFAULT__"
if not defined BUNDLE_ROOT set "BUNDLE_ROOT=%REPO_ROOT%\build\windows-release\bundle"

set "LAUNCHER_DIR=%BUNDLE_ROOT%\launcher"
set "LAUNCHER_SCRIPT=%LAUNCHER_DIR%\start-learning-platform.vbs"
set "BACKEND_EXE=%BUNDLE_ROOT%\backend\LearningPlatformBackend.exe"
set "WSCRIPT_PATH=%SystemRoot%\System32\wscript.exe"
set "CSCRIPT_PATH=%SystemRoot%\System32\cscript.exe"

if not exist "%BUNDLE_ROOT%" (
    echo [ERROR] Bundle directory was not found:
    echo %BUNDLE_ROOT%
    exit /b 1
)

if not exist "%LAUNCHER_SCRIPT%" (
    echo [ERROR] Launcher script was not found:
    echo %LAUNCHER_SCRIPT%
    exit /b 1
)

if not exist "%WSCRIPT_PATH%" (
    echo [ERROR] Windows Script Host was not found:
    echo %WSCRIPT_PATH%
    exit /b 1
)

if not exist "%CSCRIPT_PATH%" (
    echo [ERROR] CScript was not found:
    echo %CSCRIPT_PATH%
    exit /b 1
)

set "TEMP_VBS=%TEMP%\create-shortcut-%RANDOM%-%RANDOM%.vbs"

(
    echo Set shell = CreateObject("WScript.Shell"^)
    echo Set fso = CreateObject("Scripting.FileSystemObject"^)
    echo desktopPath = WScript.Arguments(0^)
    echo shortcutName = WScript.Arguments(1^)
    echo launcherScript = WScript.Arguments(2^)
    echo launcherDir = WScript.Arguments(3^)
    echo backendExe = WScript.Arguments(4^)
    echo wscriptPath = WScript.Arguments(5^)
    echo If Len(desktopPath^) = 0 Then desktopPath = shell.SpecialFolders("Desktop"^)
    echo If shortcutName = "__DEFAULT__" Then shortcutName = ChrW(^&H8BFE^) ^& ChrW(^&H5802^) ^& ChrW(^&H5E73^) ^& ChrW(^&H53F0^)
    echo If Not fso.FolderExists(desktopPath^) Then fso.CreateFolder desktopPath
    echo shortcutPath = fso.BuildPath(desktopPath, shortcutName ^& ".lnk"^)
    echo Set shortcut = shell.CreateShortcut(shortcutPath^)
    echo shortcut.TargetPath = wscriptPath
    echo shortcut.Arguments = Chr(34^) ^& launcherScript ^& Chr(34^)
    echo shortcut.WorkingDirectory = launcherDir
    echo shortcut.Description = "Launch Classroom Platform"
    echo If fso.FileExists(backendExe^) Then shortcut.IconLocation = backendExe ^& ",0"
    echo shortcut.Save
    echo WScript.Echo "Shortcut created: " ^& shortcutPath
) > "%TEMP_VBS%"

"%CSCRIPT_PATH%" //nologo "%TEMP_VBS%" "%DESKTOP_PATH%" "%SHORTCUT_NAME%" "%LAUNCHER_SCRIPT%" "%LAUNCHER_DIR%" "%BACKEND_EXE%" "%WSCRIPT_PATH%"
set "EXIT_CODE=%ERRORLEVEL%"

del /q "%TEMP_VBS%" >nul 2>nul

if not "%EXIT_CODE%"=="0" exit /b %EXIT_CODE%

echo Target launcher:
echo %LAUNCHER_SCRIPT%
exit /b 0
