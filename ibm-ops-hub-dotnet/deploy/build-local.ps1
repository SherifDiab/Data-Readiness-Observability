<#
.SYNOPSIS
    Builds IBM Ops Hub on a developer machine (with internet access) and
    produces a ready-to-deploy "artifacts" folder you can copy to the server.

.DESCRIPTION
    Run this script on a Windows PC or Mac/Linux machine that CAN reach
    nuget.org and registry.npmjs.org.

    It will:
      1. Build the .NET backend  (dotnet publish)
      2. Build the Angular frontend (npm install + ng build)
      3. Copy everything into .\artifacts\

    Then copy the entire "artifacts" folder to the Windows Server and run:
      .\deploy-app.ps1 -UseArtifacts

.PARAMETER OutDir
    Folder to write artifacts to. Default: .\artifacts

.EXAMPLE
    # Build on your dev PC:
    .\deploy\build-local.ps1

    # Copy artifacts to server (PowerShell / robocopy):
    robocopy .\artifacts \\server\c$\ibm-ops-hub-deploy /E

    # On the server:
    cd C:\ibm-ops-hub-deploy
    .\deploy-app.ps1 -UseArtifacts

#>
param(
    [string]$OutDir = ".\artifacts"
)

$ErrorActionPreference = "Stop"
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot   = Split-Path -Parent $ScriptDir

$ApiOut  = Join-Path $OutDir "api"
$WebOut  = Join-Path $OutDir "www"
$CfgOut  = Join-Path $OutDir "deploy"

Write-Host ""
Write-Host "=== IBM Ops Hub - Local Build ===" -ForegroundColor Cyan
Write-Host "Output directory: $OutDir"
Write-Host ""

# ---------------------------------------------------------------------------
# Pre-flight
# ---------------------------------------------------------------------------
Write-Host "Checking tools..." -ForegroundColor Yellow

# .NET 8 SDK
$sdkOk = $false
try {
    $sdkList = & dotnet --list-sdks 2>$null
    if ($sdkList -match "^8\.") { $sdkOk = $true }
} catch {}
if (-not $sdkOk) {
    Write-Host "ERROR: .NET 8 SDK not found." -ForegroundColor Red
    Write-Host "  Download: https://dotnet.microsoft.com/en-us/download/dotnet/8.0" -ForegroundColor Cyan
    exit 1
}
Write-Host "  [OK] .NET 8 SDK" -ForegroundColor Green

# Node.js
$nodeOk = $false
try {
    $nv = & node --version 2>$null
    if ($nv) { $nodeOk = $true }
} catch {}
if (-not $nodeOk) {
    Write-Host "ERROR: Node.js not found." -ForegroundColor Red
    Write-Host "  Download: https://nodejs.org/en/download" -ForegroundColor Cyan
    exit 1
}
Write-Host "  [OK] Node.js ($nv)" -ForegroundColor Green
Write-Host ""

# ---------------------------------------------------------------------------
# 1. Create output folders
# ---------------------------------------------------------------------------
Write-Host "[1/4] Creating output folders..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $ApiOut | Out-Null
New-Item -ItemType Directory -Force -Path $WebOut  | Out-Null
New-Item -ItemType Directory -Force -Path $CfgOut  | Out-Null
Write-Host "  Done." -ForegroundColor Green

# ---------------------------------------------------------------------------
# 2. Build .NET backend
# ---------------------------------------------------------------------------
Write-Host "[2/4] Building .NET backend (dotnet publish)..." -ForegroundColor Yellow

$BackendSrc = Join-Path $RepoRoot "backend\IbmOpsHub"
Push-Location $BackendSrc
& dotnet publish -c Release -o $ApiOut --nologo
$exitCode = $LASTEXITCODE
Pop-Location

