terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.36"
    }
  }
  required_version = ">= 1.0"
}

provider "hcloud" {
  token = var.hcloud_token  # Set via env HETZNER_TOKEN or tfvar
}

data "hcloud_ssh_keys" "default" {
  most_recent = true
  with_selector = var.ssh_keys != [] ? join(",", var.ssh_keys) : null
}

# Private Network
resource "hcloud_network" "private" {
  name     = "${var.environment}-openleg-network"
  ip_range = "10.0.0.0/16"
  labels = {
    Environment = var.environment
  }
}

resource "hcloud_network_subnet" "private" {
  network_id   = hcloud_network.private.id
  type         = "cloud"
  network_zone = var.location
  ip_range     = "10.0.1.0/24"
}

# Firewall
resource "hcloud_firewall" "app" {
  name = "${var.environment}-app-firewall"
  labels = {
    Environment = var.environment
  }

  dynamic "rule" {
    for_each = var.firewall_rules
    content {
      direction    = rule.value.direction
      protocol     = rule.value.protocol
      port         = rule.value.port
      source_ips   = rule.value.source_ips
      description  = "Rule for ${rule.value.protocol}:${rule.value.port}"
    }
  }
}

# Volume for data storage
resource "hcloud_volume" "data" {
  name      = "${var.environment}-data-volume"
  size      = var.volume_size
  format    = "ext4"
  location  = var.location
  labels = {
    Environment = var.environment
  }
}

# Server (immutable: Use autoscaling-like with multiple if needed)
resource "hcloud_server" "app" {
  count      = 2  # HA: 2 servers
  name       = "${var.environment}-app-${count.index + 1}"
  image      = var.image
  server_type = var.server_type
  location   = var.location
  ssh_keys   = data.hcloud_ssh_keys.default.ssh_keys
  user_data  = templatefile("${path.module}/user_data.sh", {
    environment = var.environment
  })
  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }
  private_net {
    subnet_id = hcloud_network_subnet.private.id
  }
  depends_on = [hcloud_volume.data]
  labels = {
    Environment = var.environment
  }

  connection {
    type        = "ssh"
    user        = "root"
    private_key = file("~/.ssh/id_rsa")  # Adjust
    host        = self.ipv4_address
  }

  # Attach volume to first server
  provisioner "remote-exec" {
    inline = [
      "mkfs.ext4 ${hcloud_volume.data[0].linux_device}",
      "mkdir /data",
      "mount ${hcloud_volume.data[0].linux_device} /data"
    ]
  }
}

resource "hcloud_volume_attachment" "data" {
  count      = 1
  volume_id  = hcloud_volume.data.id
  server_id  = hcloud_server.app[0].id
  automount  = true
  depends_on = [hcloud_server.app]
}

# Load Balancer for HA
resource "hcloud_load_balancer" "app" {
  name       = "${var.environment}-app-lb"
  load_balancer_type = "lb11"
  location   = var.location
  labels = {
    Environment = var.environment
  }

  target {
    type = "ip"
    ip   = hcloud_server.app[0].ipv4_address
  }

  target {
    type = "ip"
    ip   = hcloud_server.app[1].ipv4_address
  }

  service {
    protocol         = "TCP"
    listen_port      = 80
    destination_port = 8080
    health_check {
      protocol         = "TCP"
      port             = 8080
      interval         = 10
      timeout          = 5
      retries          = 3
    }
  }

  labels = {
    Environment = var.environment
  }
}

# Outputs
output "server_ips" {
  value = [for server in hcloud_server.app : server.ipv4_address]
}

output "load_balancer_ip" {
  value = hcloud_load_balancer.app.ipv4_address
}

output "network_id" {
  value = hcloud_network.private.id
}

output "volume_id" {
  value = hcloud_volume.data.id
}
