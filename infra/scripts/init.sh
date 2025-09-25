#!/bin/bash

# Bootstrap script for multi-cloud infrastructure
# Installs Terraform, Pulumi, and configures providers auth
# Usage: ./init.sh [--dry-run]
# Env vars: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, DIGITALOCEAN_TOKEN, HETZNER_TOKEN, CLOUDFLARE_API_TOKEN, GOOGLE_CREDENTIALS (JSON path)

set -e  # Exit on error

DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
  DRY_RUN=true
  echo "Dry-run mode: Simulating installations/configs"
fi

echo "=== Multi-Cloud Bootstrap: OpenLegislation ==="
echo "Environment: ${ENVIRONMENT:-dev}"
echo "OS: $(uname -a)"

# Check prerequisites
command -v curl >/dev/null 2>&1 || { echo "curl required"; exit 1; }
command -v unzip >/dev/null 2>&1 || { echo "unzip required"; exit 1; }

# 1. Install Terraform
if ! command -v terraform &> /dev/null; then
  echo "Installing Terraform..."
  if [ "$DRY_RUN" = false ]; then
    curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
    sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
    sudo apt update
    sudo apt install terraform
  fi
else
  echo "Terraform already installed: $(terraform --version)"
fi

# 2. Install Pulumi
if ! command -v pulumi &> /dev/null; then
  echo "Installing Pulumi..."
  if [ "$DRY_RUN" = false ]; then
    curl -fsSL https://get.pulumi.com/ | bash
    export PATH=$PATH:$HOME/.pulumi/bin
    echo 'export PATH=$PATH:$HOME/.pulumi/bin' >> ~/.bashrc
  fi
else
  echo "Pulumi already installed: $(pulumi version)"
fi

# 3. AWS Auth
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
  echo "Warning: AWS credentials not set (AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY)"
else
  if [ "$DRY_RUN" = false ]; then
    aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
    aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
    aws configure set default.region us-east-1
  fi
  echo "AWS configured"
fi

# 4. DigitalOcean Auth
if [ -z "$DIGITALOCEAN_TOKEN" ]; then
  echo "Warning: Set DIGITALOCEAN_TOKEN for DO"
else
  echo "DO token set (env var)"
fi

# 5. Hetzner Auth
if [ -z "$HETZNER_TOKEN" ]; then
  echo "Warning: Set HETZNER_TOKEN for Hetzner"
else
  echo "Hetzner token set (env var)"
fi

# 6. Cloudflare Auth
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
  echo "Warning: Set CLOUDFLARE_API_TOKEN for CF"
else
  echo "CF token set (env var)"
fi

# 7. GCP Auth
if [ -z "$GOOGLE_CREDENTIALS" ]; then
  echo "Warning: Set GOOGLE_CREDENTIALS (JSON path) for GCP"
else
  if [ "$DRY_RUN" = false ]; then
    gcloud auth activate-service-account --key-file=$GOOGLE_CREDENTIALS
    gcloud config set project your-gcp-project  # Set project
  fi
  echo "GCP configured"
fi

# 8. Init Terraform dirs
for dir in aws hetzner cloudflare digitalocean; do
  if [ -d "terraform/$dir" ]; then
    echo "Terraform init for $dir..."
    if [ "$DRY_RUN" = false ]; then
      cd infra/terraform/$dir
      terraform init
      cd -
    fi
  fi
done

# 9. Init Pulumi
if [ -d "pulumi" ]; then
  echo "Pulumi init..."
  if [ "$DRY_RUN" = false ]; then
    cd infra/pulumi
    pulumi login  # If using Pulumi Service
    pulumi stack init $STACK
    cd -
  fi
else
  echo "Pulumi dir not found; skip"
fi

# Validation
echo "=== Validation ==="
if command -v terraform &> /dev/null; then
  echo "✓ Terraform OK"
else
  echo "✗ Terraform missing"
  exit 1
fi

if command -v pulumi &> /dev/null; then
  echo "✓ Pulumi OK"
else
  echo "✗ Pulumi missing"
  exit 1
fi

# Check AWS
if aws sts get-caller-identity >/dev/null 2>&1; then
  echo "✓ AWS auth OK"
else
  echo "✗ AWS auth failed"
fi

echo "Bootstrap complete. Run ./apply.sh to deploy."