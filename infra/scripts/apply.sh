#!/bin/bash

# Deployment script for multi-cloud infrastructure
# Usage: ./apply.sh [--dry-run] [--env dev|prod] [--provider all|aws|hetzner|cf|do]
# Env vars: Same as init.sh + TF_VAR_db_password etc. for secrets

set -e  # Exit on error

DRY_RUN=false
ENV="dev"
PROVIDER="all"

while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --env)
      ENV="$2"
      shift 2
      ;;
    --provider)
      PROVIDER="$2"
      shift 2
      ;;
    *)
      echo "Unknown option $1"
      exit 1
      ;;
  esac
done

echo "=== Multi-Cloud Deploy: OpenLegislation ==="
echo "Environment: $ENV"
echo "Provider: $PROVIDER"
echo "Dry-run: $DRY_RUN"

# Load env-specific vars (assume terraform.tfvars.$ENV)
if [ -f "infra/terraform/terraform.tfvars.$ENV" ]; then
  export $(grep -v '^#' infra/terraform/terraform.tfvars.$ENV | xargs)
fi

# Validation
if [ "$PROVIDER" = "all" ] || [[ $PROVIDER == *"aws"* ]]; then
  if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "AWS auth invalid"
    exit 1
  fi
fi

# Terraform Apply per provider
providers=()
if [ "$PROVIDER" = "all" ] || [ "$PROVIDER" = "aws" ]; then providers+=("aws"); fi
if [ "$PROVIDER" = "all" ] || [ "$PROVIDER" = "hetzner" ]; then providers+=("hetzner"); fi
if [ "$PROVIDER" = "all" ] || [ "$PROVIDER" = "cf" ]; then providers+=("cloudflare"); fi
if [ "$PROVIDER" = "all" ] || [ "$PROVIDER" = "do" ]; then providers+=("digitalocean"); fi

for prov in "${providers[@]}"; do
  echo "=== Deploying $prov ($ENV) ==="
  cd "infra/terraform/$prov"
  if [ "$DRY_RUN" = true ]; then
    terraform plan -var="environment=$ENV" -var-file="../terraform.tfvars.$ENV"
  else
    terraform init
    terraform plan -var="environment=$ENV" -var-file="../terraform.tfvars.$ENV"
    read -p "Apply $prov? (y/N): " confirm
    if [[ $confirm == [yY] ]]; then
      terraform apply -auto-approve -var="environment=$ENV" -var-file="../terraform.tfvars.$ENV"
    fi
  fi
  cd -
done

# Pulumi Up (orchestration)
echo "=== Pulumi Deploy ($ENV) ==="
cd infra/pulumi
if [ "$DRY_RUN" = true ]; then
  pulumi preview --stack "$ENV"
else
  pulumi up --stack "$ENV" --yes
fi
cd -

echo "Deploy complete. Check outputs for endpoints."
echo "Rollback: ./rollback.sh --provider $PROVIDER"