#!/bin/bash

set -euo pipefail

# OpenLegislation PostgreSQL Installer for Ubuntu/Debian
# Installs PostgreSQL, creates database/user, sets up basic config

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
DB_NAME="openleg"
DB_USER="openleg"
DB_PASS="${DB_PASS:-openleg_pass}"  # Set via env or default
POSTGRES_VERSION="14"  # Or latest stable

log "Updating system packages..."
apt update && apt upgrade -y

log "Installing PostgreSQL $POSTGRES_VERSION..."
apt install -y postgresql-$POSTGRES_VERSION postgresql-contrib-$POSTGRES_VERSION

log "Starting and enabling PostgreSQL service..."
systemctl start postgresql
systemctl enable postgresql

log "Configuring PostgreSQL to accept TCP connections..."
sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/$POSTGRES_VERSION/main/postgresql.conf
systemctl restart postgresql

log "Switching to postgres user to create $DB_USER and $DB_NAME..."
su - postgres -c "psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';\""
su - postgres -c "createdb -O $DB_USER $DB_NAME"
su - postgres -c "psql -d $DB_NAME -c 'ALTER USER $DB_USER CREATEDB;'"

log "Granting privileges to $DB_USER on $DB_NAME..."
su - postgres -c "psql -d $DB_NAME -c \"GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;\""

log "Configuring pg_hba.conf for md5 auth (local and host)..."
echo "local   all             postgres                                peer" | tee -a /etc/postgresql/$POSTGRES_VERSION/main/pg_hba.conf
echo "local   all             all                                     peer" | tee -a /etc/postgresql/$POSTGRES_VERSION/main/pg_hba.conf
echo "host    $DB_NAME        $DB_USER        127.0.0.1/32            md5" | tee -a /etc/postgresql/$POSTGRES_VERSION/main/pg_hba.conf
echo "host    $DB_NAME        $DB_USER        ::1/128                 md5" | tee -a /etc/postgresql/$POSTGRES_VERSION/main/pg_hba.conf
systemctl restart postgresql

log "PostgreSQL installation complete."
log "Database: $DB_NAME"
log "User: $DB_USER"
log "Password: $DB_PASS (change in production!)"
log "Connection string example: jdbc:postgresql://localhost:5432/$DB_NAME"

warn "For Flyway migrations, run them from the app directory after building: mvn flyway:migrate -Dflyway.configFiles=src/main/resources/flyway.conf"
warn "Edit /etc/postgresql/$POSTGRES_VERSION/main/pg_hba.conf for remote access if needed."

log "Testing connection..."
su - postgres -c "psql -d $DB_NAME -c '\\l'" &>/dev/null && log "Test successful."
