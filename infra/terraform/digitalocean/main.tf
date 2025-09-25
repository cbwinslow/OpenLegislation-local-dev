terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
  required_version = ">= 1.0"
}

provider "digitalocean" {
  token = var.do_token  # Set via env DIGITALOCEAN_TOKEN or tfvar
}

# VPC for private networking
resource "digitalocean_vpc" "main" {
  name   = "${var.environment}-openleg-vpc"
  region = var.region
  description = "VPC for OpenLegislation infrastructure"
}

# Firewall
resource "digitalocean_firewall" "app" {
  name = "${var.environment}-app-firewall"

  dynamic "inbound_rule" {
    for_each = var.firewall_rules
    content {
      protocol         = inbound_rule.value.protocol
      port_range       = inbound_rule.value.port_range
      source_addresses = inbound_rule.value.source_addresses
    }
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0"]
  }

  outbound_rule {
    protocol              = "icmp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0"]
  }

  droplet_ids = digitalocean_droplet.app[*].id
}

# Droplets (immutable: Multiple for HA)
resource "digitalocean_droplet" "app" {
  count    = 2
  name     = "${var.environment}-app-${count.index + 1}"
  size     = var.droplet_size
  image    = var.image
  region   = var.region
  vpc_uuid = digitalocean_vpc.main.id
  ssh_keys = var.ssh_keys

  user_data = templatefile("${path.module}/user_data.sh", {
    environment = var.environment
  })

  tags = ["app", var.environment]

  depends_on = [digitalocean_firewall.app]
}

# Load Balancer
resource "digitalocean_loadbalancer" "app" {
  name   = "${var.environment}-app-lb"
  region = var.region
  vpc_uuid = digitalocean_vpc.main.id

  forwarding_rule {
    entry_port     = 80
    entry_protocol = "http"
    target_port    = 8080
    target_protocol = "http"
  }

  health_check {
    port                     = 8080
    protocol                 = "http"
    path                     = "/"
    check_interval_seconds   = 10
    timeout_seconds          = 5
    healthy_threshold        = 2
    unhealthy_threshold      = 3
  }

  droplet_ids = digitalocean_droplet.app[*].id

  tags = [var.environment]
}

# Managed PostgreSQL Database Cluster
resource "digitalocean_database_cluster" "main" {
  name       = "${var.environment}-openleg-db"
  engine     = "pg"
  version    = var.db_engine_version
  size       = var.db_cluster_size
  region     = var.region
  vpc_uuid   = digitalocean_vpc.main.id
  node_count = var.environment == "prod" ? 3 : 1  # HA in prod

  user_details {
    username = var.db_username
    password = var.db_password
  }

  tags = [var.environment]
}

resource "digitalocean_database_firewall" "db" {
  database_cluster_id = digitalocean_database_cluster.main.id

  # Allow from VPC
  rule {
    type  = "vpc"
    value = digitalocean_vpc.main.id
  }

  # Allow from droplets
  dynamic "rule" {
    for_each = digitalocean_droplet.app
    content {
      type  = "droplet"
      value = rule.value.id
    }
  }
}

# Spaces (Object Storage)
resource "digitalocean_spaces_bucket" "data" {
  name   = var.spaces_name
  region = var.spaces_region

  acl = "private"

  tags = [var.environment]
}

# CDN for Spaces (optional)
resource "digitalocean_cdn_endpoint" "spaces_cdn" {
  origin       = digitalocean_spaces_bucket.data.bucket_domain_name
  certificate_id = digitalocean_certificate.main.id  # Assume cert created

  custom_domain {
    hostname = "cdn.${var.zone_name}"  # Integrate with Cloudflare
  }

  tags = [var.environment]
}

# Outputs
output "droplet_ips" {
  value = [for droplet in digitalocean_droplet.app : droplet.ipv4_address]
}

output "load_balancer_ip" {
  value = digitalocean_loadbalancer.app.ip
}

output "db_host" {
  value = digitalocean_database_cluster.main.host
}

output "db_port" {
  value = digitalocean_database_cluster.main.port
}

output "spaces_bucket" {
  value = digitalocean_spaces_bucket.data.name
}

output "vpc_id" {
  value = digitalocean_vpc.main.id
}