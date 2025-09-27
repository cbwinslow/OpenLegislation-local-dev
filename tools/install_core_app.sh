#!/bin/bash

set -euo pipefail

# OpenLegislation Core Java App Installer for Ubuntu/Debian
# Builds and deploys the Java backend WAR to Tomcat, configures app.properties, runs Flyway

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
INSTALL_DIR="/opt/openleg"
REPO_URL="https://github.com/nysenate/OpenLegislation.git"
BRANCH="dev"  # or master
DB_URL="${DB_URL:-jdbc:postgresql://localhost:5432/openleg}"
DB_USER="${DB_USER:-openleg}"
DB_PASS="${DB_PASS:-openleg_pass}"
ES_HOST="${ES_HOST:-localhost:9200}"
APP_PROPERTIES_SRC="src/main/resources/app.properties.local"
WAR_TARGET="/var/lib/tomcat9/webapps/legislation.war"

log "Installing Maven and Node.js (if not present)..."
if ! command -v mvn &> /dev/null; then
    apt install -y maven
fi
if ! command -v npm &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt install -y nodejs
fi

log "Creating installation directory $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

if [ ! -d ".git" ]; then
    log "Cloning OpenLegislation repo..."
    git clone -b "$BRANCH" "$REPO_URL" .
else
    log "Repo already exists; pulling latest..."
    git pull origin "$BRANCH"
fi

log "Building the WAR file (skipping tests)..."
mvn clean package -DskipTests=true

# Find WAR - from POM: finalName legislation##3.10.2.war, but general
WAR_FILE=$(find target -name "legislation*.war" | head -1)
if [ -z "$WAR_FILE" ]; then
    error "WAR file not found in target/. Check build logs."
fi

log "Copying WAR to Tomcat webapps: $WAR_FILE -> $WAR_TARGET"
cp "$WAR_FILE" "$WAR_TARGET"
chown tomcat:tomcat "$WAR_TARGET"

log "Configuring app.properties.local..."
if [ -f "$APP_PROPERTIES_SRC" ]; then
    cp "$APP_PROPERTIES_SRC" src/main/resources/app.properties
    # Replace placeholders with env vars if present
    if [ -n "$DB_URL" ]; then
        sed -i "s|jdbc:postgresql://localhost:5432/openleg|$DB_URL|g" src/main/resources/app.properties
    fi
    if [ -n "$DB_USER" ]; then
        sed -i "s/username=.*$/username=$DB_USER/g" src/main/resources/app.properties
    fi
    if [ -n "$DB_PASS" ]; then
        sed -i "s/password=.*$/password=$DB_PASS/g" src/main/resources/app.properties
    fi
    if [ -n "$ES_HOST" ]; then
        sed -i "s/elasticsearch.host=.*$/elasticsearch.host=$ES_HOST/g" src/main/resources/app.properties || warn "ES host placeholder not found; manual edit needed."
    fi
    log "Updated app.properties with DB/ES config."
else
    warn "No app.properties.local found; using default. Manual config recommended."
fi

log "Running Flyway migrations for DB setup..."
mvn flyway:migrate -Dflyway.configFiles=src/main/resources/flyway.conf || warn "Flyway failed; ensure DB is running and accessible."

log "Restarting Tomcat to deploy the new WAR..."
systemctl restart tomcat9
sleep 20  # Wait for deployment

log "Core Java application installation complete."
log "App deployed at http://localhost:8080"
log "Check Tomcat logs: /var/log/tomcat9/catalina.out"
log "NY Senate Maven repo deps: If auth needed, set ~/.m2/settings.xml with credentials."

warn "For production: Secure app.properties, handle private Maven repo auth, monitor deployment status."
warn "Build logs: $INSTALL_DIR/target/surefire-reports/ (if tests run)"

log "Testing deployment..."
if curl -s http://localhost:8080 | grep -q "OpenLegislation"; then  # Assume some identifier
    log "App is responding!"
else
    warn "App may not be fully deployed yet; check logs."
fi
if systemctl is-active --quiet tomcat9; then
    log "Tomcat is active post-restart."
fi
