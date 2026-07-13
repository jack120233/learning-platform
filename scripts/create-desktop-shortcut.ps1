[CmdletBinding()]
param(
    [string]$ShortcutName = "课堂平台",
    [string]$BundleRoot = "",
    [string]$DesktopPath = ""
)

$ErrorActionPreference = "Stop"

function Resolve-AbsolutePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    return [System.IO.Path]::GetFullPath($Path)
}

$repoRoot = Resolve-AbsolutePath -Path (Join-Path $PSScriptRoot "..")
$resolvedBundleRoot = if ($BundleRoot) {
    Resolve-AbsolutePath -Path $BundleRoot
} else {
    Resolve-AbsolutePath -Path (Join-Path $repoRoot "build\windows-release\bundle")
}

$launcherDir = Join-Path $resolvedBundleRoot "launcher"
$launcherScript = Join-Path $launcherDir "start-learning-platform.vbs"
$backendExe = Join-Path $resolvedBundleRoot "backend\LearningPlatformBackend.exe"
$resolvedDesktopPath = if ($DesktopPath) {
    Resolve-AbsolutePath -Path $DesktopPath
} else {
    [Environment]::GetFolderPath("Desktop")
}

if (-not (Test-Path -LiteralPath $resolvedBundleRoot)) {
    throw "未找到 bundle 目录：$resolvedBundleRoot"
}

if (-not (Test-Path -LiteralPath $launcherScript)) {
    throw "未找到启动脚本：$launcherScript"
}

if (-not (Test-Path -LiteralPath $resolvedDesktopPath)) {
    New-Item -ItemType Directory -Path $resolvedDesktopPath -Force | Out-Null
}

$shortcutPath = Join-Path $resolvedDesktopPath "$ShortcutName.lnk"
$wscriptPath = Join-Path $env:WINDIR "System32\wscript.exe"

if (-not (Test-Path -LiteralPath $wscriptPath)) {
    throw "未找到 Windows Script Host：$wscriptPath"
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $wscriptPath
$shortcut.Arguments = '"' + $launcherScript + '"'
$shortcut.WorkingDirectory = $launcherDir
$shortcut.Description = "启动课堂平台"
if (Test-Path -LiteralPath $backendExe) {
    $shortcut.IconLocation = $backendExe
}
$shortcut.Save()

Write-Host "桌面快捷方式已创建：$shortcutPath"
Write-Host "目标启动器：$launcherScript"
