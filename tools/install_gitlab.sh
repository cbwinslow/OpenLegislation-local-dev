#!/bin/bash

set -euo pipefail

# OpenLegislation GitLab Installer for Ubuntu/Debian (Bare Metal Omnibus)
# Equivalent to Ansible playbook; installs GitLab EE/CE via omnibus package

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 1>&2
   exit 1
fi

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
GITLAB_EXTERNAL_URL="${GITLAB_EXTERNAL_URL:-http://localhost}"
GITLAB_ROOT_EMAIL="${GITLAB_ROOT_EMAIL:-admin@example.com}"
GITLAB_ROOT_PASS="${GITLAB_ROOT_PASS:-changeme123}"
GITLAB_EDITION="ee"  # ee or ce
INSTALL_DIR="/opt/gitlab"

log "Updating system packages..."
apt update && apt upgrade -y

log "Installing prerequisites..."
apt install -y curl openssh-server ca-certificates tzdata postfix

log "Downloading GitLab $GITLAB_EDITION Omnibus installer..."
curl -sSL https://packages.gitlab.com/install/repositories/gitlab/gitlab-$GITLAB_EDITION/script.deb.sh | bash

log "Installing GitLab $GITLAB_EDITION..."
EXTERNAL_URL="$GITLAB_EXTERNAL_URL" apt install -y gitlab-$GITLAB_EDITION

log "Configuring GitLab..."
cat > /etc/gitlab/gitlab.rb << EOF
# External URL
external_url '$GITLAB_EXTERNAL_URL'

# Email
gitlab_rails['gitlab_email_from'] = 'noreply@example.com'
gitlab_rails['gitlab_email_reply_to'] = '$GITLAB_ROOT_EMAIL'

# Root account
gitlab_rails['initial_root_password'] = '$GITLAB_ROOT_PASS'

# Timezone (set to system or specific)
gitlab_rails['time_zone'] = 'UTC'

# Disable unnecessary components if needed
# postgresql['enable'] = false  # if using external DB
# redis['enable'] = false

EOF

log "Reconfiguring GitLab to apply settings..."
gitlab-ctl reconfigure

log "Starting GitLab services..."
gitlab-ctl start
gitlab-ctl status

log "GitLab $GITLAB_EDITION installation complete."
log "Access: $GITLAB_EXTERNAL_URL"
log "Initial login: $GITLAB_ROOT_EMAIL / $GITLAB_ROOT_PASS"
log "Logs: gitlab-ctl tail"
log "Backup: gitlab-ctl backup"

warn "For production: Set HTTPS (external_url 'https://'), configure SMTP, add firewall rules (ufw allow 80,443,22), increase memory (4GB+ RAM), set strong root pass."
warn "Edition: Change GITLAB_EDITION=ce to install Community Edition."
warn "Post-install: Run 'gitlab-ctl reconfigure' after rb edits."

log "Testing installation..."
if gitlab-ctl status | grep -q "run:"; then
    log "All GitLab services are running."
else
    warn "Some services not running; check gitlab-ctl status."
fi
sleep 10
curl -s "$GITLAB_EXTERNAL_URL" | grep -q "GitLab" && log "GitLab web UI accessible." || warn "UI not ready; wait and check logs."
