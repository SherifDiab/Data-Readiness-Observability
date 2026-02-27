#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Installs all prerequisites for IBM Ops Hub on Windows Server.
    Run this script ONCE on a fresh Windows Server installation.

.NOTES
    Run as Administrator in PowerShell 5.1+ or PowerShell 7+
    Usage: .\install-prerequisites.ps1
#>

$ErrorActionPreference = "Stop"
Write-Host "=== IBM Ops Hub — Prerequisites Installer ===" -ForegroundColor Cyan

# ─── 1. Enable IIS and required features ─────────────────────────────────────
Write-Host "`n[1/6] Enabling IIS and Windows features..." -ForegroundColor Yellow
$features = @(
    "Web-Server",
    "Web-WebServer",
    "Web-Common-Http",
    "Web-Default-Doc",
    "Web-Static-Content",
    "Web-Http-Errors",
    "Web-Http-Redirect",
    "Web-App-Dev",
    "Web-Net-Ext45",
    "Web-Asp-Net45",
    "Web-ISAPI-Ext",
    "Web-ISAPI-Filter",
    "Web-Health",
    "Web-Http-Logging",
    "Web-Mgmt-Tools",
    "Web-Mgmt-Console",
    "Web-Scripting-Tools"
)
foreach ($f in $features) {
    Install-WindowsFeature -Name $f -IncludeManagementTools -ErrorAction SilentlyContinue | Out-Null
}
Write-Host "  IIS features enabled." -ForegroundColor Green

# ─── 2. Install .NET 8 Hosting Bundle ────────────────────────────────────────
Write-Host "`n[2/6] Installing .NET 8 Hosting Bundle..." -ForegroundColor Yellow
$dotnetBundle = "https://builds.dotnet.microsoft.com/dotnet/aspnetcore/Runtime/8.0.0/dotnet-hosting-8.0.0-win.exe"
$dotnetInstaller = "$env:TEMP\dotnet-hosting-8.exe"

if (-not (Get-Command dotnet -ErrorAction SilentlyContinue) -or
    -not [System.Version]"8.0.0".IsCompatibleWith((& dotnet --version 2>$null))) {
    Invoke-WebRequest -Uri $dotnetBundle -OutFile $dotnetInstaller -UseBasicParsing
    Start-Process -FilePath $dotnetInstaller -ArgumentList "/quiet /norestart" -Wait
    Write-Host "  .NET 8 Hosting Bundle installed." -ForegroundColor Green
} else {
    Write-Host "  .NET 8 already installed, skipping." -ForegroundColor Gray
}

# ─── 3. Install Node.js (for Angular build) ───────────────────────────────────
Write-Host "`n[3/6] Installing Node.js 20 LTS..." -ForegroundColor Yellow
$nodeMsi = "https://nodejs.org/dist/v20.12.0/node-v20.12.0-x64.msi"
$nodeInstaller = "$env:TEMP\node-setup.msi"

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Invoke-WebRequest -Uri $nodeMsi -OutFile $nodeInstaller -UseBasicParsing
    Start-Process msiexec.exe -ArgumentList "/i `"$nodeInstaller`" /quiet /norestart" -Wait
    # Refresh PATH
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
    Write-Host "  Node.js installed." -ForegroundColor Green
} else {
    $nv = (& node --version 2>$null)
    Write-Host "  Node.js already installed: $nv, skipping." -ForegroundColor Gray
}

# ─── 4. Install PostgreSQL ────────────────────────────────────────────────────
Write-Host "`n[4/6] Installing PostgreSQL 16..." -ForegroundColor Yellow
$pgInstaller = "$env:TEMP\postgresql-16-setup.exe"
$pgPassword  = "postgres"  # Change before production!
$pgPort      = "5432"
$pgDir       = "C:\Program Files\PostgreSQL\16"

if (-not (Test-Path "$pgDir\bin\psql.exe")) {
    $pgUrl = "https://sbp.enterprisedb.com/getfile.jsp?fileid=1259128"  # PostgreSQL 16 Windows installer
    Write-Host "  Downloading PostgreSQL installer (this may take a few minutes)..."
    Invoke-WebRequest -Uri $pgUrl -OutFile $pgInstaller -UseBasicParsing
    Start-Process -FilePath $pgInstaller -Wait -ArgumentList @(
        "--mode", "unattended",
        "--superpassword", $pgPassword,
        "--servicename", "postgresql-x64-16",
        "--serverport", $pgPort
    )
    Write-Host "  PostgreSQL installed. Password: $pgPassword (CHANGE IN PRODUCTION)" -ForegroundColor Green
} else {
    Write-Host "  PostgreSQL already installed, skipping." -ForegroundColor Gray
}

# Create the opshub database
$pgBin = "$pgDir\bin"
$env:PGPASSWORD = $pgPassword
& "$pgBin\psql.exe" -U postgres -c "CREATE DATABASE opshub;" 2>$null
Write-Host "  Database 'opshub' created (or already exists)." -ForegroundColor Green

# ─── 5. Install Redis (Memurai — free Redis for Windows) ─────────────────────
Write-Host "`n[5/6] Installing Memurai (Redis for Windows)..." -ForegroundColor Yellow
$memuraiMsi = "$env:TEMP\memurai-setup.msi"
# Memurai Developer (free) — for production use Memurai or WSL Redis
$memuraiUrl = "https://www.memurai.com/downloads/memurai-developer.msi"

if (-not (Get-Service "Memurai" -ErrorAction SilentlyContinue)) {
    try {
        Invoke-WebRequest -Uri $memuraiUrl -OutFile $memuraiMsi -UseBasicParsing -TimeoutSec 60
        Start-Process msiexec.exe -ArgumentList "/i `"$memuraiMsi`" /quiet /norestart" -Wait
        Start-Service "Memurai" -ErrorAction SilentlyContinue
        Write-Host "  Memurai (Redis) installed and started." -ForegroundColor Green
    } catch {
        Write-Host "  WARNING: Could not auto-install Memurai. Download manually from https://www.memurai.com" -ForegroundColor Yellow
        Write-Host "  Alternatively, install WSL2 and run Redis in WSL." -ForegroundColor Yellow
    }
} else {
    Write-Host "  Memurai already installed, skipping." -ForegroundColor Gray
}

# ─── 6. Install URL Rewrite Module for IIS ───────────────────────────────────
Write-Host "`n[6/6] Installing IIS URL Rewrite Module..." -ForegroundColor Yellow
$rewriteUrl = "https://download.microsoft.com/download/1/2/8/128E2E22-C1B9-44A4-BE2A-5859ED1D4592/rewrite_amd64_en-US.msi"
$rewriteMsi = "$env:TEMP\rewrite_amd64.msi"

if (-not (Test-Path "HKLM:\SOFTWARE\Microsoft\IIS Extensions\URL Rewrite")) {
    Invoke-WebRequest -Uri $rewriteUrl -OutFile $rewriteMsi -UseBasicParsing
    Start-Process msiexec.exe -ArgumentList "/i `"$rewriteMsi`" /quiet /norestart" -Wait
    Write-Host "  URL Rewrite Module installed." -ForegroundColor Green
} else {
    Write-Host "  URL Rewrite already installed, skipping." -ForegroundColor Gray
}

Write-Host "`n=== Prerequisites installation complete! ===" -ForegroundColor Cyan
Write-Host "Next step: run .\deploy-app.ps1 to deploy IBM Ops Hub." -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT: Change the PostgreSQL password in appsettings.json before production use!" -ForegroundColor Red
