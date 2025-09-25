#!/bin/bash

# Script to install monitoring stack on bare metal (Ubuntu/Debian)
# Components: Grafana, Loki, OpenSearch, NetData, Prometheus
# Run as root or with sudo
# Basic install; configure integrations manually (e.g., Grafana datasources)

set -e  # Exit on error

echo "Installing monitoring stack..."

# Update system
apt update -y && apt upgrade -y

# Install common dependencies
apt install -y wget apt-transport-https ca-certificates gnupg lsb-release curl unzip

# 1. Install Grafana (bare metal via apt)
echo "Installing Grafana..."
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor -o /usr/share/keyrings/grafana.gpg
echo "deb [signed-by=/usr/share/keyrings/grafana.gpg] https://apt.grafana.com stable main" | tee /etc/apt/sources.list.d/grafana.list
apt update -y
apt install -y grafana
systemctl daemon-reload
systemctl start grafana-server
systemctl enable grafana-server
echo "Grafana installed. Access at http://localhost:3000 (admin/admin)"

# 2. Install Prometheus (bare metal via apt)
echo "Installing Prometheus..."
wget -q -O - https://packagecloud.io/gpg.key | gpg --dearmor -o /usr/share/keyrings/prometheus.gpg
echo "deb [signed-by=/usr/share/keyrings/prometheus.gpg] https://packagecloud.io/prometheus/prometheus/debian/ $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/prometheus.list
apt update -y
apt install -y prometheus
systemctl start prometheus
systemctl enable prometheus
echo "Prometheus installed. Access at http://localhost:9090"

# 3. Install Loki (bare metal via apt/Debian package)
echo "Installing Loki..."
wget -q -O - https://artifacts.grafana.com/gpg.key | gpg --dearmor -o /usr/share/keyrings/grafana-loki.gpg
echo "deb [signed-by=/usr/share/keyrings/grafana-loki.gpg] https://artifacts.grafana.com/loki/deb stable main" | tee /etc/apt/sources.list.d/loki.list
apt update -y
apt install -y loki
# Basic config: single instance
cat > /etc/loki/local-config.yaml << 'EOF'
auth_enabled: false
server:
  http_listen_port: 3100
ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s
  chunk_idle_period: 5m
  chunk_retain_period: 30s
schema_config:
  configs:
    - from: 2020-05-15
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 168h
storage_config:
  boltdb_shipper:
    active_index_directory: /tmp/loki/index
    cache_location: /tmp/loki/index_cache
    shared_store: filesystem
  filesystem:
    directory: /tmp/loki/chunks
limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
chunk_store_config:
  chunk_idle_period: 1h
  max_look_back_period: 0s
table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
compactor:
  working_directory: /tmp/loki/compactor
  shared_store: filesystem
  compaction_interval: 10m
  retention_enabled: false
EOF
systemctl start loki
systemctl enable loki
echo "Loki installed. Access at http://localhost:3100 (config in /etc/loki/local-config.yaml)"

# 4. Install OpenSearch (bare metal via apt)
echo "Installing OpenSearch..."
wget -qO - https://artifacts.opensearch.org/publickeys/opensearch.pgp | gpg --dearmor -o /usr/share/keyrings/opensearch.gpg
echo "deb [signed-by=/usr/share/keyrings/opensearch.gpg] https://artifacts.opensearch.org/releases/bundle/opensearch/2.x/apt stable main" | tee /etc/apt/sources.list.d/opensearch-2.x.list
apt update -y
apt install -y opensearch
# Basic config: single node
sed -i 's/#cluster.initial_cluster_manager_nodes: \["cluster-manager-node1"\]/cluster.initial_cluster_manager_nodes: \["node-1"\]/' /etc/opensearch/opensearch.yml
sed -i 's/#network.host: 192.168.0.1/network.host: 0.0.0.0/' /etc/opensearch/opensearch.yml
sed -i 's/#discovery.seed_hosts: \["host1", "host2"\]/discovery.seed_hosts: \["127.0.0.1"\]/' /etc/opensearch/opensearch.yml
systemctl daemon-reload
systemctl start opensearch
systemctl enable opensearch
echo "OpenSearch installed. Access at http://localhost:9200"

# 5. Install Netdata (bare metal via kickstart)
echo "Installing Netdata..."
bash <(curl -Ss https://my-netdata.io/kickstart.sh) --dont-wait
systemctl start netdata
systemctl enable netdata
echo "Netdata installed. Access at http://localhost:19999"

# Final notes
echo "Monitoring stack installed successfully!"
echo "Summary:"
echo "- Grafana: http://localhost:3000 (login: admin/admin)"
echo "- Prometheus: http://localhost:9090"
echo "- Loki: http://localhost:3100"
echo "- OpenSearch: http://localhost:9200"
echo "- Netdata: http://localhost:19999"
echo ""
echo "Next steps:"
echo "1. Configure Grafana datasources: Prometheus (http://localhost:9090), Loki (http://localhost:3100), OpenSearch (http://localhost:9200)"
echo "2. Set up dashboards in Grafana for monitoring."
echo "3. For production: Secure with HTTPS, firewalls, persistent storage."
echo "4. Netdata auto-monitors; check /etc/netdata for config."
echo ""
echo "To stop all: systemctl stop grafana-server prometheus loki opensearch netdata"
echo "To start all: systemctl start grafana-server prometheus loki opensearch netdata"