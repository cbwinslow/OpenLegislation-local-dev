#!/bin/bash

# OpenLegislation Automation Setup Script
# This script sets up the complete automation stack including n8n, Flowise, Graphite, and Agentic Knowledge Graph

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env.automation"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.automation.yml"

# Default configuration values
DEFAULT_POSTGRES_PASSWORD="secure_postgres_password_change_me"
DEFAULT_N8N_PASSWORD="secure_n8n_password_change_me"
DEFAULT_FLOWISE_PASSWORD="secure_flowise_password_change_me"
DEFAULT_GRAPHITE_SECRET="change_me_to_random_string"
DEFAULT_KG_API_KEY="secure_kg_api_key_change_me"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking system dependencies..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Check if curl is installed
    if ! command -v curl &> /dev/null; then
        log_error "curl is not installed. Please install curl first."
        exit 1
    fi

    log_success "All dependencies are installed"
}

generate_secure_password() {
    # Generate a secure random password
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

setup_environment() {
    log_info "Setting up environment configuration..."

    if [ -f "$ENV_FILE" ]; then
        log_warning "Environment file already exists: $ENV_FILE"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Keeping existing environment file"
            return
        fi
    fi

    # Generate secure passwords
    POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-$(generate_secure_password)}
    N8N_PASSWORD=${N8N_PASSWORD:-$(generate_secure_password)}
    FLOWISE_PASSWORD=${FLOWISE_PASSWORD:-$(generate_secure_password)}
    GRAPHITE_SECRET=${GRAPHITE_SECRET:-$(generate_secure_password)}
    KG_API_KEY=${KG_API_KEY:-$(generate_secure_password)}

    # Create environment file
    cat > "$ENV_FILE" << EOF
# OpenLegislation Automation Environment Configuration
# Generated on $(date)

# PostgreSQL Configuration
POSTGRES_DB=openlegislation
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

# n8n Configuration
N8N_USER=admin
N8N_PASSWORD=$N8N_PASSWORD
N8N_HOST=localhost
N8N_WEBHOOK_URL=http://localhost:5678

# Flowise Configuration
FLOWISE_USER=admin
FLOWISE_PASSWORD=$FLOWISE_PASSWORD

# Graphite Configuration
GRAPHITE_SECRET_KEY=$GRAPHITE_SECRET

# Agentic Knowledge Graph Configuration
AGENTIC_KG_API_KEY=$KG_API_KEY

# GitHub/GitLab Webhook Secrets (generate your own)
GITHUB_WEBHOOK_SECRET=$(generate_secure_password)
GITLAB_WEBHOOK_SECRET=$(generate_secure_password)

# GPU Configuration (set to true if you have GPU support)
GPU_ENABLED=false

# Development/Production Mode
ENVIRONMENT=production
LOG_LEVEL=info

# External API Keys (add your own)
# OPENAI_API_KEY=your_openai_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here
# GROQ_API_KEY=your_groq_key_here
EOF

    log_success "Environment file created: $ENV_FILE"
    log_warning "IMPORTANT: Please save these credentials securely:"
    echo "  PostgreSQL Password: $POSTGRES_PASSWORD"
    echo "  n8n Password: $N8N_PASSWORD"
    echo "  Flowise Password: $FLOWISE_PASSWORD"
    echo "  Agentic KG API Key: $KG_API_KEY"
}

create_directories() {
    log_info "Creating necessary directories..."

    # Create automation directories
    mkdir -p "$PROJECT_ROOT/automation/n8n_workflows"
    mkdir -p "$PROJECT_ROOT/automation/flowise_workflows"
    mkdir -p "$PROJECT_ROOT/automation/graphite_config"
    mkdir -p "$PROJECT_ROOT/automation/database_init"
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/data"

    # Create agentic knowledge graph directory
    mkdir -p "$PROJECT_ROOT/agentic-knowledge-graph/config"
    mkdir -p "$PROJECT_ROOT/agentic-knowledge-graph/data"

    log_success "Directories created"
}

