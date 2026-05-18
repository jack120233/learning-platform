param(
    [string]$Port = "8000",
    [string]$VideoPath = ""
)

$ErrorActionPreference = "Stop"

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$configFile = Join-Path $rootDir "config\windows-classroom.env"
$pythonExe = Join-Path $rootDir "project_code\.venv\Scripts\python.exe"
$dbPath = Join-Path $rootDir "project_code\backend\data\windows-classroom.db"
$startupLog = Join-Path $rootDir "project_code\backend\logs\windows-classroom-startup.log"
$errorLog = Join-Path $rootDir "project_code\backend\logs\windows-classroom-startup-error.log"
$uiDist = Join-Path $rootDir "UI\dist\index.html"
$localUrl = "http://127.0.0.1:$Port/"

function Write-Section($title) {
    Write-Host ""
    Write-Host "=== $title ===" -ForegroundColor Cyan
}

function Test-Http($url) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 5
        return @{
            Ok = $true
            StatusCode = [int]$response.StatusCode
        }
    } catch {
        $statusCode = $null
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }
        return @{
            Ok = $false
            StatusCode = $statusCode
            Error = $_.Exception.Message
        }
    }
}

function Invoke-Python($code) {
    & $pythonExe -c $code
}

Write-Host "Windows classroom verification helper" -ForegroundColor Green
Write-Host "Root: $rootDir"

Write-Section "Files"
foreach ($item in @(
    @{ Label = "Config"; Path = $configFile },
    @{ Label = "Python"; Path = $pythonExe },
    @{ Label = "UI dist"; Path = $uiDist },
    @{ Label = "Database"; Path = $dbPath },
    @{ Label = "Startup log"; Path = $startupLog },
    @{ Label = "Error log"; Path = $errorLog }
)) {
    $exists = Test-Path $item.Path
    Write-Host ("{0,-12}: {1}" -f $item.Label, $(if ($exists) { "OK" } else { "MISSING" }))
    if ($exists) {
        Write-Host "  $($item.Path)"
    }
}

Write-Section "Config"
if (Test-Path $configFile) {
    $configMap = @{}
    foreach ($line in Get-Content $configFile) {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.TrimStart().StartsWith("#")) {
            continue
        }
        $parts = $line -split "=", 2
        if ($parts.Count -eq 2) {
            $configMap[$parts[0].Trim()] = $parts[1].Trim()
        }
    }

    foreach ($key in @("APP_EDITION", "HOST", "PORT", "CACHE_BACKEND", "SQLITE_BUSY_TIMEOUT_MS")) {
        Write-Host ("{0,-24}: {1}" -f $key, $configMap[$key])
    }
}

Write-Section "HTTP"
$rootResponse = Test-Http $localUrl
if ($rootResponse.Ok) {
    Write-Host ("Root URL           : OK ({0})" -f $rootResponse.StatusCode)
} else {
    Write-Host ("Root URL           : FAIL ({0}) {1}" -f $rootResponse.StatusCode, $rootResponse.Error) -ForegroundColor Yellow
}

foreach ($path in @("courses", "profile")) {
    $response = Test-Http ($localUrl + $path)
    if ($response.Ok) {
        Write-Host ("SPA /{0,-12}: OK ({1})" -f $path, $response.StatusCode)
    } else {
        Write-Host ("SPA /{0,-12}: FAIL ({1}) {2}" -f $path, $response.StatusCode, $response.Error) -ForegroundColor Yellow
    }
}

foreach ($path in @("api/unknown", "api/v1/unknown", "uploads/not-exist.png")) {
    $response = Test-Http ($localUrl + $path)
    if (-not $response.Ok -and $response.StatusCode -eq 404) {
        Write-Host ("404 /{0,-16}: OK (404)" -f $path)
    } else {
        Write-Host ("404 /{0,-16}: CHECK ({1})" -f $path, $response.StatusCode) -ForegroundColor Yellow
    }
}

Write-Section "SQLite"
if ((Test-Path $pythonExe) -and (Test-Path $dbPath)) {
    $journalMode = Invoke-Python "import sqlite3; c=sqlite3.connect(r'$dbPath'); print(c.execute('PRAGMA journal_mode').fetchone()[0]); c.close()"
    Write-Host ("journal_mode       : {0}" -f $journalMode)
} else {
    Write-Host "journal_mode       : skipped (missing python or database)" -ForegroundColor Yellow
}

Write-Section "Range"
if ([string]::IsNullOrWhiteSpace($VideoPath)) {
    Write-Host "Range check        : skipped (pass -VideoPath uploads/<path>)"
} else {
    $rangeUrl = if ($VideoPath.StartsWith("/")) { "$localUrl$($VideoPath.TrimStart('/'))" } else { "$localUrl$VideoPath" }
    try {
        $rangeResponse = Invoke-WebRequest -UseBasicParsing -Uri $rangeUrl -Headers @{ Range = "bytes=0-1023" } -TimeoutSec 10
        Write-Host ("Range status       : {0}" -f [int]$rangeResponse.StatusCode)
        Write-Host ("Content-Range      : {0}" -f $rangeResponse.Headers["Content-Range"])
        Write-Host ("Accept-Ranges      : {0}" -f $rangeResponse.Headers["Accept-Ranges"])
    } catch {
        $statusCode = $null
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }
        Write-Host ("Range status       : FAIL ({0}) {1}" -f $statusCode, $_.Exception.Message) -ForegroundColor Yellow
    }
}

Write-Section "Next"
Write-Host "1. Confirm root URL, SPA routes, and 404 checks above."
Write-Host "2. Confirm journal_mode is wal."
Write-Host "3. If VideoPath was provided, confirm Range returns 206 and Content-Range."
Write-Host "4. Attach startup logs, error logs, and browser Network screenshots to the test record."
