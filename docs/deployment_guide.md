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

## Core OpenLegislation Components Installers
### 6. PostgreSQL (Bare Metal)
#### Description
Database for OpenLegislation app and Flyway migrations.

#### Script
`tools/install_postgres.sh`

#### Usage
1. Set env: `export DB_PASS=strongpass`
2. `cd tools && chmod +x install_postgres.sh && sudo ./install_postgres.sh`
3. Creates `openleg` DB/user; run Flyway from core app script.

#### Testing
- `psql -h localhost -U openleg -d openleg -c '\dt'` (lists tables after migrations)
- Logs: `/var/log/postgresql/`

### 7. Elasticsearch 8 (Bare Metal)
#### Description
Search engine for legislation indexing (matches client v8.14.3).

#### Script
`tools/install_elasticsearch.sh`

#### Usage
1. `sudo ES_HEAP=2g ./tools/install_elasticsearch.sh` (adjust heap)
2. Config: Edit `/etc/elasticsearch/elasticsearch.yml` for prod (e.g., security).

#### Testing
- `curl localhost:9200/_cluster/health` (green status)
- Logs: `/var/log/elasticsearch/`

### 8. Tomcat 9 (Bare Metal)
#### Description
Application server for Java WAR deployment.

#### Script
`tools/install_tomcat.sh`

#### Usage
1. `sudo ./tools/install_tomcat.sh`
2. Deploys WAR via core app script.

#### Testing
- `curl http://localhost:8080` (Tomcat welcome)
- Logs: `/var/log/tomcat9/`

### 9. Core Java Application (Bare Metal)
#### Description
Builds Spring/Java WAR, deploys to Tomcat, configures props, runs Flyway.

#### Script
`tools/install_core_app.sh`

#### Usage
1. Set env: `export DB_PASS=pass ES_HOST=localhost:9200`
2. `sudo ./tools/install_core_app.sh`
3. Clones to `/opt/openleg`, builds, deploys to Tomcat.

#### Testing
- `curl http://localhost:8080/api` (API endpoints)
- Check Tomcat logs for startup.

### 10. Python Ingestion Tools (Venv with uv)
#### Description
Tools for federal/state data ingestion (govinfo, bulk ingest).

#### Script
`tools/install_python_tools.sh`

#### Usage
1. `./tools/install_python_tools.sh` (non-sudo)
2. Activate: `source /opt/openleg/tools/venv/bin/activate`
3. Run: `uv run python govinfo_data_connector.py`

#### Testing
- `uv run python -c "import requests; print('OK')"`
- Run sample: `./tools/bulk_ingest_congress_gov.sh`

### 11. GitLab (Bare Metal Omnibus - Bash Equivalent)
#### Description
Git repo manager (replaces Ansible).

#### Script
`tools/install_gitlab.sh`

#### Usage
1. Set env: `export GITLAB_EXTERNAL_URL=http://your-domain.com GITLAB_ROOT_PASS=strongpass`
2. `sudo ./tools/install_gitlab.sh`
3. Reconfigure: `gitlab-ctl reconfigure`

#### Testing
- Access URL, login with root creds
- `gitlab-ctl status`

### 12. Bin Scripts and Cron Jobs
#### Description
Legacy bash scripts for mirroring, data transfer, crons.

#### Script
`tools/setup_bin_crons.sh`

#### Usage
1. `./tools/setup_bin_crons.sh` (or sudo for root crons)
2. Copies to `/opt/openleg/bin`, adds example crontab entries.

#### Testing
- `crontab -l | grep openleg`
- Manual run: `/opt/openleg/bin/mirror_aging.sh`

## Overall Testing and Validation
1. Run all scripts in order: DB/ES/Tomcat/Core App/Python Tools, then ancillaries (monitoring first).
2. Monitor with stack: Add Tomcat/GitLab as Prometheus targets; use Sentry for errors.
3. Full stack access: Verify ports (5432 DB, 9200 ES, 8080 Tomcat, etc.); resolve conflicts.
4. End-to-end: Ingest sample data via Python tools, query via Tomcat API, check ES indices.
5. Backup: Script data (/var/lib/postgresql, /var/lib/elasticsearch, /opt/openleg).
6. Production: Systemd timers for backups; Grafana alerts for services.

## Usage Summary
- Core install order: `sudo ./tools/install_postgres.sh && sudo ./tools/install_elasticsearch.sh && sudo ./tools/install_tomcat.sh && sudo DB_PASS=pass ./tools/install_core_app.sh && ./tools/install_python_tools.sh && ./tools/setup_bin_crons.sh`
- Ancillary: Existing Docker/package scripts + new GitLab/bash crons.
- Customize: Env vars for creds/URLs; edit scripts for specifics.
- Cleanup: `apt purge postgresql tomcat9 elasticsearch gitlab-ee` etc.; remove /opt/openleg.

For issues, check logs/services. Contribute back to OpenLegislation repo if useful!
