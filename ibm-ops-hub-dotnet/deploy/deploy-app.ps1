#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Deploys IBM Ops Hub (.NET + Angular) to IIS on Windows Server.

.DESCRIPTION
    TWO MODES:

    MODE 1 - Build + Deploy (requires internet / NuGet access on this server):
        .\deploy-app.ps1

    MODE 2 - Deploy pre-built artifacts (no internet needed on server):
        .\deploy-app.ps1 -UseArtifacts -ArtifactsPath "C:\path\to\artifacts"

        Build the artifacts first on a machine WITH internet access:
        Run:  .\build-local.ps1   (produces an "artifacts" folder)
        Copy the artifacts folder to the server, then use MODE 2.

.PARAMETER AppPath
    Deployment root directory. Default: C:\inetpub\ibm-ops-hub

.PARAMETER ApiPort
    Port for the API backend. Default: 5000

.PARAMETER FrontendPort
    Port for the Angular frontend in IIS. Default: 80

.PARAMETER SiteName
    IIS site name prefix. Default: IbmOpsHub

.PARAMETER UseArtifacts
    Switch: skip build steps and deploy from pre-built artifacts.

.PARAMETER ArtifactsPath
    Path to the artifacts folder produced by build-local.ps1.
    Only used when -UseArtifacts is specified.
    Default: ".\artifacts" (relative to where you run the script from)

.EXAMPLE
    # Standard (builds on server - needs nuget.org access):
    .\deploy-app.ps1

    # Pre-built (no internet needed on server):
    .\deploy-app.ps1 -UseArtifacts -ArtifactsPath "C:\ibm-deploy\artifacts"
#>
param(
    [string]$AppPath       = "C:\inetpub\ibm-ops-hub",
    [int]   $ApiPort       = 5000,
    [int]   $FrontendPort  = 80,
    [string]$SiteName      = "IbmOpsHub",
    [switch]$UseArtifacts,
    [string]$ArtifactsPath = ".\artifacts"
)

$ErrorActionPreference = "Stop"
$RepoRoot  = Split-Path -Parent $PSScriptRoot
$DeployDir = $PSScriptRoot

Write-Host ""
Write-Host "=== IBM Ops Hub Deployment ===" -ForegroundColor Cyan
Write-Host "App path  : $AppPath"
Write-Host "API port  : $ApiPort"
Write-Host "Frontend  : port $FrontendPort"
if ($UseArtifacts) {
    Write-Host "Mode      : Deploy pre-built artifacts" -ForegroundColor Yellow
    Write-Host "Artifacts : $ArtifactsPath"
} else {
    Write-Host "Mode      : Build + Deploy (requires NuGet/npm access)" -ForegroundColor Yellow
}
Write-Host ""

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------
$ApiDeploy  = Join-Path $AppPath "api"
$WebDeploy  = Join-Path $AppPath "www"
$LogsDir    = Join-Path $AppPath "logs"

