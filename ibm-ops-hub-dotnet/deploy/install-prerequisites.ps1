#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Checks and installs prerequisites for IBM Ops Hub on Windows Server.
    If automatic download is blocked by a corporate firewall, the script
    prints the exact download URL and waits for you to install manually.

.NOTES
    Run as Administrator in PowerShell 5.1+
    Usage: .\install-prerequisites.ps1
#>

# Never stop on errors - we handle every failure manually
$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "=== IBM Ops Hub - Prerequisites Check ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script enables IIS, then checks each required component." -ForegroundColor Gray
Write-Host "If a download fails (e.g. corporate firewall), it prints the URL" -ForegroundColor Gray
Write-Host "so you can download manually and re-run." -ForegroundColor Gray
Write-Host ""

$manualStepsNeeded = @()

# ---------------------------------------------------------------------------
# Helper: try to download a file, return $true on success
# ---------------------------------------------------------------------------
function Try-Download {
    param([string]$Url, [string]$OutFile)
    try {
        $wc = New-Object System.Net.WebClient
        $wc.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        $wc.DownloadFile($Url, $OutFile)
        if ((Test-Path $OutFile) -and (Get-Item $OutFile).Length -gt 100000) {
            return $true
        }
    } catch {}
    # Fallback: Invoke-WebRequest
    try {
        Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing -ErrorAction Stop
        if ((Test-Path $OutFile) -and (Get-Item $OutFile).Length -gt 100000) {
            return $true
        }
    } catch {}
    return $false
}

# ---------------------------------------------------------------------------
# 1. Enable IIS (no internet needed - uses Windows components)
# ---------------------------------------------------------------------------
Write-Host "[1/6] Enabling IIS and Windows features..." -ForegroundColor Yellow

$features = @(
    "Web-Server", "Web-WebServer", "Web-Common-Http",
    "Web-Default-Doc", "Web-Static-Content", "Web-Http-Errors",
    "Web-Http-Redirect", "Web-App-Dev", "Web-Net-Ext45",
    "Web-Asp-Net45", "Web-ISAPI-Ext", "Web-ISAPI-Filter",
    "Web-Health", "Web-Http-Logging", "Web-Mgmt-Tools",
    "Web-Mgmt-Console", "Web-Scripting-Tools"
)

$iisOk = $true
foreach ($f in $features) {
    $result = Install-WindowsFeature -Name $f -IncludeManagementTools -ErrorAction SilentlyContinue
    if ($result -and -not $result.Success) { $iisOk = $false }
}

if ($iisOk) {
    Write-Host "  [OK] IIS features enabled." -ForegroundColor Green
} else {
    Write-Host "  [WARN] Some IIS features may not have installed. Check Server Manager." -ForegroundColor Yellow
}
Write-Host ""

# ---------------------------------------------------------------------------
# 2. .NET 8 Hosting Bundle
# ---------------------------------------------------------------------------
Write-Host "[2/6] Checking .NET 8 Hosting Bundle..." -ForegroundColor Yellow

$dotnetOk = $false
try {
    $dotnetVer = & dotnet --version 2>$null
    if ($dotnetVer -and ($dotnetVer -match "^8\.")) { $dotnetOk = $true }
} catch {}

# Also check registry (ASP.NET Core Runtime may be installed without SDK)
if (-not $dotnetOk) {
    $aspKey = "HKLM:\SOFTWARE\dotnet\Setup\InstalledVersions\x64\sharedhost"
    if (Test-Path $aspKey) { $dotnetOk = $true }
}

if ($dotnetOk) {
    Write-Host "  [OK] .NET 8 already installed." -ForegroundColor Green
} else {
    Write-Host "  [NOT FOUND] .NET 8 Hosting Bundle not detected." -ForegroundColor Red
    Write-Host "  Trying auto-download..." -ForegroundColor Gray

    $dotnetUrl  = "https://download.visualstudio.microsoft.com/download/pr/9d6b6b6f-8b48-4f7b-b970-4a4b59e66cf3/b21b64cf24e6d2bf13dd8a64dd4f3e91/dotnet-hosting-8.0.8-win.exe"
    $dotnetFile = "$env:TEMP\dotnet-hosting-8.exe"

    if (Try-Download -Url $dotnetUrl -OutFile $dotnetFile) {
        Write-Host "  Download OK. Installing..."
        Start-Process -FilePath $dotnetFile -ArgumentList "/quiet", "/norestart" -Wait -ErrorAction SilentlyContinue
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
        Write-Host "  [OK] .NET 8 Hosting Bundle installed." -ForegroundColor Green
    } else {
        Write-Host "  [ACTION REQUIRED] Auto-download blocked. Download manually:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "    https://dotnet.microsoft.com/en-us/download/dotnet/8.0" -ForegroundColor White
        Write-Host "    --> Click 'Hosting Bundle' under 'ASP.NET Core Runtime 8.0'" -ForegroundColor White
        Write-Host ""
        Write-Host "  Install it, then re-run this script." -ForegroundColor Yellow
        $manualStepsNeeded += ".NET 8 Hosting Bundle"
    }
}
Write-Host ""

