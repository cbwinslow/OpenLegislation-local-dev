#!/bin/bash

# Rollback script for multi-cloud infrastructure
# Destroys resources in reverse order (Pulumi then TF providers)
# Usage: ./rollback.sh [--force] [--env dev|prod] [--provider all|aws|hetzner|cf|do]
# WARNING: This destroys resources; backup data first!

set -e  # Exit on error

FORCE=false
ENV="dev"
PROVIDER="all"

while [[ $# -gt 0 ]]; do
  case $1 in
    --force)
      FORCE=true
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

if [ "$FORCE" = false ]; then
  read -p "Confirm rollback for $ENV ($PROVIDER)? This destroys resources! (y/N): " confirm
  if [[ $confirm != [yY] ]]; then
    echo "Aborted."
    exit 0
  fi
fi

echo "=== Multi-Cloud Rollback: OpenLegislation ($ENV) ==="
echo "Provider: $PROVIDER"

# Load env vars
if [ -f "infra/terraform/terraform.tfvars.$ENV" ]; then
  export $(grep -v '^#' infra/terraform/terraform.tfvars.$ENV | xargs)
fi

# Pulumi Destroy first (orchestration)
echo "=== Pulumi Destroy ($ENV) ==="
cd infra/pulumi
pulumi destroy --stack "$ENV" --yes
cd -

# Terraform Destroy per provider (reverse order: DO, CF, Hetzner, AWS)
providers=()
if [ "$PROVIDER" = "all" ] || [ "$PROVIDER" = "do" ]; then providers=("digitalocean" "$providers[@]"); fi
if [ "$PROVIDER" = "all" ] || [ "$PROVIDER" = "cf" ]; then providers=("cloudflare" "$providers[@]"); fi
if [ "$PROVIDER" = "all" ] || [ "$PROVIDER" = "hetzner" ]; then providers=("hetzner" "$providers[@]"); fi
if [ "$PROVIDER" = "all" ] || [ "$PROVIDER" = "aws" ]; then providers=("aws" "$providers[@]"); fi

for prov in "${providers[@]}"; do
  echo "=== Destroying $prov ($ENV) ==="
  cd "infra/terraform/$prov"
  terraform init
  terraform plan -destroy -var="environment=$ENV" -var-file="../terraform.tfvars.$ENV"
  terraform destroy -auto-approve -var="environment=$ENV" -var-file="../terraform.tfvars.$ENV"
  cd -
done

# Cleanup state if needed (manual: rm -rf .terraform/ etc.)
echo "Rollback complete. Verify no resources remain (e.g., AWS console)."
echo "Data backups: Ensure S3/Spaces purged if needed."
