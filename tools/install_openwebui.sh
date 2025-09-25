#!/bin/bash

# Script to install and configure OpenWebUI using Docker
# Assumes Ubuntu/Debian Linux environment
# Run as root or with sudo

set -e  # Exit on any error

echo "Installing OpenWebUI via Docker..."

# Update package list
apt update -y

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    apt install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt update -y
    apt install -y docker-ce docker-ce-cli containerd.io
    systemctl start docker
    systemctl enable docker
    usermod -aG docker $USER  # Add user to docker group (relogin needed)
else
    echo "Docker is already installed."
fi

# Install Docker Compose if not present (for easier management, though not strictly needed)
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    apt install -y docker-compose
fi

# Create directory for OpenWebUI data
OPENWEBUI_DIR="/opt/openwebui"
mkdir -p $OPENWEBUI_DIR

# Pull the official OpenWebUI image
echo "Pulling OpenWebUI Docker image..."
docker pull ghcr.io/open-webui/open-webui:main

# Run the container
echo "Starting OpenWebUI container..."
docker run -d \
    --name openwebui \
    -p 3000:8080 \
    -v $OPENWEBUI_DIR:/app/backend/data \
    --restart always \
    -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
    --add-host=host.docker.internal:host-gateway \
    ghcr.io/open-webui/open-webui:main

# Wait for container to start
sleep 10

# Check if running
if docker ps | grep -q openwebui; then
    echo "OpenWebUI installed and running successfully!"
    echo "Access it at http://localhost:3000"
    echo "Data persisted in $OPENWEBUI_DIR"
    echo "Note: Ensure Ollama is running on port 11434 if integrating with it."
else
    echo "Failed to start OpenWebUI. Check logs with: docker logs openwebui"
    exit 1
fi

echo "Installation complete. To stop: docker stop openwebui"
echo "To remove: docker rm openwebui"