# ---------------------------------------------------------------------------
# If using pre-built artifacts, validate the artifacts folder
# ---------------------------------------------------------------------------
if ($UseArtifacts) {
    $ArtifactsPath = Resolve-Path $ArtifactsPath -ErrorAction SilentlyContinue
    if (-not $ArtifactsPath) {
        Write-Host ""
        Write-Host "ERROR: Artifacts folder not found." -ForegroundColor Red
        Write-Host ""
        Write-Host "  Run build-local.ps1 on a machine with internet to produce the" -ForegroundColor Yellow
        Write-Host "  artifacts folder, then copy it here and run:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "    .\deploy-app.ps1 -UseArtifacts -ArtifactsPath C:\path\to\artifacts" -ForegroundColor White
        Write-Host ""
        exit 1
    }

    $ArtifactsApi  = Join-Path $ArtifactsPath "api"
    $ArtifactsWww  = Join-Path $ArtifactsPath "www"
    $ArtifactsDep  = Join-Path $ArtifactsPath "deploy"

    if (-not (Test-Path $ArtifactsApi)) {
        Write-Host "ERROR: artifacts\api folder not found in: $ArtifactsPath" -ForegroundColor Red
        exit 1
    }
    if (-not (Test-Path $ArtifactsWww)) {
        Write-Host "ERROR: artifacts\www folder not found in: $ArtifactsPath" -ForegroundColor Red
        exit 1
    }

    Write-Host "[1/4] Validating artifacts..." -ForegroundColor Yellow
    $apiExe = Get-ChildItem -Path $ArtifactsApi -Filter "*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    $apiDll = Get-ChildItem -Path $ArtifactsApi -Filter "IbmOpsHub.dll" -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $apiExe -and -not $apiDll) {
        Write-Host "  WARNING: No IbmOpsHub.dll or .exe found in artifacts\api." -ForegroundColor Yellow
        Write-Host "  The build may be incomplete. Continuing anyway..." -ForegroundColor Gray
    } else {
        Write-Host "  [OK] API artifacts found." -ForegroundColor Green
    }
    $indexHtml = Join-Path $ArtifactsWww "index.html"
    if (-not (Test-Path $indexHtml)) {
        Write-Host "  WARNING: index.html not found in artifacts\www." -ForegroundColor Yellow
    } else {
        Write-Host "  [OK] Frontend artifacts found." -ForegroundColor Green
    }

    # ---------------------------------------------------------------------------
    # Deploy from artifacts
    # ---------------------------------------------------------------------------
    Write-Host "[2/4] Creating deployment directories..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $ApiDeploy | Out-Null
    New-Item -ItemType Directory -Force -Path $WebDeploy  | Out-Null
    New-Item -ItemType Directory -Force -Path $LogsDir    | Out-Null
    Write-Host "  Done." -ForegroundColor Green

    Write-Host "[3/4] Copying artifacts to deployment directories..." -ForegroundColor Yellow
    Copy-Item -Path "$ArtifactsApi\*" -Destination $ApiDeploy -Recurse -Force
    Copy-Item -Path "$ArtifactsWww\*" -Destination $WebDeploy  -Recurse -Force

    # Copy IIS web.configs (prefer artifacts/deploy, fall back to current deploy dir)
    if (Test-Path "$ArtifactsDep\api-web.config") {
        Copy-Item "$ArtifactsDep\api-web.config"      "$ApiDeploy\web.config" -Force
        Copy-Item "$ArtifactsDep\frontend-web.config" "$WebDeploy\web.config" -Force
    } else {
        Copy-Item "$DeployDir\api-web.config"      "$ApiDeploy\web.config" -Force
        Copy-Item "$DeployDir\frontend-web.config" "$WebDeploy\web.config" -Force
    }
    Write-Host "  [OK] Files copied." -ForegroundColor Green

} else {

    # ---------------------------------------------------------------------------
    # Build on server (requires internet access to nuget.org and registry.npmjs.org)
    # ---------------------------------------------------------------------------

    # Pre-flight checks
    Write-Host "Checking build prerequisites..." -ForegroundColor Yellow

    # .NET 8 SDK
    $sdkOk = $false
    try {
        $sdkList = & dotnet --list-sdks 2>$null
        if ($sdkList -match "^8\.") { $sdkOk = $true }
    } catch {}

    if (-not $sdkOk) {
        Write-Host ""
        Write-Host "ERROR: .NET 8 SDK not found." -ForegroundColor Red
        Write-Host ""
        Write-Host "  The .NET Hosting Bundle (runtime) is installed, but building also" -ForegroundColor Yellow
        Write-Host "  requires the .NET SDK (compiler). These are two separate downloads." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Download the .NET 8 SDK:" -ForegroundColor White
        Write-Host "    https://dotnet.microsoft.com/en-us/download/dotnet/8.0" -ForegroundColor Cyan
        Write-Host "    --> Under 'SDK' column --> Windows --> x64 Installer" -ForegroundColor White
        Write-Host ""
        Write-Host "  ALTERNATIVE: If NuGet is blocked by your corporate firewall," -ForegroundColor Yellow
        Write-Host "  build on a dev machine instead:" -ForegroundColor Yellow
        Write-Host "    1. On dev machine: .\deploy\build-local.ps1" -ForegroundColor White
        Write-Host "    2. Copy artifacts\ folder to server" -ForegroundColor White
        Write-Host "    3. On server: .\deploy\deploy-app.ps1 -UseArtifacts" -ForegroundColor White
        Write-Host ""
        exit 1
    }
    Write-Host "  [OK] .NET 8 SDK found." -ForegroundColor Green

    # Node.js
    $nodeOk = $false
    try {
        $nv = & node --version 2>$null
        if ($nv) { $nodeOk = $true }
    } catch {}

    if (-not $nodeOk) {
        Write-Host ""
        Write-Host "ERROR: Node.js not found." -ForegroundColor Red
        Write-Host ""
        Write-Host "  Download Node.js 20 LTS:" -ForegroundColor White
        Write-Host "    https://nodejs.org/en/download  --> Windows x64 (.msi)" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  After installing, close and reopen PowerShell, then re-run." -ForegroundColor White
        Write-Host ""
        exit 1
    }
    Write-Host "  [OK] Node.js found ($nv)." -ForegroundColor Green
    Write-Host ""

    # Step 1: Directories
    Write-Host "[1/5] Creating deployment directories..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $ApiDeploy | Out-Null
    New-Item -ItemType Directory -Force -Path $WebDeploy  | Out-Null
    New-Item -ItemType Directory -Force -Path $LogsDir    | Out-Null
    Write-Host "  Done." -ForegroundColor Green

    # Step 2: Build .NET backend
    Write-Host "[2/5] Building .NET backend (dotnet publish)..." -ForegroundColor Yellow

    $BackendSrc = Join-Path $RepoRoot "backend\IbmOpsHub"
    Push-Location $BackendSrc
    & dotnet publish -c Release -o $ApiDeploy --nologo
    $exitCode = $LASTEXITCODE
    Pop-Location

    if ($exitCode -ne 0) {
        Write-Host ""
        Write-Host "ERROR: dotnet publish failed (exit code $exitCode)." -ForegroundColor Red
        Write-Host ""
        Write-Host "  If you see NU1100 'Unable to resolve package' errors, nuget.org" -ForegroundColor Yellow
        Write-Host "  is probably blocked by your corporate firewall." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Solutions:" -ForegroundColor White
        Write-Host ""
        Write-Host "  A) Set HTTP proxy before running:" -ForegroundColor White
        Write-Host "       `$env:HTTPS_PROXY = 'http://your-proxy:port'" -ForegroundColor Cyan
        Write-Host "       .\deploy\deploy-app.ps1" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  B) Configure internal NuGet feed:" -ForegroundColor White
        Write-Host "       Edit backend\IbmOpsHub\NuGet.Config" -ForegroundColor Cyan
        Write-Host "       Uncomment Option A and set your corporate NuGet URL" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  C) Build on a dev machine with internet (RECOMMENDED):" -ForegroundColor White
        Write-Host "       1. On dev machine: .\deploy\build-local.ps1" -ForegroundColor Cyan
        Write-Host "       2. Copy artifacts\ to server" -ForegroundColor Cyan
        Write-Host "       3. On server: .\deploy\deploy-app.ps1 -UseArtifacts" -ForegroundColor Cyan
        Write-Host ""
        exit 1
    }
    Write-Host "  Backend published to: $ApiDeploy" -ForegroundColor Green

    Copy-Item -Path "$DeployDir\api-web.config" -Destination "$ApiDeploy\web.config" -Force

    # Step 3: Build Angular frontend
    Write-Host "[3/5] Building Angular frontend (ng build)..." -ForegroundColor Yellow
    $FrontendSrc = Join-Path $RepoRoot "frontend"
    Push-Location $FrontendSrc

    if (-not (Test-Path "node_modules")) {
        Write-Host "  Running npm install (first time, may take a few minutes)..."
        & npm install --prefer-offline 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host ""
            Write-Host "ERROR: npm install failed." -ForegroundColor Red
            Write-Host "  If behind a corporate proxy:" -ForegroundColor Yellow
            Write-Host "    npm config set proxy http://your-proxy:port" -ForegroundColor White
            Write-Host "    npm config set https-proxy http://your-proxy:port" -ForegroundColor White
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

    # Angular 17+ build output
    $angularDist = Join-Path $FrontendSrc "dist\ibm-ops-hub-angular\browser"
    if (-not (Test-Path $angularDist)) {
        $angularDist = Join-Path $FrontendSrc "dist\ibm-ops-hub-angular"
    }
    if (-not (Test-Path $angularDist)) {
        Write-Host "ERROR: Angular dist folder not found at: $angularDist" -ForegroundColor Red
        exit 1
    }

    Copy-Item -Path "$angularDist\*" -Destination $WebDeploy -Recurse -Force
    Copy-Item -Path "$DeployDir\frontend-web.config" -Destination "$WebDeploy\web.config" -Force
    Write-Host "  Frontend built to: $WebDeploy" -ForegroundColor Green

    Write-Host "[4/5] IIS config..." -ForegroundColor Yellow
    Write-Host "  (Included above with web.config copies.)" -ForegroundColor Gray
}

