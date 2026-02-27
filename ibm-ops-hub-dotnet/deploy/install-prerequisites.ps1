#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Installs all prerequisites for IBM Ops Hub on Windows Server.
    Run this script ONCE on a fresh Windows Server installation.

.NOTES
    Run as Administrator in PowerShell 5.1+
    Usage: .\install-prerequisites.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== IBM Ops Hub - Prerequisites Installer ===" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# Helper: download a file with progress
# ---------------------------------------------------------------------------
function Download-File {
    param([string]$Url, [string]$OutFile, [string]$Label)
    Write-Host "  Downloading $Label ..."
    try {
        $wc = New-Object System.Net.WebClient
        $wc.Headers.Add("User-Agent", "Mozilla/5.0")
        $wc.DownloadFile($Url, $OutFile)
    }
    catch {
        # Fallback to Invoke-WebRequest
        Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing
    }
    if (-not (Test-Path $OutFile) -or (Get-Item $OutFile).Length -lt 1024) {
        throw "Download failed or file is too small: $OutFile"
    }
    Write-Host "  Download complete." -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# 1. Enable IIS and required Windows features
# ---------------------------------------------------------------------------
Write-Host "[1/6] Enabling IIS and Windows features..." -ForegroundColor Yellow

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
Write-Host ""

# ---------------------------------------------------------------------------
# 2. Install .NET 8 Hosting Bundle
# ---------------------------------------------------------------------------
Write-Host "[2/6] Installing .NET 8 Hosting Bundle..." -ForegroundColor Yellow

$dotnetInstalled = $false
try {
    $dotnetVer = & dotnet --version 2>$null
    if ($dotnetVer -and $dotnetVer.StartsWith("8.")) {
        $dotnetInstalled = $true
    }
} catch {}

if (-not $dotnetInstalled) {
    # Direct download from Microsoft
    $dotnetUrl  = "https://download.visualstudio.microsoft.com/download/pr/9d6b6b6f-8b48-4f7b-b970-4a4b59e66cf3/b21b64cf24e6d2bf13dd8a64dd4f3e91/dotnet-hosting-8.0.8-win.exe"
    $dotnetFile = "$env:TEMP\dotnet-hosting-8.exe"
    Download-File -Url $dotnetUrl -OutFile $dotnetFile -Label ".NET 8 Hosting Bundle"
    Start-Process -FilePath $dotnetFile -ArgumentList "/quiet", "/norestart" -Wait
    Write-Host "  .NET 8 Hosting Bundle installed." -ForegroundColor Green
    # Refresh PATH so dotnet is available immediately
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH", "User")
} else {
    Write-Host "  .NET 8 already installed ($dotnetVer), skipping." -ForegroundColor Gray
}
Write-Host ""

# ---------------------------------------------------------------------------
# 3. Install Node.js 20 LTS
# ---------------------------------------------------------------------------
Write-Host "[3/6] Installing Node.js 20 LTS..." -ForegroundColor Yellow

$nodeInstalled = $false
try {
    $nodeVer = & node --version 2>$null
    if ($nodeVer) { $nodeInstalled = $true }
} catch {}

if (-not $nodeInstalled) {
    $nodeUrl  = "https://nodejs.org/dist/v20.17.0/node-v20.17.0-x64.msi"
    $nodeFile = "$env:TEMP\node-setup.msi"
    Download-File -Url $nodeUrl -OutFile $nodeFile -Label "Node.js 20 LTS"
    Start-Process msiexec.exe -ArgumentList "/i", "`"$nodeFile`"", "/quiet", "/norestart" -Wait
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH", "User")
    Write-Host "  Node.js installed." -ForegroundColor Green
} else {
    Write-Host "  Node.js already installed ($nodeVer), skipping." -ForegroundColor Gray
}
Write-Host ""

# ---------------------------------------------------------------------------
# 4. Install PostgreSQL 16
# ---------------------------------------------------------------------------
Write-Host "[4/6] Installing PostgreSQL 16..." -ForegroundColor Yellow

$pgDir      = "C:\Program Files\PostgreSQL\16"
$pgPassword = "postgres"  # CHANGE THIS before production!
$pgPort     = "5432"

if (-not (Test-Path "$pgDir\bin\psql.exe")) {
    # Direct installer from EnterpriseDB (no redirect, no session cookie required)
    $pgUrl  = "https://get.enterprisedb.com/postgresql/postgresql-16.4-1-windows-x64.exe"
    $pgFile = "$env:TEMP\postgresql-16-setup.exe"
    Write-Host "  Downloading PostgreSQL installer (~200 MB, please wait)..."
    Download-File -Url $pgUrl -OutFile $pgFile -Label "PostgreSQL 16"

    Write-Host "  Running PostgreSQL installer (silent mode)..."
    $pgArgs = "--mode unattended --superpassword $pgPassword --servicename postgresql-x64-16 --serverport $pgPort"
    Start-Process -FilePath $pgFile -ArgumentList $pgArgs -Wait
    Write-Host "  PostgreSQL 16 installed." -ForegroundColor Green
    Write-Host "  Superuser password: $pgPassword  <-- CHANGE IN PRODUCTION!" -ForegroundColor Yellow
} else {
    Write-Host "  PostgreSQL already installed, skipping." -ForegroundColor Gray
}

# Create the opshub database
Write-Host "  Creating 'opshub' database..."
$env:PGPASSWORD = $pgPassword
$psqlExe = "$pgDir\bin\psql.exe"
if (Test-Path $psqlExe) {
    & $psqlExe -U postgres -c "CREATE DATABASE opshub;" 2>&1 | Out-Null
    Write-Host "  Database 'opshub' ready." -ForegroundColor Green
}
Write-Host ""

# ---------------------------------------------------------------------------
# 5. Install Redis for Windows (Memurai Developer - free)
# ---------------------------------------------------------------------------
Write-Host "[5/6] Installing Redis (Memurai Developer edition)..." -ForegroundColor Yellow

$redisService = Get-Service -Name "Memurai" -ErrorAction SilentlyContinue
if (-not $redisService) {
    try {
        # Try winget first (available on Windows Server 2022 / Windows 10+)
        $winget = Get-Command winget -ErrorAction SilentlyContinue
        if ($winget) {
            Write-Host "  Installing Memurai via winget..."
            & winget install --id Memurai.Memurai --silent --accept-package-agreements --accept-source-agreements
        } else {
            # Fallback: download MSI directly
            $memuraiUrl  = "https://www.memurai.com/downloads/memurai-developer-4.1.0.msi"
            $memuraiFile = "$env:TEMP\memurai-setup.msi"
            Download-File -Url $memuraiUrl -OutFile $memuraiFile -Label "Memurai Developer"
            Start-Process msiexec.exe -ArgumentList "/i", "`"$memuraiFile`"", "/quiet", "/norestart" -Wait
        }
        Start-Service "Memurai" -ErrorAction SilentlyContinue
        Write-Host "  Memurai (Redis) installed and started." -ForegroundColor Green
    }
    catch {
        Write-Host ""
        Write-Host "  WARNING: Could not auto-install Memurai." -ForegroundColor Yellow
        Write-Host "  Install Redis manually using ONE of these options:" -ForegroundColor Yellow
        Write-Host "    Option A (recommended): winget install Memurai.Memurai" -ForegroundColor White
        Write-Host "    Option B: Download from https://www.memurai.com/get-memurai" -ForegroundColor White
        Write-Host "    Option C: Enable WSL2, then: wsl --install; sudo apt install redis-server" -ForegroundColor White
        Write-Host ""
    }
} else {
    Write-Host "  Memurai (Redis) already installed, skipping." -ForegroundColor Gray
}
Write-Host ""

