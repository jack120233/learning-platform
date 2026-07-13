[CmdletBinding()]
param(
    [string]$OutputRoot = "",
    [switch]$SkipFrontendBuild,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"

function Resolve-ExistingCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CommandName
    )

    $command = Get-Command $CommandName -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        return $null
    }

    return $command.Source
}

function Resolve-IsccPath {
    if ($env:ISCC_PATH -and (Test-Path -LiteralPath $env:ISCC_PATH)) {
        return (Resolve-Path -LiteralPath $env:ISCC_PATH).Path
    }

    $fromCommand = Resolve-ExistingCommand -CommandName "ISCC.exe"
    if ($fromCommand) {
        return $fromCommand
    }

    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    return $null
}

function Ensure-Directory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$uiDir = Join-Path $repoRoot "UI"
$backendDir = Join-Path $repoRoot "project_code\backend"
$venvPython = Join-Path $repoRoot "project_code\.venv\Scripts\python.exe"
$releaseRoot = if ($OutputRoot) { $OutputRoot } else { Join-Path $repoRoot "build\windows-release" }
$releaseRoot = [System.IO.Path]::GetFullPath($releaseRoot)
$portableRoot = Join-Path $releaseRoot "bundle"
$pyInstallerRoot = Join-Path $releaseRoot "pyinstaller"
$pyInstallerDist = Join-Path $pyInstallerRoot "dist"
$pyInstallerWork = Join-Path $pyInstallerRoot "build"
$pyInstallerBundle = Join-Path $pyInstallerDist "LearningPlatformBackend"
$installerScript = Join-Path $repoRoot "installer\learning-platform.iss"
$frontendDistDir = Join-Path $uiDir "dist"
$databaseFile = Join-Path $repoRoot "project_code\backend\data\windows-local.db"
$databaseManifestFile = Join-Path $repoRoot "project_code\backend\data\.sqlite-bootstrap.json"
$uploadsDir = Join-Path $repoRoot "project_code\backend\uploads"
$launcherDir = Join-Path $repoRoot "launcher"
$configFile = Join-Path $repoRoot "config\windows-release.env"

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "未找到 Python 虚拟环境：$venvPython"
}

if (-not (Test-Path -LiteralPath $databaseFile)) {
    throw "未找到预制 SQLite 数据库：$databaseFile"
}

if (-not (Test-Path -LiteralPath $databaseManifestFile)) {
    throw "未找到 SQLite bootstrap 清单：$databaseManifestFile"
}

if (-not (Test-Path -LiteralPath $uploadsDir)) {
    throw "未找到课程资源目录：$uploadsDir"
}

if (-not $SkipFrontendBuild) {
    $npmPath = Resolve-ExistingCommand -CommandName "npm.cmd"
    if (-not $npmPath) {
        throw "未找到 npm.cmd，无法构建前端。"
    }

    Push-Location $uiDir
    try {
        & $npmPath run build
        if ($LASTEXITCODE -ne 0) {
            throw "前端构建失败，退出码：$LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}

if (-not (Test-Path -LiteralPath $frontendDistDir)) {
    throw "未找到前端 dist 目录：$frontendDistDir"
}

if (Test-Path -LiteralPath $releaseRoot) {
    Remove-Item -LiteralPath $releaseRoot -Recurse -Force
}

Ensure-Directory -Path $portableRoot
Ensure-Directory -Path $pyInstallerDist
Ensure-Directory -Path $pyInstallerWork

& $venvPython -m PyInstaller `
    --noconfirm `
    --clean `
    --distpath $pyInstallerDist `
    --workpath $pyInstallerWork `
    (Join-Path $backendDir "LearningPlatformBackend.spec")
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller 构建失败，退出码：$LASTEXITCODE"
}

Copy-Item -LiteralPath $pyInstallerBundle -Destination (Join-Path $portableRoot "backend") -Recurse
Ensure-Directory -Path (Join-Path $portableRoot "frontend")
Copy-Item -LiteralPath $frontendDistDir -Destination (Join-Path $portableRoot "frontend\dist") -Recurse

Ensure-Directory -Path (Join-Path $portableRoot "data")
Copy-Item -LiteralPath $databaseFile -Destination (Join-Path $portableRoot "data\windows-local.db")
Copy-Item -LiteralPath $databaseManifestFile -Destination (Join-Path $portableRoot "data\.sqlite-bootstrap.json")
Copy-Item -LiteralPath $uploadsDir -Destination (Join-Path $portableRoot "uploads") -Recurse
Copy-Item -LiteralPath $launcherDir -Destination (Join-Path $portableRoot "launcher") -Recurse

Ensure-Directory -Path (Join-Path $portableRoot "config")
Copy-Item -LiteralPath $configFile -Destination (Join-Path $portableRoot "config\windows-release.env")


if ($SkipInstaller) {
    Write-Host "已生成便携交付目录：$portableRoot"
    exit 0
}

$isccPath = Resolve-IsccPath
if (-not $isccPath) {
    Write-Warning "未找到 Inno Setup 编译器 ISCC.exe，已生成便携交付目录：$portableRoot"
    exit 0
}

$installerOutDir = Join-Path $releaseRoot "installer"
Ensure-Directory -Path $installerOutDir

& $isccPath `
    "/DSourceDir=$portableRoot" `
    "/DOutputDir=$installerOutDir" `
    $installerScript
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup 编译失败，退出码：$LASTEXITCODE"
}

Write-Host "安装包输出目录：$installerOutDir"
