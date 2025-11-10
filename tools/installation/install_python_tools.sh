#!/bin/bash

set -euo pipefail

# OpenLegislation Python Ingestion Tools Installer for Ubuntu/Debian
# Sets up Python environment with uv, installs dependencies from pyproject.toml

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" 1>&2
}

# Default values - override with env vars
TOOLS_DIR="/opt/openleg/tools"
VENV_DIR="$TOOLS_DIR/venv"
PYTHON_VERSION="3.12"

# No root required; user-level install
if [[ $EUID -eq 0 ]]; then
   warn "Running as root; consider non-root for venv activation."
fi

log "Installing Python $PYTHON_VERSION (if not present)..."
if ! command -v python$PYTHON_VERSION &> /dev/null; then
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y python$PYTHON_VERSION python$PYTHON_VERSION-venv python$PYTHON_VERSION-dev
    else
        error "APT not found; manual Python install required."
    fi
fi

log "Installing uv (Python package manager)..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc
fi

log "Creating tools directory $TOOLS_DIR..."
mkdir -p "$TOOLS_DIR"
cd "$TOOLS_DIR"

log "Copying Python tools from current project..."
if [ -e "../../../tools" ]; then  # Assuming run from current project tools/
    rsync -av ../../../tools/ . --exclude='venv' --exclude='.git' --exclude='__pycache__'
else
    log "Tools dir not found; ensure script is run from OpenLegislation/tools or adjust path."
fi

log "Creating virtual environment with uv..."
uv venv --python $PYTHON_VERSION
source venv/bin/activate

log "Installing dependencies with uv sync..."
uv sync  # Installs from pyproject.toml and uv.lock

log "Making shell scripts executable..."
find . -name "*.sh" -exec chmod +x {} \;

log "Python tools installation complete."
log "Activate venv: source $VENV_DIR/bin/activate"
log "Run example: ./bulk_ingest_congress_gov.sh or python govinfo_data_connector.py"
log "Added to PATH? Add 'export PATH=\"$VENV_DIR/bin:\$PATH\"' to ~/.bashrc for scripts like uv run python ..."

warn "For system-wide access, consider symlinking key scripts to /usr/local/bin after activation."
warn "Deps include: uv sync will pull from pyproject (e.g., requests, pandas for ingestion)."

log "Testing setup..."
source venv/bin/activate
python --version | grep -q "$PYTHON_VERSION" && log "Python $PYTHON_VERSION active."
uv --version && log "uv installed."
which python && log "Python in venv."
