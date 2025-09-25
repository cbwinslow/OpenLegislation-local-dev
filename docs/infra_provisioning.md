# Multi-Cloud Infrastructure Provisioning Guide

This guide details setup, deployment, and management of OpenLegislation's multi-cloud infrastructure using Terraform and Pulumi. Covers AWS, Hetzner, Cloudflare, DigitalOcean (GCP in Pulumi). Focus: Secure, immutable, monitored deploys.

## Setup
### Prerequisites
- Linux/macOS (tested Ubuntu).
- Git, curl, unzip.
- Accounts/API keys:
  - AWS: Access Key/Secret (IAM user with Admin; restrict in prod).
  - DigitalOcean: Personal Access Token (API > Tokens).
  - Hetzner: API Token (Cloud Console > API Tokens).
  - Cloudflare: API Token (with Zone:DNS:Edit, Workers:Edit).
  - GCP: Service Account JSON (with Compute, SQL, Storage roles).
  - Pulumi: Account (pulumi.com; free for basics).
- Env vars: Set in ~/.bashrc or .env:
  ```
  export AWS_ACCESS_KEY_ID=...
  export AWS_SECRET_ACCESS_KEY=...
  export DIGITALOCEAN_TOKEN=...
  export HETZNER_TOKEN=...
  export CLOUDFLARE_API_TOKEN=...
  export GOOGLE_CREDENTIALS=/path/to/key.json
  export ENVIRONMENT=dev  # or prod
  export TF_VAR_db_password=SecurePass123!  # For RDS/DO DB
  ```
- Install: Run `infra/scripts/init.sh` (installs TF/Pulumi, configs auth).

### Directory Structure
- `infra/terraform/{aws,hetzner,cloudflare,digitalocean}/`: Provider modules (main.tf, variables.tf).
- `infra/pulumi/`: Python stacks (__main__.py for orchestration).
- `infra/scripts/`: init.sh (bootstrap), apply.sh (deploy), rollback.sh (destroy).
- tfvars: `infra/terraform/terraform.tfvars.dev` (customize: instance_type=t3.micro, etc.).

### Costs Estimate
- **Dev**: $50-100/mo (micro instances, low traffic).
  - AWS: $20 (EC2 t3.micro + RDS micro + S3 5GB).
  - DO: $15 (droplet + DB).
  - Hetzner: $10 (2x CX22 servers).
  - CF: Free (DNS/Pages basic).
  - GCP: $10 (e2-micro + storage).
- **Prod**: $200-500/mo (scale: multi-AZ, LB, traffic).
- Monitoring: Add $20 (CloudWatch/Prom).
- Optimization: Spot/reserved instances, auto-scale.

## Deployment Steps
1. **Bootstrap**:
   ```
   cd infra/scripts
   chmod +x *.sh
   ./init.sh  # Installs TF/Pulumi, auth checks
   ```

2. **Configure Vars**:
   - Edit `infra/terraform/terraform.tfvars.dev`:
     ```
     environment = "dev"
     vpc_cidr = "10.0.0.0/16"
     instance_type = "t3.micro"
     db_password = "SecurePass123!"  # Or use SSM
     zone_name = "openlegislation.com"
     # Provider-specific
     ```
   - For prod: Copy to .tfvars.prod, scale up (e.g., t3.small, multi-AZ=true).

3. **Dry-Run/Plan**:
   ```
   ./apply.sh --dry-run --env dev --provider all
   ```
   - TF: Plans each provider.
   - Pulumi: Previews stack.

4. **Apply/Deploy**:
   ```
   ./apply.sh --env dev --provider all  # Interactive confirm
   ```
   - Order: TF providers first (base infra), then Pulumi (orchestrates app/monitoring).
   - Pulumi integrates outputs (e.g., AWS ALB IP to CF DNS).
   - Time: 5-10 min dev.
   - Outputs: Endpoints (e.g., LB IP, DB host) in TF/Pulumi console.

5. **Post-Deploy**:
   - SSH to instances: `ssh -i key.pem ubuntu@IP` (user_data installs Docker/app).
   - Verify: `curl http://LB-IP:8080` (app health).
   - Monitoring: Access Grafana (Pulumi deploys ECS service); add datasources for AWS/DO metrics.
   - CI/CD: .github/workflows/deploy.yml (on push: pulumi up).

6. **Rollback**:
   ```
   ./rollback.sh --force --env dev --provider all
   ```
   - Destroys Pulumi, then TF (reverse order).
   - Data: S3/Spaces manual purge if needed.
   - State: TF backend S3 (configure in backend.tf), Pulumi snapshots.

## Best Practices
- **Immutable**: Use ASGs/LB (AWS/DO/Hetzner); no in-place updates.
- **Secrets**: TF vars sensitive=true; Pulumi config set --secret. Prod: SSM/Secrets Manager (fetch in user_data).
- **Validation**: Scripts check auth; add pre-apply hooks (e.g., tfsec for security).
- **Monitoring**: Pulumi deploys Prom/Grafana; scrape EC2/Droplet metrics. Alerts: CloudWatch/PagerDuty.
- **CI/CD**: GitHub Actions: Checkout, init, apply on merge to main (secrets in repo).
- **Rollback/Blue-Green**: Pulumi/TF destroy + recreate; CF Workers for zero-downtime.
- **Security**: Least-priv IAM, firewalls (VPC-only DB), TLS (CF proxy), rotate secrets.
- **Costs**: TF outputs cost estimates; use Pulumi Cost API. Tag resources for billing.
- **State Management**: Remote: S3 for TF (with DynamoDB lock), Pulumi Service.
- **Updates**: `terraform apply` for changes; `pulumi up` for orchestration.

## Example tfvars.dev
```
environment = "dev"
db_password = "devpass"
zone_name = "dev.openlegislation.com"
droplet_size = "s-1vcpu-1gb"
server_type = "cx11"
```

For prod: Scale up, multi-AZ, custom domains.

Troubleshoot: Check logs (CloudWatch, DO console), state (tf state list).