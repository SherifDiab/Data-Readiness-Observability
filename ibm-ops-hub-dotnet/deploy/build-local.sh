#!/usr/bin/env bash
# =============================================================================
# build-local.sh  — IBM Ops Hub build script for macOS / Linux
# =============================================================================
# Run this on your Mac (or any Linux machine) that has internet access.
# It produces an "artifacts/" folder you can copy to the Windows Server.
#
# USAGE:
#   cd ibm-ops-hub-dotnet
#   chmod +x deploy/build-local.sh
#   ./deploy/build-local.sh
#
# Then copy artifacts/ to the Windows Server and run:
#   .\deploy\deploy-app.ps1 -UseArtifacts -ArtifactsPath C:\path\to\artifacts
#
# PREREQUISITES on your Mac:
#   .NET 8 SDK   ->  https://dotnet.microsoft.com/en-us/download/dotnet/8.0
#                    (macOS pkg installer)
#   Node.js 20+  ->  https://nodejs.org/en/download  or  brew install node
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_DIR="${1:-$REPO_ROOT/artifacts}"

API_OUT="$OUT_DIR/api"
WEB_OUT="$OUT_DIR/www"
CFG_OUT="$OUT_DIR/deploy"

echo ""
echo "=== IBM Ops Hub - Local Build (macOS/Linux) ==="
echo "Repo root : $REPO_ROOT"
echo "Output    : $OUT_DIR"
echo ""

# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------
echo "Checking tools..."

# The macOS .NET installer puts dotnet in /usr/local/share/dotnet but doesn't
# always add it to PATH. Check known locations and add to PATH if needed.
if ! command -v dotnet &>/dev/null; then
    for candidate in \
        "/usr/local/share/dotnet" \
        "$HOME/.dotnet" \
        "/usr/local/bin"
    do
        if [ -x "$candidate/dotnet" ]; then
            export PATH="$candidate:$PATH"
            echo "  (added $candidate to PATH)"
            break
        fi
    done
fi

if ! command -v dotnet &>/dev/null; then
    echo ""
    echo "ERROR: dotnet not found in PATH or common macOS locations."
    echo ""
    echo "  Quick fix — paste this in your terminal, then re-run the script:"
    echo "    export PATH=\"\$PATH:/usr/local/share/dotnet\""
    echo ""
    echo "  To make it permanent, add the line above to ~/.zshrc (or ~/.bash_profile):"
    echo "    echo 'export PATH=\"\$PATH:/usr/local/share/dotnet\"' >> ~/.zshrc"
    echo "    source ~/.zshrc"
    echo ""
    echo "  If you haven't installed .NET 8 SDK yet:"
    echo "    https://dotnet.microsoft.com/en-us/download/dotnet/8.0"
    echo "    --> macOS -> x64 or Arm64 Installer (.pkg)"
    echo ""
    exit 1
fi

SDK_OK=false
while IFS= read -r line; do
    if [[ "$line" == 8.* ]]; then SDK_OK=true; fi
done < <(dotnet --list-sdks 2>/dev/null)

if [ "$SDK_OK" = false ]; then
    echo ""
    echo "ERROR: .NET 8 SDK not found (you have other versions but not 8.x)."
    echo "  https://dotnet.microsoft.com/en-us/download/dotnet/8.0"
    echo ""
    exit 1
fi
echo "  [OK] .NET 8 SDK"

if ! command -v node &>/dev/null; then
    echo ""
    echo "ERROR: node not found."
    echo "  brew install node   OR   https://nodejs.org/en/download"
    echo ""
    exit 1
fi
NODE_VER="$(node --version)"
echo "  [OK] Node.js $NODE_VER"
echo ""

# ---------------------------------------------------------------------------
# 1. Create output folders
# ---------------------------------------------------------------------------
echo "[1/4] Creating output folders..."
mkdir -p "$API_OUT" "$WEB_OUT" "$CFG_OUT"
echo "  Done."

# ---------------------------------------------------------------------------
# 2. Build .NET backend
# ---------------------------------------------------------------------------
echo "[2/4] Building .NET backend (dotnet publish)..."
BACKEND_SRC="$REPO_ROOT/backend/IbmOpsHub"

dotnet publish "$BACKEND_SRC" \
    -c Release \
    -o "$API_OUT" \
    --nologo

echo "  [OK] Backend built -> $API_OUT"

# ---------------------------------------------------------------------------
# 3. Build Angular frontend
# ---------------------------------------------------------------------------
echo "[3/4] Building Angular frontend..."
FRONTEND_SRC="$REPO_ROOT/frontend"

pushd "$FRONTEND_SRC" > /dev/null

if [ ! -d "node_modules" ]; then
    echo "  Running npm install (first time, may take a few minutes)..."
    npm install
fi

echo "  Running ng build..."
npm run build

popd > /dev/null

# Find the Angular dist output (Angular 17 puts it under browser/)
ANGULAR_DIST="$FRONTEND_SRC/dist/ibm-ops-hub-angular/browser"
if [ ! -d "$ANGULAR_DIST" ]; then
    ANGULAR_DIST="$FRONTEND_SRC/dist/ibm-ops-hub-angular"
fi
if [ ! -d "$ANGULAR_DIST" ]; then
    echo "ERROR: Angular dist folder not found. Expected: $ANGULAR_DIST"
    exit 1
fi

cp -r "$ANGULAR_DIST/." "$WEB_OUT/"
echo "  [OK] Frontend built -> $WEB_OUT"

# ---------------------------------------------------------------------------
# 4. Copy IIS config and deploy scripts
# ---------------------------------------------------------------------------
echo "[4/4] Copying deployment files..."
cp "$SCRIPT_DIR/frontend-web.config" "$CFG_OUT/"
cp "$SCRIPT_DIR/api-web.config"      "$CFG_OUT/"
cp "$SCRIPT_DIR/deploy-app.ps1"      "$CFG_OUT/"
echo "  Done."

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "============================================"
echo "  Build complete!"
echo "============================================"
echo ""
echo "  Artifacts folder: $OUT_DIR"
echo ""
echo "  NEXT STEPS:"
echo ""
echo "  1. Copy the 'artifacts' folder to your Windows Server."
echo "     From macOS terminal, e.g. with scp:"
echo ""
echo "       scp -r $OUT_DIR user@windows-server:'C:/ibm-deploy/artifacts'"
echo ""
echo "     Or zip it first:"
echo "       cd $REPO_ROOT"
echo "       zip -r artifacts.zip artifacts/"
echo "     Then transfer artifacts.zip and extract on the server."
echo ""
echo "  2. On the Windows Server (as Administrator in PowerShell):"
echo ""
echo "       cd C:\\ibm-deploy"
echo "       .\\deploy\\deploy-app.ps1 -UseArtifacts -ArtifactsPath C:\\ibm-deploy\\artifacts"
echo ""
echo "  NOTE: The server still needs IIS + .NET Hosting Bundle + URL Rewrite."
echo "  Run install-prerequisites.ps1 on the server first (no internet needed"
echo "  for IIS; Hosting Bundle needs to be manually downloaded if firewall blocks)."
echo ""
