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
    [string]$AppPath    = "C:\inetpub\ibm-ops-hub",
    [int]   $ApiPort    = 5000,
    [int]   $FrontendPort = 80,
    [string]$SiteName   = "IbmOpsHub"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "=== IBM Ops Hub Deployment ===" -ForegroundColor Cyan
Write-Host "App path  : $AppPath"
Write-Host "API port  : $ApiPort"
Write-Host "Frontend  : port $FrontendPort"
Write-Host ""

# ─── Paths ────────────────────────────────────────────────────────────────────
$BackendSrc  = Join-Path $RepoRoot "backend\IbmOpsHub"
$FrontendSrc = Join-Path $RepoRoot "frontend"
$ApiDeploy   = Join-Path $AppPath  "api"
$WebDeploy   = Join-Path $AppPath  "www"

# ─── 1. Create directories ────────────────────────────────────────────────────
Write-Host "[1/6] Creating deployment directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $ApiDeploy | Out-Null
New-Item -ItemType Directory -Force -Path $WebDeploy | Out-Null
New-Item -ItemType Directory -Force -Path "$AppPath\logs" | Out-Null

# ─── 2. Build backend ─────────────────────────────────────────────────────────
Write-Host "[2/6] Building .NET backend..." -ForegroundColor Yellow
Push-Location $BackendSrc
dotnet publish -c Release -o $ApiDeploy --nologo
if ($LASTEXITCODE -ne 0) { throw "dotnet publish failed" }
Pop-Location
Write-Host "  Backend built to $ApiDeploy" -ForegroundColor Green

# ─── 3. Build Angular frontend ────────────────────────────────────────────────
Write-Host "[3/6] Building Angular frontend..." -ForegroundColor Yellow
Push-Location $FrontendSrc
if (-not (Test-Path "node_modules")) {
    Write-Host "  Installing npm packages..."
    npm ci --silent
}
npm run build -- --base-href /
if ($LASTEXITCODE -ne 0) { throw "Angular build failed" }
# Angular 17 outputs to dist/ibm-ops-hub-angular/browser
$angularDist = Join-Path $FrontendSrc "dist\ibm-ops-hub-angular\browser"
if (-not (Test-Path $angularDist)) {
    $angularDist = Join-Path $FrontendSrc "dist\ibm-ops-hub-angular"
}
Copy-Item -Path "$angularDist\*" -Destination $WebDeploy -Recurse -Force
Pop-Location
Write-Host "  Frontend built to $WebDeploy" -ForegroundColor Green

# ─── 4. Copy IIS web.config files ────────────────────────────────────────────
Write-Host "[4/6] Deploying IIS configuration..." -ForegroundColor Yellow
Copy-Item -Path "$PSScriptRoot\frontend-web.config" -Destination "$WebDeploy\web.config" -Force
Copy-Item -Path "$PSScriptRoot\api-web.config"      -Destination "$ApiDeploy\web.config" -Force

# ─── 5. Create IIS sites ──────────────────────────────────────────────────────
Write-Host "[5/6] Configuring IIS sites..." -ForegroundColor Yellow
Import-Module WebAdministration -ErrorAction SilentlyContinue

# API app pool
$apiPool = "${SiteName}Api"
if (-not (Test-Path "IIS:\AppPools\$apiPool")) {
    New-WebAppPool -Name $apiPool
    Set-ItemProperty "IIS:\AppPools\$apiPool" managedRuntimeVersion ""
    Set-ItemProperty "IIS:\AppPools\$apiPool" processModel.identityType ApplicationPoolIdentity
}

# Frontend app pool
$webPool = "${SiteName}Web"
if (-not (Test-Path "IIS:\AppPools\$webPool")) {
    New-WebAppPool -Name $webPool
    Set-ItemProperty "IIS:\AppPools\$webPool" managedRuntimeVersion ""
}

# Frontend site (port $FrontendPort)
if (Get-Website -Name "${SiteName}Frontend" -ErrorAction SilentlyContinue) {
    Remove-Website -Name "${SiteName}Frontend"
}
New-Website -Name "${SiteName}Frontend" -Port $FrontendPort -PhysicalPath $WebDeploy -ApplicationPool $webPool | Out-Null

# API site (port $ApiPort) — runs as a .NET process via AspNetCoreModule
if (Get-Website -Name "${SiteName}Api" -ErrorAction SilentlyContinue) {
    Remove-Website -Name "${SiteName}Api"
}
New-Website -Name "${SiteName}Api" -Port $ApiPort -PhysicalPath $ApiDeploy -ApplicationPool $apiPool | Out-Null

# ─── 6. Start sites ───────────────────────────────────────────────────────────
Write-Host "[6/6] Starting IIS sites..." -ForegroundColor Yellow
Start-WebAppPool -Name $apiPool  -ErrorAction SilentlyContinue
Start-WebAppPool -Name $webPool  -ErrorAction SilentlyContinue
Start-Website -Name "${SiteName}Frontend" -ErrorAction SilentlyContinue
Start-Website -Name "${SiteName}Api"      -ErrorAction SilentlyContinue

# ─── Done ─────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=== Deployment complete! ===" -ForegroundColor Cyan
Write-Host "Frontend  : http://localhost:$FrontendPort" -ForegroundColor White
Write-Host "API       : http://localhost:$ApiPort" -ForegroundColor White
Write-Host "API Docs  : http://localhost:$ApiPort/swagger" -ForegroundColor White
Write-Host ""
Write-Host "NEXT: Edit $ApiDeploy\appsettings.json with your IBM credentials." -ForegroundColor Yellow
Write-Host "Then run: iisreset  (to restart IIS with the new settings)" -ForegroundColor Yellow