setup_database_init() {
    log_info "Setting up database initialization scripts..."

    # Create automation-specific database initialization
    cat > "$PROJECT_ROOT/automation/database_init/automation_tables.sql" << 'EOF'
-- Automation-specific database tables
-- This file is loaded during Docker container initialization

-- n8n execution logs table (if not using n8n's built-in DB)
CREATE TABLE IF NOT EXISTS automation_executions (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(255) UNIQUE NOT NULL,
    workflow_id VARCHAR(255),
    workflow_name VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Flowise chat history
CREATE TABLE IF NOT EXISTS flowise_chats (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    chat_id VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    response TEXT,
    agent_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Graphite metrics buffer (for offline metrics)
CREATE TABLE IF NOT EXISTS graphite_metrics_buffer (
    id SERIAL PRIMARY KEY,
    metric_path VARCHAR(500) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    timestamp INTEGER NOT NULL,
    sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agentic Knowledge Graph relationships cache
CREATE TABLE IF NOT EXISTS kg_relationships_cache (
    id SERIAL PRIMARY KEY,
    entity1_type VARCHAR(100) NOT NULL,
    entity1_id VARCHAR(255) NOT NULL,
    entity2_type VARCHAR(100) NOT NULL,
    entity2_id VARCHAR(255) NOT NULL,
    relationship_type VARCHAR(100) NOT NULL,
    confidence_score FLOAT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(entity1_type, entity1_id, entity2_type, entity2_id, relationship_type)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_automation_executions_status ON automation_executions(status);
CREATE INDEX IF NOT EXISTS idx_automation_executions_workflow_id ON automation_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_flowise_chats_session_id ON flowise_chats(session_id);
CREATE INDEX IF NOT EXISTS idx_graphite_metrics_buffer_sent ON graphite_metrics_buffer(sent);
CREATE INDEX IF NOT EXISTS idx_kg_relationships_cache_entities ON kg_relationships_cache(entity1_type, entity1_id, entity2_type, entity2_id);

-- Insert default configuration data
INSERT INTO telemetry_config (component, config_key, config_value) VALUES
('automation', 'n8n_webhook_url', 'http://n8n:5678'),
('automation', 'flowise_api_url', 'http://flowise:3000'),
('automation', 'graphite_host', 'graphite'),
('automation', 'graphite_port', '2003'),
('automation', 'agentic_kg_url', 'http://agentic-kg:8000')
ON CONFLICT (component, config_key) DO NOTHING;
EOF

    log_success "Database initialization scripts created"
}

create_dockerfile() {
    log_info "Creating Dockerfile for Agentic Knowledge Graph..."

    cat > "$PROJECT_ROOT/agentic-knowledge-graph/Dockerfile" << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "main.py"]
EOF

    # Create requirements.txt for Agentic KG
    cat > "$PROJECT_ROOT/agentic-knowledge-graph/requirements.txt" << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
asyncpg==0.29.0
redis==5.0.1
python-multipart==0.0.6
aiofiles==23.2.1
httpx==0.25.2
structlog==23.2.0
python-dotenv==1.0.0
networkx==3.2.1
numpy==1.26.2
scikit-learn==1.3.2
sentence-transformers==2.2.2
EOF

    log_success "Dockerfile and requirements created for Agentic Knowledge Graph"
}

create_n8n_workflows() {
    log_info "Creating sample n8n workflows..."

    # Create automated ingestion workflow
    cat > "$PROJECT_ROOT/automation/n8n_workflows/automated_ingestion.json" << 'EOF'
{
  "name": "Automated Legislative Data Ingestion",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "hours",
              "value": 6
            }
          ]
        }
      },
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1,
      "position": [240, 300]
    },
    {
      "parameters": {
        "url": "http://host.docker.internal:8001/queue/status",
        "method": "GET"
      },
      "name": "Check Queue Status",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [460, 300]
    },
    {
      "parameters": {
        "url": "http://host.docker.internal:8001/jobs/submit",
        "method": "POST",
        "body": {
          "job_type": "ingestion",
          "ingestion_type": "congress",
          "parameters": {
            "start_congress": 110,
            "end_congress": 118,
            "enable_gpu": true,
            "enable_parallel": true
          }
        }
      },
      "name": "Submit Ingestion Job",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [680, 300]
    },
    {
      "parameters": {
        "url": "http://host.docker.internal:8001/jobs/{{ $node[\"Submit Ingestion Job\"].json[\"job_id\"] }}/status",
        "method": "GET"
      },
      "name": "Monitor Job Progress",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [900, 300]
    },
    {
      "parameters": {
        "to": "engineering@openlegislation.org",
        "subject": "Ingestion Job Completed",
        "body": "Job {{ $node[\"Submit Ingestion Job\"].json[\"job_id\"] }} completed successfully at {{ new Date().toISOString() }}"
      },
      "name": "Send Notification",
      "type": "@n8n/nodes-base.emailSend",
      "typeVersion": 1,
      "position": [1120, 300]
    }
  ],
  "connections": {
    "Schedule Trigger": {
      "main": [
        [
          {
            "node": "Check Queue Status",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Check Queue Status": {
      "main": [
        [
          {
            "node": "Submit Ingestion Job",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Submit Ingestion Job": {
      "main": [
        [
          {
            "node": "Monitor Job Progress",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Monitor Job Progress": {
      "main": [
        [
          {
            "node": "Send Notification",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
EOF

    log_success "Sample n8n workflows created"
}

start_services() {
    log_info "Starting automation services..."

    cd "$PROJECT_ROOT"

    # Pull images first
    log_info "Pulling Docker images..."
    docker-compose -f "$COMPOSE_FILE" pull

    # Start services
    log_info "Starting services..."
    docker-compose -f "$COMPOSE_FILE" up -d

    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 30

    # Check service health
    check_service_health

    log_success "Automation services started successfully!"
}

check_service_health() {
    log_info "Checking service health..."

    services=(
        "postgres:5432"
        "redis:6379"
        "n8n:5678/healthz"
        "flowise:3000/api/v1/ping"
        "graphite:8080"
        "openlegislation:8000/health"
    )

    for service in "${services[@]}"; do
        service_name=$(echo $service | cut -d: -f1)
        service_url=$(echo $service | cut -d: -f2-)

        if curl -f -s "http://localhost:$service_url" > /dev/null 2>&1; then
            log_success "$service_name is healthy"
        else
            log_warning "$service_name is not yet healthy (this may take a few minutes)"
        fi
    done
}

show_access_info() {
    log_success "🎉 OpenLegislation Automation Stack is ready!"
    echo ""
    echo "Access your services at:"
    echo "  📊 n8n Workflows:     http://localhost:5678"
    echo "  🤖 Flowise AI:        http://localhost:3000"
    echo "  📈 Graphite Metrics:  http://localhost:8080"
    echo "  🧠 Agentic KG:        http://localhost:8000"
    echo "  🚀 OpenLegislation:   http://localhost:8001"
    echo "  🔗 Queue API:         http://localhost:8002"
    echo "  🪝 Webhooks:          http://localhost:9000"
    echo ""
    echo "Database access:"
    echo "  PostgreSQL: localhost:5432 (user: postgres)"
    echo "  Redis: localhost:6379"
    echo ""
    log_warning "Remember to change the default passwords in $ENV_FILE!"
}

main() {
    echo "🚀 OpenLegislation Automation Setup"
    echo "=================================="

    # Check if running as root (not recommended for Docker)
    if [ "$EUID" -eq 0 ]; then
        log_warning "Running as root. Consider using a non-root user for Docker operations."
    fi

    # Run setup steps
    check_dependencies
    setup_environment
    create_directories
    setup_database_init
    create_dockerfile
    create_n8n_workflows

    # Ask user if they want to start services
    echo ""
    read -p "Do you want to start the automation services now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        start_services
        show_access_info
    else
        log_info "Services not started. You can start them later with:"
        echo "  cd $PROJECT_ROOT && docker-compose -f docker-compose.automation.yml up -d"
        echo ""
        show_access_info
    fi

    log_success "Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Review and customize the configuration in $ENV_FILE"
    echo "2. Import workflows into n8n from $PROJECT_ROOT/automation/n8n_workflows/"
    echo "3. Configure AI agents in Flowise"
    echo "4. Set up dashboards in Graphite"
    echo "5. Start the automated ingestion scheduler"
}

# Handle command line arguments
case "${1:-}" in
    "start")
        cd "$PROJECT_ROOT"
        start_services
        show_access_info
        ;;
    "stop")
        cd "$PROJECT_ROOT"
        log_info "Stopping automation services..."
        docker-compose -f "$COMPOSE_FILE" down
        log_success "Services stopped"
        ;;
    "restart")
        cd "$PROJECT_ROOT"
        log_info "Restarting automation services..."
        docker-compose -f "$COMPOSE_FILE" restart
        log_success "Services restarted"
        ;;
    "status")
        cd "$PROJECT_ROOT"
        log_info "Checking service status..."
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
    "logs")
        cd "$PROJECT_ROOT"
        service="${2:-}"
        if [ -n "$service" ]; then
            docker-compose -f "$COMPOSE_FILE" logs -f "$service"
        else
            docker-compose -f "$COMPOSE_FILE" logs -f
        fi
        ;;
    "cleanup")
        cd "$PROJECT_ROOT"
        log_warning "This will remove all containers and volumes. Are you sure?"
        read -p "Type 'yes' to confirm: " -r
        if [[ $REPLY == "yes" ]]; then
            docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans
            log_success "Cleanup completed"
        else
            log_info "Cleanup cancelled"
        fi
        ;;
    "help"|"-h"|"--help")
        echo "OpenLegislation Automation Setup Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  (no command)  Run full setup"
        echo "  start         Start services"
        echo "  stop          Stop services"
        echo "  restart       Restart services"
        echo "  status        Show service status"
        echo "  logs [svc]    Show logs (optionally for specific service)"
        echo "  cleanup       Remove all containers and volumes"
        echo "  help          Show this help"
        ;;
    *)
        main "$@"
        ;;
esac