# ---------------------------------------------------------------------------
# 3. Node.js 20 LTS
# ---------------------------------------------------------------------------
Write-Host "[3/6] Checking Node.js..." -ForegroundColor Yellow

$nodeOk = $false
try {
    $nodeVer = & node --version 2>$null
    if ($nodeVer) { $nodeOk = $true }
} catch {}

if ($nodeOk) {
    Write-Host "  [OK] Node.js already installed ($nodeVer)." -ForegroundColor Green
} else {
    Write-Host "  [NOT FOUND] Node.js not detected." -ForegroundColor Red
    Write-Host "  Trying auto-download..." -ForegroundColor Gray

    $nodeUrl  = "https://nodejs.org/dist/v20.17.0/node-v20.17.0-x64.msi"
    $nodeFile = "$env:TEMP\node-setup.msi"

    if (Try-Download -Url $nodeUrl -OutFile $nodeFile) {
        Write-Host "  Download OK. Installing..."
        Start-Process msiexec.exe -ArgumentList "/i", "`"$nodeFile`"", "/quiet", "/norestart" -Wait -ErrorAction SilentlyContinue
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
        Write-Host "  [OK] Node.js installed." -ForegroundColor Green
    } else {
        Write-Host "  [ACTION REQUIRED] Auto-download blocked. Download manually:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "    https://nodejs.org/en/download  --> Windows x64 Installer (.msi)" -ForegroundColor White
        Write-Host ""
        Write-Host "  Install it, then re-run this script." -ForegroundColor Yellow
        $manualStepsNeeded += "Node.js 20 LTS"
    }
}
Write-Host ""

# ---------------------------------------------------------------------------
# 4. PostgreSQL 16
# ---------------------------------------------------------------------------
Write-Host "[4/6] Checking PostgreSQL..." -ForegroundColor Yellow

$pgDir  = "C:\Program Files\PostgreSQL\16"
$pgPass = "postgres"  # Change before production!
$pgOk   = Test-Path "$pgDir\bin\psql.exe"

if ($pgOk) {
    Write-Host "  [OK] PostgreSQL already installed." -ForegroundColor Green
} else {
    Write-Host "  [NOT FOUND] PostgreSQL not detected." -ForegroundColor Red
    Write-Host "  Trying auto-download (~200 MB)..." -ForegroundColor Gray

    # Direct EDB installer URL (no redirect, no session required)
    $pgUrl  = "https://get.enterprisedb.com/postgresql/postgresql-16.4-1-windows-x64.exe"
    $pgFile = "$env:TEMP\postgresql-16-setup.exe"

    if (Try-Download -Url $pgUrl -OutFile $pgFile) {
        Write-Host "  Download OK. Installing (this takes ~2 minutes, please wait)..."
        $pgArgs = "--mode unattended --superpassword $pgPass --servicename postgresql-x64-16 --serverport 5432"
        Start-Process -FilePath $pgFile -ArgumentList $pgArgs -Wait -ErrorAction SilentlyContinue
        $pgOk = Test-Path "$pgDir\bin\psql.exe"
        if ($pgOk) {
            Write-Host "  [OK] PostgreSQL installed. Password: $pgPass" -ForegroundColor Green
            Write-Host "  REMINDER: Change this password before production use!" -ForegroundColor Yellow
        } else {
            Write-Host "  [WARN] Installer ran but psql.exe not found. Check C:\Program Files\PostgreSQL\" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  [ACTION REQUIRED] Auto-download blocked. Download manually:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "    https://www.postgresql.org/download/windows/" -ForegroundColor White
        Write-Host "    --> Click 'Download the installer' --> Version 16 --> Windows x86-64" -ForegroundColor White
        Write-Host ""
        Write-Host "  During install: set password to 'postgres', port to 5432." -ForegroundColor White
        Write-Host "  Then re-run this script." -ForegroundColor Yellow
        $manualStepsNeeded += "PostgreSQL 16"
    }
}

# Create the opshub database (only if psql exists)
if (Test-Path "$pgDir\bin\psql.exe") {
    Write-Host "  Creating 'opshub' database..."
    $env:PGPASSWORD = $pgPass
    & "$pgDir\bin\psql.exe" -U postgres -c "CREATE DATABASE opshub;" 2>&1 | Out-Null
    Write-Host "  [OK] Database 'opshub' ready." -ForegroundColor Green
}
Write-Host ""

# ---------------------------------------------------------------------------
# 5. Redis (Memurai Developer - free)
# ---------------------------------------------------------------------------
Write-Host "[5/6] Checking Redis (Memurai)..." -ForegroundColor Yellow

$redisOk = $null -ne (Get-Service "Memurai" -ErrorAction SilentlyContinue)

if ($redisOk) {
    Write-Host "  [OK] Memurai (Redis) already installed." -ForegroundColor Green
} else {
    Write-Host "  [NOT FOUND] Redis service not detected." -ForegroundColor Red

    # Try winget first (available on Windows Server 2022, Windows 10 21H2+)
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host "  Trying: winget install Memurai.Memurai ..."
        & winget install --id Memurai.Memurai --silent --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
        $redisOk = $null -ne (Get-Service "Memurai" -ErrorAction SilentlyContinue)
    }

    if (-not $redisOk) {
        # Try direct MSI download
        $memuraiUrl  = "https://www.memurai.com/downloads/memurai-developer-4.1.0.msi"
        $memuraiFile = "$env:TEMP\memurai-setup.msi"
        if (Try-Download -Url $memuraiUrl -OutFile $memuraiFile) {
            Start-Process msiexec.exe -ArgumentList "/i", "`"$memuraiFile`"", "/quiet", "/norestart" -Wait -ErrorAction SilentlyContinue
            $redisOk = $null -ne (Get-Service "Memurai" -ErrorAction SilentlyContinue)
        }
    }

    if ($redisOk) {
        Start-Service "Memurai" -ErrorAction SilentlyContinue
        Write-Host "  [OK] Memurai installed and started." -ForegroundColor Green
    } else {
        Write-Host "  [ACTION REQUIRED] Could not auto-install Redis. Choose one:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Option A - Memurai (recommended for Windows Server):" -ForegroundColor White
        Write-Host "    https://www.memurai.com/get-memurai  --> Download Developer edition (free)" -ForegroundColor White
        Write-Host ""
        Write-Host "  Option B - winget (if available on your server):" -ForegroundColor White
        Write-Host "    winget install Memurai.Memurai" -ForegroundColor White
        Write-Host ""
        Write-Host "  Install it, then re-run this script." -ForegroundColor Yellow
        $manualStepsNeeded += "Redis / Memurai"
    }
}
Write-Host ""

