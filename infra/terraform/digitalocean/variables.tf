variable "environment" {
  description = "Environment name (dev/prod)"
  type        = string
  default     = "dev"
}

variable "droplet_size" {
  description = "Droplet size slug (e.g., s-1vcpu-2gb)"
  type        = string
  default     = "s-1vcpu-2gb"
}

variable "region" {
  description = "DigitalOcean region (e.g., nyc3)"
  type        = string
  default     = "nyc3"
}

variable "image" {
  description = "Droplet image (e.g., ubuntu-22-04-x64)"
  type        = string
  default     = "ubuntu-22-04-x64"
}

variable "ssh_keys" {
  description = "List of SSH key fingerprints or IDs"
  type        = list(string)
  default     = []
}

variable "db_cluster_size" {
  description = "Managed DB cluster node size (e.g., db-s-1vcpu-1gb)"
  type        = string
  default     = "db-s-1vcpu-1gb"
}

variable "db_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15"
}

variable "db_username" {
  description = "DB master username"
  type        = string
  default     = "admin"
}

variable "db_password" {
  description = "DB master password (sensitive)"
  type        = string
  sensitive   = true
}

variable "spaces_name" {
  description = "Spaces bucket name"
  type        = string
  default     = "openlegislation-spaces-${var.environment}"
}

variable "spaces_region" {
  description = "Spaces region"
  type        = string
  default     = "nyc3"
}

variable "vpc_name" {
  description = "VPC name for private networking"
  type        = string
  default     = "openleg-vpc"
}

variable "firewall_rules" {
  description = "List of firewall rules for droplets"
  type = list(object({
    protocol    = string
    port_range  = string
    source_addresses = list(string)
  }))
  default = [
    {
      protocol        = "tcp"
      port_range      = "22"
      source_addresses = ["0.0.0.0/0"]
    },
    {
      protocol        = "tcp"
      port_range      = "8080"
      source_addresses = ["0.0.0.0/0"]
    },
    {
      protocol        = "tcp"
      port_range      = "5432"
      source_addresses = ["10.0.0.0/16"]  # VPC CIDR
    }
  ]
}