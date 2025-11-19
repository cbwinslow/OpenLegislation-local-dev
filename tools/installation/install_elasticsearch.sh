#!/bin/bash

set -euo pipefail

# OpenLegislation Elasticsearch Installer for Ubuntu/Debian
# Installs Elasticsearch 8.14.3 for bare metal, configures single-node

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

# Default values - can override with env vars
ES_VERSION="8.14.3"
ES_HEAP="1g"  # Adjust based on RAM (e.g., 1g for small, 4g+ for prod)

log "Updating system packages..."
apt update && apt upgrade -y

log "Installing prerequisites..."
apt install -y wget gnupg apt-transport-https lsb-release

log "Downloading and adding Elasticsearch GPG key..."
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg

log "Adding Elasticsearch APT repository..."
echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x apt stable main" | tee /etc/apt/sources.list.d/elastic-8.x.list

log "Updating APT index with Elastic repo..."
apt update

log "Installing Elasticsearch $ES_VERSION..."
apt install -y elasticsearch=$ES_VERSION

log "Configuring Elasticsearch for single-node discovery..."
cat > /etc/elasticsearch/elasticsearch.yml << EOF
# ======================== Elasticsearch Configuration =========================
#
# NOTE: Elasticsearch comes with reasonable defaults for most settings.
#       Before you set out to tweak and tune the configuration, make sure you
#       understand what are you trying to accomplish and the consequences.

# OpenLegislation single-node setup
cluster.name: openleg-cluster
node.name: node-1

# Bind to localhost and loopback
network.host: 127.0.0.1

# Single-node discovery
discovery.type: single-node

# Disable X-Pack security for basic setup (enable for prod with certs/auth)
xpack.security.enabled: false

# Paths
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch

# JVM Heap
# Set in /etc/elasticsearch/jvm.options below

EOF

log "Configuring JVM heap size to $ES_HEAP..."
echo "# OpenLegislation JVM options" > /etc/elasticsearch/jvm.options.d/openleg.options
echo "-Xms$ES_HEAP" >> /etc/elasticsearch/jvm.options.d/openleg.options
echo "-Xmx$ES_HEAP" >> /etc/elasticsearch/jvm.options.d/openleg.options

log "Starting and enabling Elasticsearch service..."
systemctl daemon-reload
systemctl start elasticsearch
systemctl enable elasticsearch

log "Waiting for Elasticsearch to start (up to 60s)..."
sleep 10
for i in {1..6}; do
    if curl -s http://localhost:9200 > /dev/null; then
        log "Elasticsearch is running!"
        break
    fi
    sleep 10
done

log "Elasticsearch $ES_VERSION installation complete."
log "Access: http://localhost:9200"
log "Cluster health command: curl -X GET 'localhost:9200/_cluster/health?pretty'"

warn "For production: Enable X-Pack security (xpack.security.enabled: true), set up TLS, adjust heap/RAM, configure remote access in elasticsearch.yml (network.host: 0.0.0.0)."
warn "Logs: /var/log/elasticsearch/openleg-cluster.log"
warn "Data: /var/lib/elasticsearch"

log "Testing installation..."
curl -s http://localhost:9200/_cluster/health | grep -q '"status":"green"' && log "Cluster health is green!" || warn "Cluster health may be yellow (normal for single-node during init)."
