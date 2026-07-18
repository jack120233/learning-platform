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
$controlPanelExe = Join-Path $resolvedBundleRoot "LearningPlatformControlPanel.exe"
$resolvedDesktopPath = if ($DesktopPath) {
    Resolve-AbsolutePath -Path $DesktopPath
} else {
    [Environment]::GetFolderPath("Desktop")
}

if (-not (Test-Path -LiteralPath $resolvedBundleRoot)) {
    throw "未找到 bundle 目录：$resolvedBundleRoot"
}
if (-not (Test-Path -LiteralPath $controlPanelExe)) {
    throw "未找到控制面板：$controlPanelExe"
}
if (-not (Test-Path -LiteralPath $resolvedDesktopPath)) {
    New-Item -ItemType Directory -Path $resolvedDesktopPath -Force | Out-Null
}

$shortcutPath = Join-Path $resolvedDesktopPath "$ShortcutName.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $controlPanelExe
$shortcut.WorkingDirectory = $resolvedBundleRoot
$shortcut.Description = "打开学习平台控制面板"
$shortcut.IconLocation = "$controlPanelExe,0"
$shortcut.Save()

Write-Host "桌面快捷方式已创建：$shortcutPath"
Write-Host "目标控制面板：$controlPanelExe"