# ---------------------------------------------------------------------------
# 6. IIS URL Rewrite Module
# ---------------------------------------------------------------------------
Write-Host "[6/6] Checking IIS URL Rewrite Module..." -ForegroundColor Yellow

$rewriteOk = Test-Path "HKLM:\SOFTWARE\Microsoft\IIS Extensions\URL Rewrite"

if ($rewriteOk) {
    Write-Host "  [OK] URL Rewrite already installed." -ForegroundColor Green
} else {
    $rewriteUrl  = "https://download.microsoft.com/download/1/2/8/128E2E22-C1B9-44A4-BE2A-5859ED1D4592/rewrite_amd64_en-US.msi"
    $rewriteFile = "$env:TEMP\rewrite_amd64.msi"

    if (Try-Download -Url $rewriteUrl -OutFile $rewriteFile) {
        Start-Process msiexec.exe -ArgumentList "/i", "`"$rewriteFile`"", "/quiet", "/norestart" -Wait -ErrorAction SilentlyContinue
        Write-Host "  [OK] URL Rewrite Module installed." -ForegroundColor Green
    } else {
        Write-Host "  [ACTION REQUIRED] Download URL Rewrite manually:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "    https://www.iis.net/downloads/microsoft/url-rewrite" -ForegroundColor White
        Write-Host "    --> Download 'URL Rewrite Module 2.1'" -ForegroundColor White
        Write-Host ""
        $manualStepsNeeded += "IIS URL Rewrite Module"
    }
}
Write-Host ""

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Installation Summary" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if ($manualStepsNeeded.Count -eq 0) {
    Write-Host "  All prerequisites installed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Next steps:" -ForegroundColor White
    Write-Host "  1. Close and reopen PowerShell (to refresh PATH)" -ForegroundColor White
    Write-Host "  2. Run: .\deploy-app.ps1" -ForegroundColor White
} else {
    Write-Host "  The following require MANUAL download and install:" -ForegroundColor Yellow
    Write-Host ""
    foreach ($step in $manualStepsNeeded) {
        Write-Host "    [ ] $step" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "  After installing the items above:" -ForegroundColor White
    Write-Host "  Run this script again to verify and continue." -ForegroundColor White
}

Write-Host ""
Write-Host "  SECURITY: Change the PostgreSQL password in appsettings.json before production!" -ForegroundColor Yellow
Write-Host ""
