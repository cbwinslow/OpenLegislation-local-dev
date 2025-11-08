#!/bin/bash

# CrewAI Environment Setup Script
# ===============================
# This script sets up a Python virtual environment and installs
# all dependencies required for the CrewAI framework and specialized crews.

set -e  # Exit on any error

echo "🚀 Setting up CrewAI Environment for OpenLegislation"
echo "=================================================="

# Check if Python 3.10+ is available
if ! command -v python3.10 &> /dev/null && ! command -v python3.11 &> /dev/null && ! command -v python3.12 &> /dev/null; then
    echo "❌ Error: Python 3.10 or higher is required"
    echo "Please install Python 3.10+ and try again"
    exit 1
fi

# Determine which Python version to use
PYTHON_CMD=""
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
else
    PYTHON_CMD="python3"
fi

echo "✅ Using Python: $($PYTHON_CMD --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
$PYTHON_CMD -m venv crewai_env

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source crewai_env/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Install additional MCP server dependencies
echo "🔌 Installing MCP server dependencies..."
pip install mcp-server-github mcp-server-filesystem mcp-server-brave-search mcp-server-sqlite

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env template file..."
    cat > .env << EOF
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# GitHub API Configuration
GITHUB_TOKEN=your_github_token_here

# Brave Search API Configuration
BRAVE_API_KEY=your_brave_api_key_here

# Database Configuration (for OpenLegislation)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=openlegislation
DB_USER=openleg
DB_PASSWORD=your_db_password_here

# Elasticsearch Configuration
ES_HOST=localhost
ES_PORT=9200

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
EOF
    echo "⚠️  Please edit the .env file with your actual API keys and configuration"
else
    echo "✅ .env file already exists"
fi

# Create logs directory
mkdir -p logs

# Test the installation
echo "🧪 Testing CrewAI installation..."
python3 -c "
try:
    import crewai
    import crewai_tools
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    from dotenv import load_dotenv
    print('✅ All CrewAI dependencies installed successfully!')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

echo ""
echo "🎉 CrewAI Environment Setup Complete!"
echo "===================================="
echo ""
echo "To activate the virtual environment:"
echo "  source crewai_env/bin/activate"
echo ""
echo "To run CrewAI crews:"
echo "  python crewai/run_crew.py --help"
echo ""
echo "Available crew types:"
echo "  - development: Software development and engineering"
echo "  - legislative: Legislative analysis and policy assessment"
echo "  - political: Political strategy and campaign management"
echo "  - database: Database administration and optimization"
echo ""
echo "Example usage:"
echo "  python crewai/run_crew.py development --project 'OpenLegislation enhancement'"
echo ""
echo "Don't forget to:"
echo "1. Edit the .env file with your API keys"
echo "2. Activate the virtual environment before running crews"
echo "3. Check the README.md for detailed usage instructions"