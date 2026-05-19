Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Assert-PathExists {
    param(
        [string]$Path,
        [string]$Description
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "$Description not found: $Path"
    }
}

function Invoke-RobocopyCopy {
    param(
        [string]$Source,
        [string]$Destination
    )

    $destinationParent = Split-Path -Parent $Destination
    if ($destinationParent) {
        New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null
    }

    New-Item -ItemType Directory -Path $Destination -Force | Out-Null

    $robocopyArgs = @(
        $Source
        $Destination
        "/E"
        "/R:2"
        "/W:1"
        "/NFL"
        "/NDL"
        "/NJH"
        "/NJS"
        "/XD"
        "__pycache__"
        ".pytest_cache"
        "/XF"
        "*.pyc"
        "*.pyo"
    )

    & robocopy @robocopyArgs | Out-Null
    $exitCode = $LASTEXITCODE
    if ($exitCode -gt 7) {
        throw "robocopy failed for '$Source' -> '$Destination' with exit code $exitCode"
    }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$uiDir = Join-Path $repoRoot "UI"
$backendDir = Join-Path $repoRoot "project_code\backend"
$venvPython = Join-Path $repoRoot "project_code\.venv\Scripts\python.exe"
$configFile = Join-Path $repoRoot "config\windows-local.env"
$launcherFile = Join-Path $repoRoot "start-windows-local.cmd"
$packageReadme = Join-Path $scriptDir "package-readme.txt"
$releaseRoot = Join-Path $repoRoot "release\windows-local"

Write-Step "Validating branch"
$currentBranch = (& git -C $repoRoot branch --show-current).Trim()
if ([string]::IsNullOrWhiteSpace($currentBranch) -and $env:GITHUB_REF_NAME) {
    $currentBranch = $env:GITHUB_REF_NAME.Trim()
}
if ($currentBranch -ne "future/windows-local") {
    throw "Expected branch 'future/windows-local' but found '$currentBranch'"
}

Write-Step "Validating inputs"
Assert-PathExists -Path $venvPython -Description "Windows Python runtime"
Assert-PathExists -Path $configFile -Description "Windows local config file"
Assert-PathExists -Path $launcherFile -Description "Windows launcher"
Assert-PathExists -Path $packageReadme -Description "Package README template"
Assert-PathExists -Path (Join-Path $uiDir "package.json") -Description "UI package.json"
Assert-PathExists -Path (Join-Path $backendDir "app") -Description "Backend app directory"
Assert-PathExists -Path (Join-Path $backendDir "scripts") -Description "Backend scripts directory"
Assert-PathExists -Path (Join-Path $backendDir "requirements.txt") -Description "Backend requirements file"

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw "npm.cmd is required on the build machine to generate UI/dist"
}

Write-Step "Reading application version"
Push-Location $backendDir
try {
    $appVersion = (& $venvPython -c "from app.config import settings; print(settings.app_version)").Trim()
}
finally {
    Pop-Location
}

if ([string]::IsNullOrWhiteSpace($appVersion)) {
    throw "Unable to resolve app version from backend settings"
}

$versionRoot = Join-Path $releaseRoot $appVersion
$packageRoot = Join-Path $versionRoot "learning-platform"
$zipPath = Join-Path $versionRoot "learning-platform-windows-local-$appVersion.zip"

Write-Step "Building frontend production bundle"
Push-Location $uiDir
try {
    & npm.cmd run build
}
finally {
    Pop-Location
}

$frontendIndex = Join-Path $uiDir "dist\index.html"
Assert-PathExists -Path $frontendIndex -Description "Built frontend index"

Write-Step "Preparing release directory"
if (Test-Path -LiteralPath $packageRoot) {
    Remove-Item -LiteralPath $packageRoot -Recurse -Force
}
if (Test-Path -LiteralPath $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

New-Item -ItemType Directory -Path $packageRoot -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $packageRoot "config") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $packageRoot "UI") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $packageRoot "project_code\backend") -Force | Out-Null

Write-Step "Copying release files"
Copy-Item -LiteralPath $launcherFile -Destination (Join-Path $packageRoot "start-windows-local.cmd")
Copy-Item -LiteralPath $configFile -Destination (Join-Path $packageRoot "config\windows-local.env")
Copy-Item -LiteralPath $packageReadme -Destination (Join-Path $packageRoot "README.txt")
Copy-Item -LiteralPath (Join-Path $backendDir "requirements.txt") -Destination (Join-Path $packageRoot "project_code\backend\requirements.txt")

Invoke-RobocopyCopy -Source (Join-Path $uiDir "dist") -Destination (Join-Path $packageRoot "UI\dist")
Invoke-RobocopyCopy -Source (Join-Path $repoRoot "project_code\.venv") -Destination (Join-Path $packageRoot "project_code\.venv")
Invoke-RobocopyCopy -Source (Join-Path $backendDir "app") -Destination (Join-Path $packageRoot "project_code\backend\app")
Invoke-RobocopyCopy -Source (Join-Path $backendDir "scripts") -Destination (Join-Path $packageRoot "project_code\backend\scripts")

New-Item -ItemType Directory -Path (Join-Path $packageRoot "project_code\backend\data") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $packageRoot "project_code\backend\logs") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $packageRoot "project_code\backend\uploads") -Force | Out-Null

Write-Step "Creating ZIP archive"
Compress-Archive -Path $packageRoot -DestinationPath $zipPath -CompressionLevel Optimal

Write-Step "Package ready"
Write-Host "Version: $appVersion"
Write-Host "Directory: $packageRoot"
Write-Host "Archive: $zipPath"
