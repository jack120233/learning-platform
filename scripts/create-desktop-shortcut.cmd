@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "REPO_ROOT=%%~fI"

set "DESKTOP_PATH=%~1"
set "SHORTCUT_NAME=%~2"
set "BUNDLE_ROOT=%~3"

if not defined SHORTCUT_NAME set "SHORTCUT_NAME=__DEFAULT__"
if not defined BUNDLE_ROOT set "BUNDLE_ROOT=%REPO_ROOT%\build\windows-release\bundle"

set "CONTROL_PANEL_EXE=%BUNDLE_ROOT%\LearningPlatformControlPanel.exe"
set "CSCRIPT_PATH=%SystemRoot%\System32\cscript.exe"

if not exist "%BUNDLE_ROOT%" (
    echo [ERROR] Bundle directory was not found:
    echo %BUNDLE_ROOT%
    exit /b 1
)
if not exist "%CONTROL_PANEL_EXE%" (
    echo [ERROR] Control panel was not found:
    echo %CONTROL_PANEL_EXE%
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
    echo controlPanelExe = WScript.Arguments(2^)
    echo bundleRoot = WScript.Arguments(3^)
    echo If Len(desktopPath^) = 0 Then desktopPath = shell.SpecialFolders("Desktop"^)
    echo If shortcutName = "__DEFAULT__" Then shortcutName = ChrW(^&H8BFE^) ^& ChrW(^&H5802^) ^& ChrW(^&H5E73^) ^& ChrW(^&H53F0^)
    echo If Not fso.FolderExists(desktopPath^) Then fso.CreateFolder desktopPath
    echo shortcutPath = fso.BuildPath(desktopPath, shortcutName ^& ".lnk"^)
    echo Set shortcut = shell.CreateShortcut(shortcutPath^)
    echo shortcut.TargetPath = controlPanelExe
    echo shortcut.WorkingDirectory = bundleRoot
    echo shortcut.Description = "Open Learning Platform Control Panel"
    echo shortcut.IconLocation = controlPanelExe ^& ",0"
    echo shortcut.Save
    echo WScript.Echo "Shortcut created: " ^& shortcutPath
) > "%TEMP_VBS%"

"%CSCRIPT_PATH%" //nologo "%TEMP_VBS%" "%DESKTOP_PATH%" "%SHORTCUT_NAME%" "%CONTROL_PANEL_EXE%" "%BUNDLE_ROOT%"
set "EXIT_CODE=%ERRORLEVEL%"

del /q "%TEMP_VBS%" >nul 2>nul

if not "%EXIT_CODE%"=="0" exit /b %EXIT_CODE%

echo Target control panel:
echo %CONTROL_PANEL_EXE%
exit /b 0
