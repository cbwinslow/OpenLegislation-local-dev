#!/bin/bash
# Quick deployment script for webhook server

set -e

echo "🚀 OpenLegislation Webhook Server Deployment"
echo "============================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Please do not run as root. Run as regular user with sudo access."
    exit 1
fi

# Check dependencies
echo "📦 Checking dependencies..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Installing..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "✅ Docker installed. Please log out and back in for group changes to take effect."
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Installing..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose installed."
fi

echo "✅ All dependencies installed"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Edit .env file with your credentials before starting the server!"
    echo ""
    echo "Required configuration:"
    echo "  - GITHUB_TOKEN: Get from https://github.com/settings/tokens"
    echo "  - GITHUB_WEBHOOK_SECRET: Generate with: openssl rand -hex 32"
    echo "  - OPENROUTER_API_KEY: Get from https://openrouter.ai/keys"
    echo ""
    read -p "Press Enter to edit .env now, or Ctrl+C to exit and edit manually..."
    ${EDITOR:-nano} .env
fi

echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting webhook server..."
docker-compose up -d

echo ""
echo "✅ Webhook server is running!"
echo ""
echo "📊 Check status:"
echo "  docker-compose ps"
echo ""
echo "📋 View logs:"
echo "  docker-compose logs -f"
echo ""
echo "🏥 Health check:"
echo "  curl http://localhost:5000/health"
echo ""
echo "⚙️  Next steps:"
echo "  1. Configure GitHub webhook in your repository settings"
echo "  2. Set webhook URL to: https://your-domain.com:5000/webhook"
echo "  3. Set content type to: application/json"
echo "  4. Set secret to the value of GITHUB_WEBHOOK_SECRET in your .env"
echo "  5. Select 'Pull requests' events"
echo ""
echo "📖 For detailed setup instructions, see README.md"
echo ""
