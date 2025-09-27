#!/bin/bash

# Simulation/test script for infrastructure deployment
# Runs dry-runs (TF plan, Pulumi preview) without applying
# Usage: ./test_deploy.sh [--env dev|prod] [--provider all|aws|hetzner|cf|do]

set -e

ENV="dev"
PROVIDER="all"

while [[ $# -gt 0 ]]; do
  case $1 in
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

echo "=== Infrastructure Dry-Run Test: OpenLegislation ($ENV) ==="
echo "Provider: $PROVIDER"

# Load vars
if [ -f "infra/terraform/terraform.tfvars.$ENV" ]; then
  export $(grep -v '^#' infra/terraform/terraform.tfvars.$ENV | xargs)
fi

# Terraform Plans
providers=()
if [ "$PROVIDER" = "all" ] || [ "$PROVIDER" = "aws" ]; then providers+=("aws"); fi
if [ "$PROVIDER" = "all" ] || [ "$PROVIDER" = "hetzner" ]; then providers+=("hetzner"); fi
if [ "$PROVIDER" = "all" ] || [ "$PROVIDER" = "cf" ]; then providers+=("cloudflare"); fi
if [ "$PROVIDER" = "all" ] || [ "$PROVIDER" = "do" ]; then providers+=("digitalocean"); fi

for prov in "${providers[@]}"; do
  echo "=== Terraform Plan: $prov ($ENV) ==="
  cd "infra/terraform/$prov"
  terraform init
  terraform plan -var="environment=$ENV" -var-file="../terraform.tfvars.$ENV" -out="plan-$ENV.tfplan"
  terraform show -json plan-$ENV.tfplan > "plan-$ENV-$prov.json"  # For validation
  rm plan-$ENV.tfplan
  cd -
  echo "✓ $prov plan complete (check plan-$ENV-$prov.json for resources)"
done

# Pulumi Preview
echo "=== Pulumi Preview ($ENV) ==="
cd infra/pulumi
pulumi preview --stack "$ENV" --out preview-$ENV.json
cd -
echo "✓ Pulumi preview complete (check preview-$ENV.json)"

# Validation Summary
echo "=== Test Summary ==="
echo "All dry-runs succeeded. No resources created."
echo "Next: Review plans, then ./apply.sh --env $ENV"
echo "Costs: Use plan JSON with tools like tf-cost-estimate or Pulumi Cost."
