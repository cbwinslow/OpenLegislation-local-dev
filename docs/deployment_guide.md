# Deployment Guide for OpenLegislation Tools and Monitoring Stack

This guide documents the installation scripts and configurations created for deploying OpenWebUI, Sentry, GitLab (via Ansible), a monitoring stack (Grafana, Loki, OpenSearch, Netdata, Prometheus), and pulling official documentation. All scripts assume an Ubuntu/Debian-based Linux system (e.g., Ubuntu 22.04+). Run scripts as root or with `sudo`.

## Prerequisites
- Ubuntu/Debian OS (tested on 20.04/22.04).
- Internet access for package downloads and git clones.
- At least 4GB RAM, 20GB free disk space (more for production).
- Sudo access.
- For Docker-based installs: Ensure ports are free (e.g., 3000 for OpenWebUI, 80/443 for GitLab).
- For Ansible: Install Ansible (`sudo apt install ansible`).
- Firewall: Open necessary ports (e.g., `ufw allow 3000` for OpenWebUI).
- Update system: `sudo apt update && sudo apt upgrade -y`.

**Security Note**: For production, use strong passwords, HTTPS, firewalls (e.g., UFW), and backups. Edit configs for secrets.

## 1. OpenWebUI (Docker)
### Description
Self-hosted WebUI for LLMs (e.g., Ollama integration).

### Script
`tools/install_openwebui.sh`

### Usage
1. `cd /path/to/workspace/tools`
2. `chmod +x install_openwebui.sh`
3. `sudo ./install_openwebui.sh`

### Configuration
- Data: `/opt/openwebui` (persistent volume).
- Port: 3000 (maps to container 8080).
- Env: `OLLAMA_BASE_URL=http://host.docker.internal:11434` (edit for Ollama host).
- Restart: Always.

### Testing
1. Check container: `docker ps | grep openwebui` (should show running).
2. Access: Open `http://localhost:3000` in browser.
3. Logs: `docker logs openwebui`.
4. Stop/Start: `docker stop openwebui` / `docker start openwebui`.
5. Verify integration: If Ollama runs on 11434, models should load in UI.

### Troubleshooting
- Docker not starting: `systemctl status docker`.
- Port conflict: Change `-p 3000:8080` in script.
- Ollama not connecting: Ensure Ollama runs and use correct host IP.

## 2. Sentry Self-Hosted (Docker)
### Description
Error monitoring and performance tool.

### Script
`tools/install_sentry.sh`

### Usage
1. `cd /path/to/workspace/tools`
2. `chmod +x install_sentry.sh`
3. `sudo ./install_sentry.sh`

### Configuration
- Dir: `/opt/sentry/onpremise`.
- Config: Edit `.env` in `/opt/sentry/onpremise` (set `SENTRY_SECRET_KEY`, passwords, SMTP).
- Services: PostgreSQL, Redis, Sentry web/workers (via docker-compose).
- URL: `http://localhost` (change in .env).

### Testing
1. Check services: `cd /opt/sentry/onpremise && docker-compose ps` (all should be Up).
2. Wait 1-2 min, access `http://localhost` and complete setup (create superuser).
3. Logs: `docker-compose logs -f`.
4. Test event: Integrate a sample app and trigger an error; check dashboard.
5. Stop/Start: `docker-compose down` / `docker-compose up -d`.

### Troubleshooting
- DB init fails: Check passwords in .env; restart with `docker-compose down -v && docker-compose up -d`.
- Port 80 busy: Edit `docker-compose.yml` ports.
- Production: Scale workers, add HTTPS reverse proxy (e.g., Nginx).

## 3. GitLab (Ansible - Bare Metal Omnibus)
### Description
Git repository manager with CI/CD.

### Setup
Ansible project in `ansible/gitlab/`:
- `group_vars/all.yml`: Variables (edit URL, email, password).
- `inventory/hosts.ini`: Targets localhost.
- `site.yml`: Main playbook.
- `roles/gitlab/tasks/main.yml`: Installation tasks.

### Usage
1. Install Ansible: `sudo apt install ansible`.
2. Edit `ansible/gitlab/group_vars/all.yml` (set `gitlab_external_url`, etc.).
3. `cd ansible/gitlab`
4. `ansible-playbook -i inventory/hosts.ini site.yml`

### Configuration
- Package: GitLab EE (change to CE if needed).
- Config: Applied to `/etc/gitlab/gitlab.rb` (external_url, timezone).
- Initial login: Root email/password from vars.
- Post-install: `sudo gitlab-ctl reconfigure`.

