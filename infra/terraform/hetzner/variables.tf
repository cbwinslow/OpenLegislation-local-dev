variable "environment" {
  description = "Environment name (dev/prod)"
  type        = string
  default     = "dev"
}

variable "server_type" {
  description = "Hetzner server type (e.g., cx22)"
  type        = string
  default     = "cx22"
}

variable "location" {
  description = "Hetzner location (e.g., fsn1 for Falkenstein)"
  type        = string
  default     = "fsn1"
}

variable "image" {
  description = "Server image (e.g., ubuntu-22.04)"
  type        = string
  default     = "ubuntu-22.04"
}

variable "ssh_keys" {
  description = "List of SSH key names or IDs"
  type        = list(string)
  default     = []
}

variable "network_name" {
  description = "Private network name"
  type        = string
  default     = "openleg-network"
}

variable "volume_size" {
  description = "Volume size in GB for data storage"
  type        = number
  default     = 20
}

variable "volume_type" {
  description = "Volume type (e.g., standard)"
  type        = string
  default     = "standard"
}

variable "firewall_rules" {
  description = "List of firewall rules"
  type = list(object({
    direction   = string
    protocol    = string
    port        = optional(string)
    source_ips  = list(string)
    destination_ips = optional(list(string))
  }))
  default = [
    {
      direction  = "in"
      protocol   = "tcp"
      port       = "22"
      source_ips = ["0.0.0.0/0"]
    },
    {
      direction  = "in"
      protocol   = "tcp"
      port       = "8080"
      source_ips = ["0.0.0.0/0"]
    },
    {
      direction  = "in"
      protocol   = "tcp"
      port       = "5432"
      source_ips = ["10.0.0.0/16"]  # Private network
    }
  ]
}
