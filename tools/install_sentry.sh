#!/bin/bash

# Script to install and configure Sentry self-hosted using Docker (on-premise)
# Assumes Ubuntu/Debian Linux environment
# Run as root or with sudo
# WARNING: For production, generate strong secrets and configure SMTP, etc.
# Edit .env after setup for security

set -e  # Exit on any error

echo "Installing Sentry self-hosted via Docker..."

# Update package list
apt update -y

# Install prerequisites: Docker, git
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    apt install -y apt-transport-https ca-certificates curl software-properties-common git
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt update -y
    apt install -y docker-ce docker-ce-cli containerd.io
    systemctl start docker
    systemctl enable docker
    usermod -aG docker $USER
else
    echo "Docker is already installed."
    apt install -y git  # Ensure git is there
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    apt install -y docker-compose
fi

# Create directory for Sentry
SENTRY_DIR="/opt/sentry"
mkdir -p $SENTRY_DIR
cd $SENTRY_DIR

# Clone the official onpremise repo if not exists
if [ ! -d "onpremise" ]; then
    echo "Cloning Sentry onpremise repository..."
    git clone https://github.com/getsentry/onpremise.git
fi
cd onpremise

# Create .env file with basic config (user must edit for production)
if [ ! -f ".env" ]; then
    echo "Creating .env configuration file..."
    cat > .env << 'EOF'
# System Settings
SYSTEM_URL=http://localhost
SENTRY_SECRET_KEY=!!REPLACE_WITH_STRONG_SECRET_KEY!!  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(50))"
SENTRY_POSTGRES_HOST=sentry-postgres
SENTRY_POSTGRES_PASSWORD=!!REPLACE_WITH_STRONG_PASSWORD!!
SENTRY_REDIS_HOST=sentry-redis
SENTRY_REDIS_PASSWORD=!!REPLACE_WITH_STRONG_PASSWORD!!

# Email (configure for alerts)
MAIL_HOST=localhost
MAIL_PORT=1025
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=sentry@localhost

# Allow registrations (set to False for production)
SENTRY_ALLOW_REGISTRATION=True

# Filestore (local for dev)
SENTRY_FILESTORE=local
SENTRY_DEFAULT_BUCKET=sentry

# Snuba (for search/indexing)
SNUBA_SETTINGS=production

# Webpack (for assets)
SENTRY_USE_RELOADER=False
EOF
    echo "Basic .env created. EDIT IT before running: Set strong passwords and secret key."
    echo "Generate secret key: docker run --rm sentry python -c 'import secrets; print(secrets.token_urlsafe(50))'"
fi

# Start the stack
echo "Starting Sentry with Docker Compose..."
docker-compose up -d

# Wait for services to start (basic health check)
sleep 60

# Check if key services are running
if docker-compose ps | grep -q Up; then
    echo "Sentry installed and starting..."
    echo "Access initial setup at http://localhost (create superuser via /setup/ after services ready)"
    echo "Check logs: docker-compose logs -f"
    echo "Data persisted in $SENTRY_DIR/onpremise"
    echo "For production: Configure HTTPS, SMTP, backups, and scale as needed."
else
    echo "Failed to start Sentry. Check logs with: cd $SENTRY_DIR/onpremise && docker-compose logs"
    exit 1
fi

echo "Installation complete."
echo "To stop: cd $SENTRY_DIR/onpremise && docker-compose down"
echo "To update: cd $SENTRY_DIR/onpremise && git pull && docker-compose pull && docker-compose up -d"