# ---------------------------------------------------------------------------
# 6. Install IIS URL Rewrite Module
# ---------------------------------------------------------------------------
Write-Host "[6/6] Installing IIS URL Rewrite Module..." -ForegroundColor Yellow

$rewriteKey = "HKLM:\SOFTWARE\Microsoft\IIS Extensions\URL Rewrite"
if (-not (Test-Path $rewriteKey)) {
    $rewriteUrl  = "https://download.microsoft.com/download/1/2/8/128E2E22-C1B9-44A4-BE2A-5859ED1D4592/rewrite_amd64_en-US.msi"
    $rewriteFile = "$env:TEMP\rewrite_amd64.msi"
    Download-File -Url $rewriteUrl -OutFile $rewriteFile -Label "IIS URL Rewrite Module"
    Start-Process msiexec.exe -ArgumentList "/i", "`"$rewriteFile`"", "/quiet", "/norestart" -Wait
    Write-Host "  URL Rewrite Module installed." -ForegroundColor Green
} else {
    Write-Host "  URL Rewrite already installed, skipping." -ForegroundColor Gray
}
Write-Host ""

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
Write-Host "=== Prerequisites installation complete! ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Close and reopen PowerShell (to refresh PATH)" -ForegroundColor White
Write-Host "  2. Run: .\deploy-app.ps1" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT: Edit appsettings.json to set your IBM credentials before running." -ForegroundColor Yellow
Write-Host "SECURITY:  Change the PostgreSQL password from 'postgres' before production!" -ForegroundColor Red
Write-Host ""
