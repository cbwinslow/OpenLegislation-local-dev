#!/bin/bash

set -euo pipefail

# OpenLegislation Tomcat 9 Installer for Ubuntu/Debian
# Installs OpenJDK 21 and Tomcat 9, configures basic setup

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

# Default values
TOMCAT_PORT="8080"
TOMCAT_MEMORY="512m"  # Adjust for prod (e.g., 2g+)

log "Updating system packages..."
apt update && apt upgrade -y

log "Installing OpenJDK 21..."
apt install -y openjdk-21-jdk

log "Installing Tomcat 9..."
apt install -y tomcat9 tomcat9-admin tomcat9-common tomcat9-user

log "Configuring Tomcat memory via CATALINA_OPTS..."
echo "export CATALINA_OPTS=\"-Xms$TOMCAT_MEMORY -Xmx$TOMCAT_MEMORY -XX:+UseG1GC\"" >> /etc/default/tomcat9

log "Configuring Tomcat server.xml for port $TOMCAT_PORT (if needed)..."
# Ensure Connector port is 8080 (default)
if ! grep -q "Connector port=\"$TOMCAT_PORT\"" /etc/tomcat9/server.xml; then
    sed -i "s/Connector port=\"8080\"/Connector port=\"$TOMCAT_PORT\"/" /etc/tomcat9/server.xml || warn "Could not update port; manual edit needed."
fi

log "Setting Tomcat user permissions for OpenLegislation WAR deployment..."
# Create dir for custom WARs if needed
mkdir -p /opt/openleg/webapps
chown -R tomcat:tomcat /opt/openleg
chmod 755 /opt/openleg/webapps

log "Starting and enabling Tomcat 9 service..."
systemctl daemon-reload
systemctl start tomcat9
systemctl enable tomcat9

log "Waiting for Tomcat to start..."
sleep 10
if curl -s http://localhost:$TOMCAT_PORT > /dev/null; then
    log "Tomcat is running on port $TOMCAT_PORT!"
else
    warn "Tomcat may not be fully started; check with systemctl status tomcat9"
fi

log "Tomcat 9 installation complete."
log "Access: http://localhost:$TOMCAT_PORT"
log "Manager app: /manager (default creds: tomcat/tomcat; change in prod)"
log "WAR deployment dir: /var/lib/tomcat9/webapps or use /opt/openleg/webapps for custom"

warn "For production: Configure HTTPS, change default creds in /etc/tomcat9/tomcat-users.xml, adjust memory, enable remote admin if needed."
warn "To deploy OpenLegislation: Copy legislation##3.10.2.war to /var/lib/tomcat9/webapps/ and restart tomcat9."
warn "JAVA_HOME: $(java -XshowSettings:properties -version 2>&1 | grep 'java.home' | awk '{print $3}')"

log "Testing installation..."
if systemctl is-active --quiet tomcat9; then
    log "Tomcat service is active."
else
    error "Tomcat service failed to start. Check logs: journalctl -u tomcat9"
fi
