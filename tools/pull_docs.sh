#!/bin/bash

# Script to pull official documentation as Markdown for specified tools
# Saves to ~/KnowledgeBase/{tool_name}/
# Uses git clone of official docs repos
# Run as regular user (expands ~ to /home/cbwinslow)
# Assumes Ubuntu/Debian; installs git if needed

set -e  # Exit on error

KB_BASE="$HOME/KnowledgeBase"
TOOLS=(
    "OpenWebUI:https://github.com/open-webui/docs.git"
    "Sentry:https://github.com/getsentry/sentry-docs.git"
    "GitLab:https://gitlab.com/gitlab-org/gitlab-docs.git"
    "Grafana:https://github.com/grafana/website.git"  # Docs in src/content/docs/grafana
    "Loki:https://github.com/grafana/loki.git"  # Docs in docs/sources
    "OpenSearch:https://github.com/opensearch-project/documentation-website.git"
    "Netdata:https://github.com/netdata/netdata.git"  # Docs in docs/
    "Prometheus:https://github.com/prometheus/prometheus.git"  # Docs in documentation/
)

echo "Pulling documentation to $KB_BASE..."

# Install git if not present (requires sudo)
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    sudo apt update -y
    sudo apt install -y git
fi

# Install pandoc if needed for any conversions (optional, but repos are MD)
if ! command -v pandoc &> /dev/null; then
    echo "Installing pandoc..."
    sudo apt install -y pandoc
fi

# Create base directory
mkdir -p "$KB_BASE"

cd "$KB_BASE"

for tool_info in "${TOOLS[@]}"; do
    tool=$(echo "$tool_info" | cut -d: -f1)
    repo=$(echo "$tool_info" | cut -d: -f2)
    
    echo "Cloning docs for $tool from $repo..."
    subdir="$KB_BASE/$tool"
    mkdir -p "$subdir"
    cd "$subdir"
    
    if [ -d ".git" ]; then
        echo "$tool docs already cloned. Pulling latest..."
        git pull origin main  # Assume main branch
    else
        git clone "$repo" .
    fi
    
    cd "$KB_BASE"
    
    echo "Docs for $tool saved in $subdir"
    echo "Note: Check README or specific subdirs (e.g., docs/, sources/) for Markdown files."
done

echo "All documentation pulled successfully!"
echo "You can now vectorize the Markdown files in ~/KnowledgeBase/ subfolders."
echo "For GitLab (Git repo): git clone https://gitlab.com/gitlab-org/gitlab-docs.git"
echo "For others, adjust branch if needed (e.g., git checkout stable)."