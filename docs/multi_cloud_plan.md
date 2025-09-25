# Multi-Cloud Infrastructure Plan for OpenLegislation

## Overview
This plan outlines provisioning across multiple clouds for high availability, cost efficiency, and specialized features. Focus: Deploy app (Java backend, ingestion scripts), DB (PostgreSQL for bills/members), storage (bulk data), monitoring, CI/CD. Use Terraform for IaC per provider, Pulumi for cross-cloud orchestration. Environments: dev/prod (via workspaces/tfvars).

**Principles**:
- Immutable deployments (e.g., ASGs, blue-green).
- Secrets: Managed (AWS SSM, DO Secrets, etc.); no hard-code.
- Monitoring: Integrate Prometheus/Grafana (from prior stack).
- CI/CD: GitHub Actions to trigger Pulumi/TF applies.
- Rollback: TF state versioning, Pulumi stacks snapshots.
- Costs: Optimize (spot instances, reserved); estimate dev: $50/mo, prod: $200/mo.

## Platforms and Assets
### 1. Cloudflare (DNS/CDN/Edge)
- **Why**: Global CDN for static assets (docs/bills PDFs), DNS management, Workers for API edge (e.g., rate limiting), Zero Trust for secure access.
- **Assets**:
  - DNS Zone: Custom domain (e.g., openlegislation.com).
  - CDN: Cache rules for /api, /docs.
  - Workers: Script for auth/routing to backends.
  - Pages: Host static frontend if needed.
  - Access: Zero Trust tunnels to private backends.
- **Provider**: Free tier for basics; $20/mo pro.
- **TF Module**: cloudflare.tf (zones, records, workers via JS upload).

### 2. AWS (Core Compute/DB/Storage)
- **Why**: Mature ecosystem, scalable, integrates with monitoring/secrets.
- **Assets**:
  - VPC: Isolated network (subnets AZs).
  - EC2: t3.medium instances for app/ingestion (ASG for HA), user-data for Docker setup.
  - RDS: PostgreSQL multi-AZ, backups, IAM auth.
  - S3: Buckets for bulk XML/JSON (bills/members), lifecycle policies.
  - IAM: Roles for EC2 (S3 access), Secrets Manager for DB/API keys.
  - EKS: If containerized (optional, for OpenLegislation jars).
  - CloudWatch: Alarms, logs integration.
- **Provider**: Pay-as-you-go; est. $100/mo (EC2+RDS+S3).
- **TF Module**: aws/main.tf (vpc, ec2, rds, s3, iam).

### 3. DigitalOcean (Simple VMs/DB)
- **Why**: Easy droplets, managed DB, cost-effective for dev/staging.
- **Assets**:
  - Droplets: Basic VMs (4GB RAM) for secondary app nodes or ingestion workers.
  - Managed DB: PostgreSQL cluster (HA, backups).
  - Spaces: Object storage for media/assets (CDN integration).
  - VPC: Private networking.
  - App Platform: Deploy static sites or containers.
  - Firewalls: Basic rules.
- **Provider**: $5/droplet, $15/DB; est. $30/mo.
- **TF Module**: digitalocean.tf (droplets, db, spaces).

### 4. Hetzner (Cost-Effective VPS/Storage)
- **Why**: Cheap European hosting, good for data-intensive (ingestion), low latency for US/EU.
- **Assets**:
  - Cloud Servers: CX22 (4vCPU/8GB) for app/DB.
  - Volumes: Attached storage for Postgres data dirs.
  - Networks: Private LAN, floating IPs.
  - Firewall: Inbound rules (SSH, HTTP, PG).
  - Load Balancer: For HA across servers.
- **Provider**: €0.01/hr/server; est. $20/mo.
- **TF Module**: hetznercloud.tf (servers, volumes, firewall).

### 5. GCP (AI/ML Focus)
- **Why**: Strong AI tools for legislation analysis (e.g., bill summarization with Gemini).
- **Assets**:
  - Compute Engine: e2-medium for ML workers.
  - Cloud SQL: PostgreSQL for read replicas.
  - Cloud Storage: Buckets for datasets/models.
  - Vertex AI: Endpoints for LLM inference on ingested data.
  - Artifact Registry: Container images.
  - Secret Manager: API keys.
- **Provider**: $0.02/hr VM; est. $40/mo with AI.
- **TF Module**: google.tf (compute, sql, storage, vertex).

## Architecture
- **App**: Deploy JAR to EC2/Droplet/Hetzner (Docker for ingestion scripts); load balance via Cloudflare.
- **DB**: Primary RDS (AWS), replica Cloud SQL (GCP); sync via logical replication.
- **Storage**: S3/Spaces primary, Cloud Storage for ML data.
- **Edge**: Cloudflare Workers route /api to AWS, /ml to GCP.
- **Monitoring**: Prometheus scrapes all (exporters on VMs), Grafana dashboard.
- **CI/CD**: GitHub Actions: On push, Pulumi up (orchestrates TF), test deploy.
- **Security**: TLS (Cloudflare), IAM least-priv, VPN (Tailscale integration), secrets rotation.

## Tools Setup
- **Terraform**: v1.5+; modules in infra/terraform/{provider}/.
- **Pulumi**: Python SDK; stacks in infra/pulumi/ (e.g., dev.py: deploy all).
- **Auth**: AWS CLI, DO token, Hetzner API key, GCP service account, CF API token (env vars).
- **State**: Remote backends (S3 for TF, Pulumi Service).

## Deployment Scripts
- `infra/bootstrap.sh`: Install TF/Pulumi, auth providers.
- `infra/deploy.sh`: TF init/plan/apply per provider; Pulumi up for orchestration.
- `infra/rollback.sh`: TF destroy, Pulumi destroy.
- Vars: terraform.tfvars (env-specific: dev/prod).

## Costs & Optimization
- Dev: ~$150/mo total (scale down).
- Prod: ~$500/mo (HA, traffic).
- Optimize: Spot instances (AWS/Hetzner), reserved (DO), free tiers (CF).

## Next Steps
- Create provider configs (start with AWS).
- Delegate secrets to Security Reviewer mode if needed.
- Test dry-runs.

See infra/ for code.