if ($exitCode -ne 0) {
    Write-Host ""
    Write-Host "ERROR: dotnet publish failed (exit code $exitCode)." -ForegroundColor Red
    Write-Host ""
    Write-Host "  If NuGet packages cannot be restored, your machine may also be behind" -ForegroundColor Yellow
    Write-Host "  a firewall. Try setting the HTTPS_PROXY environment variable first:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "    `$env:HTTPS_PROXY = 'http://your-proxy:port'" -ForegroundColor White
    Write-Host "    .\deploy\build-local.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "  Or configure a corporate NuGet feed in:" -ForegroundColor Yellow
    Write-Host "    backend\IbmOpsHub\NuGet.Config" -ForegroundColor White
    exit 1
}

Write-Host "  Backend built to: $ApiOut" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 3. Build Angular frontend
# ---------------------------------------------------------------------------
Write-Host "[3/4] Building Angular frontend..." -ForegroundColor Yellow

$FrontendSrc = Join-Path $RepoRoot "frontend"
Push-Location $FrontendSrc

Write-Host "  Running npm install..."
& npm install 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: npm install failed." -ForegroundColor Red
    Write-Host "  If behind a proxy:" -ForegroundColor Yellow
    Write-Host "    npm config set proxy http://your-proxy:port" -ForegroundColor White
    Write-Host "    npm config set https-proxy http://your-proxy:port" -ForegroundColor White
    Pop-Location
    exit 1
}

Write-Host "  Running ng build..."
& npm run build 2>&1
$ngExit = $LASTEXITCODE
Pop-Location

if ($ngExit -ne 0) {
    Write-Host "ERROR: Angular build failed (exit code $ngExit)." -ForegroundColor Red
    exit 1
}

# Find Angular dist output
$angularDist = Join-Path $FrontendSrc "dist\ibm-ops-hub-angular\browser"
if (-not (Test-Path $angularDist)) {
    $angularDist = Join-Path $FrontendSrc "dist\ibm-ops-hub-angular"
}
if (-not (Test-Path $angularDist)) {
    Write-Host "ERROR: Angular dist folder not found at: $angularDist" -ForegroundColor Red
    exit 1
}

Copy-Item -Path "$angularDist\*" -Destination $WebOut -Recurse -Force
Write-Host "  Frontend built to: $WebOut" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 4. Copy IIS config and deploy script
# ---------------------------------------------------------------------------
Write-Host "[4/4] Copying deployment files..." -ForegroundColor Yellow
Copy-Item -Path "$ScriptDir\frontend-web.config" -Destination "$CfgOut\frontend-web.config" -Force
Copy-Item -Path "$ScriptDir\api-web.config"      -Destination "$CfgOut\api-web.config"      -Force
Copy-Item -Path "$ScriptDir\deploy-app.ps1"      -Destination "$CfgOut\deploy-app.ps1"      -Force
Write-Host "  Done." -ForegroundColor Green

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Build complete!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Artifacts folder: $((Resolve-Path $OutDir).Path)" -ForegroundColor White
Write-Host ""
Write-Host "  NEXT STEPS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Copy the entire 'artifacts' folder to the Windows Server." -ForegroundColor White
Write-Host "     Example (from your dev machine):" -ForegroundColor Gray
Write-Host "       robocopy .\artifacts \\YourServer\c$\ibm-deploy /E" -ForegroundColor White
Write-Host "     Or zip it: Compress-Archive .\artifacts artifacts.zip" -ForegroundColor White
Write-Host ""
Write-Host "  2. On the Windows Server (as Administrator in PowerShell):" -ForegroundColor White
Write-Host "       cd C:\ibm-deploy" -ForegroundColor White
Write-Host "       .\deploy\deploy-app.ps1 -UseArtifacts" -ForegroundColor Cyan
Write-Host ""
Write-Host "  NOTE: The server still needs IIS + .NET Hosting Bundle + URL Rewrite." -ForegroundColor Yellow
Write-Host "  Run install-prerequisites.ps1 on the server first." -ForegroundColor Yellow
Write-Host ""
