variable "environment" {
  description = "Environment name (dev/prod)"
  type        = string
  default     = "dev"
}

variable "zone_name" {
  description = "Cloudflare zone/domain name (e.g., openlegislation.com)"
  type        = string
}

variable "account_id" {
  description = "Cloudflare account ID"
  type        = string
  sensitive   = true
}

variable "api_token" {
  description = "Cloudflare API token (set via env CLOUDFLARE_API_TOKEN)"
  type        = string
  sensitive   = true
  default     = null
}

variable "dns_records" {
  description = "List of DNS records"
  type = list(object({
    name    = string
    type    = string
    value   = string
    proxied = optional(bool, true)
  }))
  default = []
}

variable "pages_project_name" {
  description = "Cloudflare Pages project name"
  type        = string
  default     = "openlegislation-pages"
}

variable "pages_source_dir" {
  description = "Local dir for Pages content (relative to module)"
  type        = string
  default     = "../pages"  # Assume pages/ dir with static files
}

variable "worker_name" {
  description = "Cloudflare Worker name for edge logic"
  type        = string
  default     = "openleg-api-worker"
}

variable "worker_script" {
  description = "Worker script content or path"
  type        = string
  default     = "worker.js"  # Assume file in module
}
