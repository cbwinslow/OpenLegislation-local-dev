#!/bin/bash

set -euo pipefail

# OpenLegislation Bin Scripts and Cron Jobs Setup for Ubuntu/Debian
# Copies bin/ scripts to /opt/openleg/bin, makes executable, sets up example crontab

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

# Default values
BIN_DIR="/opt/openleg/bin"
CRON_USER="${CRON_USER:-root}"  # or current user

log "Creating bin directory $BIN_DIR..."
mkdir -p "$BIN_DIR"

log "Copying bin scripts from current project..."
if [ -d "../../../bin" ]; then  # Assuming run from tools/
    rsync -av ../../../bin/ "$BIN_DIR/"
    find "$BIN_DIR" -name "*.sh" -exec chmod +x {} \;
    log "Scripts copied and made executable: $(ls "$BIN_DIR"/*.sh)"
else
    warn "bin/ dir not found; ensure script run from project root/tools."
fi

log "Setting up example crontab for $CRON_USER..."
# Backup current crontab
(crontab -u "$CRON_USER" -l 2>/dev/null || true) | grep -v "# OpenLegislation" > /tmp/openleg_cron_backup

# Add example entries - adjust as needed
cat >> /tmp/openleg_cron_temp << EOF
# OpenLegislation Cron Jobs - Added by setup_bin_crons.sh
# Mirror aging data daily at 2AM
0 2 * * * $BIN_DIR/mirror_aging.sh >> /var/log/openleg/mirror_aging.log 2>&1

# Transfer data hourly
0 * * * * $BIN_DIR/xferdata.sh >> /var/log/openleg/xferdata.log 2>&1

# Cron for website (if applicable)
# 0 3 * * 0 $BIN_DIR/website_cron_d7.sh >> /var/log/openleg/website_cron.log 2>&1

EOF

cat /tmp/openleg_cron_backup /tmp/openleg_cron_temp > /tmp/openleg_cron_new
crontab -u "$CRON_USER" /tmp/openleg_cron_new

log "Cron setup complete. Entries added for common bin scripts."
log "View crontab: crontab -u $CRON_USER -l"
log "Logs: Create /var/log/openleg/ dir and ensure permissions if needed."

warn "Review and adjust cron entries based on your needs (e.g., frequencies, paths)."
warn "For non-root user: Ensure $CRON_USER has access to bin/ and logs."
warn "To remove: Edit crontab and delete # OpenLegislation lines."

log "Testing crontab load..."
crontab -u "$CRON_USER" -l | grep -q "OpenLegislation" && log "Cron entries installed." || warn "No cron changes detected."