### Testing
1. Check install: `dpkg -l | grep gitlab` (should show installed).
2. Services: `sudo gitlab-ctl status` (all should be run).
3. Access: `http://your_gitlab_url` (login with root creds).
4. Create repo: New project in UI; clone via git.
5. Reconfigure: `sudo gitlab-ctl reconfigure` after changes.

### Troubleshooting
- Repo add fails: Check GPG key; run `apt update`.
- HTTPS: Set `gitlab_https: true` and add cert paths in vars.
- Memory issues: GitLab needs 4GB+; monitor with `gitlab-ctl tail`.
- Fallback to Docker: If bare metal fails, use official Docker image manually.

## 4. Monitoring Stack (Bare Metal Packages)
### Description
Observability tools: Metrics (Prometheus/Netdata), Logs (Loki), Search (OpenSearch), Viz (Grafana).

### Script
`tools/install_monitoring.sh`

### Usage
1. `cd /path/to/workspace/tools`
2. `chmod +x install_monitoring.sh`
3. `sudo ./install_monitoring.sh`

### Configuration
- Grafana: `/etc/grafana/grafana.ini` (default admin/admin).
- Prometheus: `/etc/prometheus/prometheus.yml` (add scrape configs).
- Loki: `/etc/loki/local-config.yaml` (filesystem storage; edit for S3).
- OpenSearch: `/etc/opensearch/opensearch.yml` (single node).
- Netdata: `/etc/netdata/netdata.conf` (auto-config).
- Ports: 3000 (Grafana), 9090 (Prom), 3100 (Loki), 9200 (OS), 19999 (Netdata).

### Testing
1. Check services: `systemctl status grafana-server prometheus loki opensearch netdata` (all active).
2. Access:
   - Grafana: `http://localhost:3000` → Add datasources (Prom:9090, Loki:3100, OS:9200).
   - Prometheus: `http://localhost:9090` → Query `up`.
   - Loki: `curl http://localhost:3100/ready` (should return "ready").
   - OpenSearch: `curl http://localhost:9200` (JSON response).
   - Netdata: `http://localhost:19999` (dashboard loads).
3. Integration: In Grafana, create dashboard with Prom metrics; log to Loki via Promtail (install separately if needed).
4. Logs: `journalctl -u grafana-server` etc.

### Troubleshooting
- Repo keys fail: Manual wget/gpg as in script.
- OpenSearch cluster: For multi-node, edit yml files.
- Storage: Loki/OpenSearch use /tmp; change to persistent dirs.
- Fallback to Docker: Use docker-compose for stack if packages fail.

## 5. Pull Documentation Script
### Description
Clones official Markdown docs repos to `~/KnowledgeBase/{tool}/` for vectorization.

### Script
`tools/pull_docs.sh`

### Usage
1. `cd /path/to/workspace/tools`
2. `chmod +x pull_docs.sh`
3. `./pull_docs.sh` (no sudo needed; installs git/pandoc if missing).

### Configuration
- Base: `~/KnowledgeBase`.
- Repos: Listed in script (edit TOOLS array for branches/URLs).

### Testing
1. Run script; check `~/KnowledgeBase/` for subdirs with .git.
2. Verify MD files: `ls ~/KnowledgeBase/OpenWebUI/*.md` (or docs/ subdir).
3. Update: Rerun to `git pull`.
4. Vectorize: Use tools like LangChain to embed MD files.

### Troubleshooting
- Git clone fails: Check network; manual clone if needed.
- Non-MD docs: Some (e.g., Grafana) have MD in subpaths; convert HTML if any via pandoc.

## Overall Testing and Validation
1. Run all scripts in order (monitoring first for observability).
2. Monitor with stack: Add GitLab/Sentry/OpenWebUI as scrape targets in Prometheus.
3. Full stack access: Ensure no port conflicts (e.g., Grafana/OpenWebUI both 3000? Change one).
4. Backup: Script data dirs (e.g., rsync /opt/*).
5. Production: Use systemd timers for backups; monitor with alerts in Grafana.

## Usage Summary
- All scripts in `tools/`: Make executable, run with sudo (except pull_docs).
- Ansible: From `ansible/gitlab/`.
- Customize: Edit scripts/vars before running.
- Cleanup: `docker rm -f openwebui` for Docker; `apt purge` for packages.

For issues, check logs/services. Contribute back to OpenLegislation repo if useful!