# ---------------------------------------------------------------------------
# IIS setup (common to both modes)
# ---------------------------------------------------------------------------
$iisStep = if ($UseArtifacts) { "4" } else { "5" }
Write-Host "[$iisStep/$(if($UseArtifacts){'4'}else{'5'})] Configuring IIS sites..." -ForegroundColor Yellow
Import-Module WebAdministration -ErrorAction Stop

# API app pool (no managed runtime = ASP.NET Core in-process)
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
foreach ($s in @("${SiteName}Frontend", "${SiteName}Api")) {
    if (Get-Website -Name $s -ErrorAction SilentlyContinue) {
        Remove-Website -Name $s
    }
}

New-Website -Name "${SiteName}Frontend" -Port $FrontendPort -PhysicalPath $WebDeploy -ApplicationPool $webPool | Out-Null
New-Website -Name "${SiteName}Api"      -Port $ApiPort      -PhysicalPath $ApiDeploy -ApplicationPool $apiPool | Out-Null

Write-Host "  IIS sites created." -ForegroundColor Green

# Start everything
Start-WebAppPool -Name $apiPool -ErrorAction SilentlyContinue
Start-WebAppPool -Name $webPool -ErrorAction SilentlyContinue
Start-Website    -Name "${SiteName}Frontend" -ErrorAction SilentlyContinue
Start-Website    -Name "${SiteName}Api"      -ErrorAction SilentlyContinue

# Enable ARR proxy so the frontend web.config can reverse-proxy /api/* and
# /hubs/* to the .NET backend.  Without this, URL Rewrite rewrites with an
# absolute HTTP URL (http://localhost:5000/...) fail with IIS error 0x8007007b
# (ERROR_INVALID_NAME / 404.4) because there is no HTTP proxy engine.
Write-Host "  Enabling ARR proxy..." -ForegroundColor Gray
try {
    Set-WebConfigurationProperty `
        -PSPath "MACHINE/WEBROOT/APPHOST" `
        -Filter "system.webServer/proxy" `
        -Name "enabled" `
        -Value $true
    Write-Host "  [OK] ARR proxy enabled." -ForegroundColor Green
} catch {
    Write-Host "  [WARN] Could not enable ARR proxy automatically: $_" -ForegroundColor Yellow
    Write-Host "  Enable it manually: IIS Manager -> Application Request Routing Cache -> Server Proxy Settings -> Enable proxy" -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "=== Deployment complete! ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Dashboard : http://localhost:$FrontendPort"  -ForegroundColor White
Write-Host "  API       : http://localhost:$ApiPort"       -ForegroundColor White
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
