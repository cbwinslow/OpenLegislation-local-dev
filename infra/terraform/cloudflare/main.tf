terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
  required_version = ">= 1.0"
}

provider "cloudflare" {
  account_id = var.account_id
  api_token  = var.api_token
}

# DNS Zone
resource "cloudflare_zone" "main" {
  zone = var.zone_name
  type = "full"  # Assume domain is added to Cloudflare

  tags = {
    Environment = var.environment
  }
}

# DNS Records (dynamic from var)
resource "cloudflare_record" "dns" {
  for_each = { for record in var.dns_records : "${record.name}.${var.zone_name}" => record }

  zone_id = cloudflare_zone.main.id
  name    = each.value.name
  value   = each.value.value
  type    = each.value.type
  proxied = each.value.proxied
  ttl     = 1  # Auto TTL

  tags = {
    Environment = var.environment
  }
}

# Cloudflare Pages (for static frontend/docs)
resource "cloudflare_pages_project" "main" {
  account_id = var.account_id
  name       = var.pages_project_name
  production_branch = "main"

  build_config {
    build_command  = "npm run build"  # Assume static site build
    output_directory = "dist"  # Or build output dir
  }

  source {
    type = "git"
    config {
      git_username = "github-actions"  # For CI deploy
      repo_name    = "openlegislation/openlegislation"  # Repo
      branch       = "main"
    }
  }

  tags = {
    Environment = var.environment
  }
}

# Deployment for Pages (manual or via CI; here assume local dir for TF)
resource "cloudflare_pages_deployment" "main" {
  account_id = var.account_id
  project_name = cloudflare_pages_project.main.name

  # For TF, upload from local; in prod use CI
  # Note: This is for initial; use API in CI for updates
  # For simplicity, assume pre-built; in practice, use null_resource with local-exec
  depends_on = [cloudflare_pages_project.main]
}

# Cloudflare Worker for edge API (e.g., auth/rate limit)
resource "cloudflare_worker_script" "api_worker" {
  name    = var.worker_name
  content = file("${path.module}/${var.worker_script}")
}

resource "cloudflare_worker_route" "api" {
  zone_id = cloudflare_zone.main.id
  pattern = "api.*.${var.zone_name}/*"
  script_name = cloudflare_worker_script.api_worker.name
}

# Outputs
output "zone_id" {
  value = cloudflare_zone.main.id
}

output "pages_url" {
  value = cloudflare_pages_project.main.url
}

output "worker_name" {
  value = cloudflare_worker_script.api_worker.name
}

output "dns_records" {
  value = cloudflare_record.dns
}