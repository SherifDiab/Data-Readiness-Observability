#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Builds and deploys IBM Ops Hub (.NET + Angular) to IIS on Windows Server.

.PARAMETER AppPath
    Deployment root directory. Default: C:\inetpub\ibm-ops-hub

.PARAMETER ApiPort
    Port for the API backend. Default: 5000

.PARAMETER FrontendPort
    Port for the Angular frontend in IIS. Default: 80

.EXAMPLE
    .\deploy-app.ps1 -AppPath "D:\apps\ibm-ops-hub"
#>
param(
    [string]$AppPath      = "C:\inetpub\ibm-ops-hub",
    [int]   $ApiPort      = 5000,
    [int]   $FrontendPort = 80,
    [string]$SiteName     = "IbmOpsHub"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "=== IBM Ops Hub Deployment ===" -ForegroundColor Cyan
Write-Host "App path  : $AppPath"
Write-Host "API port  : $ApiPort"
Write-Host "Frontend  : port $FrontendPort"
Write-Host ""

# ---------------------------------------------------------------------------
# Pre-flight checks — fail fast with helpful messages
# ---------------------------------------------------------------------------
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# .NET SDK (required for dotnet publish)
$dotnetSdk = $false
try {
    $sdkList = & dotnet --list-sdks 2>$null
    if ($sdkList -match "^8\.") { $dotnetSdk = $true }
} catch {}

if (-not $dotnetSdk) {
    Write-Host ""
    Write-Host "ERROR: .NET 8 SDK not found." -ForegroundColor Red
    Write-Host ""
    Write-Host "  The .NET Hosting Bundle (runtime) is installed, but 'dotnet publish'" -ForegroundColor Yellow
    Write-Host "  also requires the .NET SDK (the build/compiler tools)." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Download the .NET 8 SDK here:" -ForegroundColor White
    Write-Host "  https://dotnet.microsoft.com/en-us/download/dotnet/8.0" -ForegroundColor Cyan
    Write-Host "  --> Under 'SDK' column --> Windows --> x64 Installer" -ForegroundColor White
    Write-Host ""
    Write-Host "  After installing the SDK, re-run this script." -ForegroundColor White
    Write-Host ""
    exit 1
}
Write-Host "  [OK] .NET 8 SDK found." -ForegroundColor Green

# Node.js (required for Angular build)
$nodeOk = $false
try {
    $nodeVer = & node --version 2>$null
    if ($nodeVer) { $nodeOk = $true }
} catch {}

if (-not $nodeOk) {
    Write-Host ""
    Write-Host "ERROR: Node.js not found." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Download Node.js 20 LTS here:" -ForegroundColor White
    Write-Host "  https://nodejs.org/en/download  --> Windows x64 (.msi)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  After installing, close and reopen PowerShell, then re-run this script." -ForegroundColor White
    Write-Host ""
    exit 1
}
Write-Host "  [OK] Node.js found ($nodeVer)." -ForegroundColor Green
Write-Host ""

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
$BackendSrc  = Join-Path $RepoRoot "backend\IbmOpsHub"
$FrontendSrc = Join-Path $RepoRoot "frontend"
$ApiDeploy   = Join-Path $AppPath  "api"
$WebDeploy   = Join-Path $AppPath  "www"

# ---------------------------------------------------------------------------
# 1. Create directories
# ---------------------------------------------------------------------------
Write-Host "[1/6] Creating deployment directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $ApiDeploy | Out-Null
New-Item -ItemType Directory -Force -Path $WebDeploy  | Out-Null
New-Item -ItemType Directory -Force -Path "$AppPath\logs" | Out-Null
Write-Host "  Done." -ForegroundColor Green

# ---------------------------------------------------------------------------
# 2. Build .NET backend
# ---------------------------------------------------------------------------
Write-Host "[2/6] Building .NET backend (dotnet publish)..." -ForegroundColor Yellow
Push-Location $BackendSrc
& dotnet publish -c Release -o $ApiDeploy --nologo
$exitCode = $LASTEXITCODE
Pop-Location

if ($exitCode -ne 0) {
    Write-Host ""
    Write-Host "ERROR: dotnet publish failed (exit code $exitCode)." -ForegroundColor Red
    Write-Host "Check the errors above. Common causes:" -ForegroundColor Yellow
    Write-Host "  - Missing NuGet packages (no internet or proxy blocking nuget.org)" -ForegroundColor White
    Write-Host "  - Wrong .NET SDK version (need 8.x)" -ForegroundColor White
    Write-Host ""
    exit 1
}
Write-Host "  Backend published to: $ApiDeploy" -ForegroundColor Green

# Copy the IIS web.config for the API right after publish
# (dotnet publish may overwrite it)
Copy-Item -Path "$PSScriptRoot\api-web.config" -Destination "$ApiDeploy\web.config" -Force

# ---------------------------------------------------------------------------
# 3. Build Angular frontend
# ---------------------------------------------------------------------------
Write-Host "[3/6] Building Angular frontend (ng build)..." -ForegroundColor Yellow
Push-Location $FrontendSrc

if (-not (Test-Path "node_modules")) {
    Write-Host "  Running npm install (first time, may take a few minutes)..."
    & npm install --prefer-offline 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "ERROR: npm install failed." -ForegroundColor Red
        Write-Host "  If you are behind a corporate proxy, configure npm:" -ForegroundColor Yellow
        Write-Host "  npm config set proxy http://your-proxy:port" -ForegroundColor White
        Write-Host "  npm config set https-proxy http://your-proxy:port" -ForegroundColor White
        Pop-Location
        exit 1
    }
}

& npm run build 2>&1
$ngExit = $LASTEXITCODE
Pop-Location

if ($ngExit -ne 0) {
    Write-Host "ERROR: Angular build failed (exit code $ngExit)." -ForegroundColor Red
    exit 1
}

# Angular 17 build output location
$angularDist = Join-Path $FrontendSrc "dist\ibm-ops-hub-angular\browser"
if (-not (Test-Path $angularDist)) {
    $angularDist = Join-Path $FrontendSrc "dist\ibm-ops-hub-angular"
}
if (-not (Test-Path $angularDist)) {
    Write-Host "ERROR: Angular dist folder not found at: $angularDist" -ForegroundColor Red
    exit 1
}

Copy-Item -Path "$angularDist\*" -Destination $WebDeploy -Recurse -Force
Write-Host "  Frontend built to: $WebDeploy" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 4. Deploy IIS web.config files
# ---------------------------------------------------------------------------
Write-Host "[4/6] Deploying IIS configuration..." -ForegroundColor Yellow
Copy-Item -Path "$PSScriptRoot\frontend-web.config" -Destination "$WebDeploy\web.config" -Force
Write-Host "  Done." -ForegroundColor Green

# ---------------------------------------------------------------------------
# 5. Create IIS app pools and sites
# ---------------------------------------------------------------------------
Write-Host "[5/6] Configuring IIS sites..." -ForegroundColor Yellow
Import-Module WebAdministration -ErrorAction Stop

# API app pool (no managed runtime = ASP.NET Core)
$apiPool = "${SiteName}Api"
if (-not (Test-Path "IIS:\AppPools\$apiPool")) {
    New-WebAppPool -Name $apiPool | Out-Null
}
Set-ItemProperty "IIS:\AppPools\$apiPool" managedRuntimeVersion ""
Set-ItemProperty "IIS:\AppPools\$apiPool" processModel.identityType ApplicationPoolIdentity

# Frontend app pool
$webPool = "${SiteName}Web"
if (-not (Test-Path "IIS:\AppPools\$webPool")) {
    New-WebAppPool -Name $webPool | Out-Null
}
Set-ItemProperty "IIS:\AppPools\$webPool" managedRuntimeVersion ""

# Remove old sites if they exist, then create fresh
$existingSites = @("${SiteName}Frontend", "${SiteName}Api")
foreach ($s in $existingSites) {
    if (Get-Website -Name $s -ErrorAction SilentlyContinue) {
        Remove-Website -Name $s
    }
}

New-Website -Name "${SiteName}Frontend" -Port $FrontendPort -PhysicalPath $WebDeploy  -ApplicationPool $webPool | Out-Null
New-Website -Name "${SiteName}Api"      -Port $ApiPort      -PhysicalPath $ApiDeploy  -ApplicationPool $apiPool | Out-Null

Write-Host "  IIS sites created." -ForegroundColor Green

# ---------------------------------------------------------------------------
# 6. Start everything
# ---------------------------------------------------------------------------
Write-Host "[6/6] Starting IIS sites..." -ForegroundColor Yellow
Start-WebAppPool -Name $apiPool -ErrorAction SilentlyContinue
Start-WebAppPool -Name $webPool -ErrorAction SilentlyContinue
Start-Website    -Name "${SiteName}Frontend" -ErrorAction SilentlyContinue
Start-Website    -Name "${SiteName}Api"      -ErrorAction SilentlyContinue
Write-Host "  Done." -ForegroundColor Green

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "=== Deployment complete! ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Dashboard : http://localhost:$FrontendPort" -ForegroundColor White
Write-Host "  API       : http://localhost:$ApiPort"      -ForegroundColor White
Write-Host "  Swagger   : http://localhost:$ApiPort/swagger" -ForegroundColor White
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "  1. Edit the config file with your IBM credentials:" -ForegroundColor White
Write-Host "     $ApiDeploy\appsettings.json" -ForegroundColor Cyan
Write-Host "  2. Run: iisreset" -ForegroundColor White
Write-Host "  3. Open http://localhost:$FrontendPort in your browser" -ForegroundColor White
Write-Host ""
Write-Host "  TIP: You can also configure credentials from the Settings page in the UI." -ForegroundColor Gray
Write-Host ""
