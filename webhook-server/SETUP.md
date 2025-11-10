# Webhook Server Setup Guide

Step-by-step guide to deploy the AI-powered PR review webhook server on your homelab.

## Overview

This guide will help you:
1. Set up the webhook server on your homelab
2. Configure GitHub to send webhook events
3. Expose the server to the internet (securely)
4. Test and monitor the system

**Time Required:** 30-60 minutes

## Part 1: Server Setup

### Option A: Docker Deployment (Recommended)

#### Prerequisites
- Linux server (Ubuntu, Debian, CentOS, etc.)
- 1GB+ RAM, 10GB+ disk space
- SSH access
- Domain name (optional, but recommended)

#### Steps

1. **SSH into your homelab server:**
   ```bash
   ssh user@your-homelab-server
   ```

2. **Install Docker and Docker Compose:**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   
   # Log out and back in for group changes
   exit
   ssh user@your-homelab-server
   ```

3. **Create deployment directory:**
   ```bash
   sudo mkdir -p /opt/openleg-webhook
   sudo chown $USER:$USER /opt/openleg-webhook
   cd /opt/openleg-webhook
   ```

4. **Copy webhook server files:**
   
   From your local machine:
   ```bash
   cd /path/to/OpenLegislation-local-dev
   scp -r webhook-server/* user@your-homelab-server:/opt/openleg-webhook/
   ```

5. **Configure environment variables:**
   ```bash
   cd /opt/openleg-webhook
   cp .env.example .env
   nano .env
   ```

   Fill in these required values:
   ```bash
   # GitHub Personal Access Token
   # Create at: https://github.com/settings/tokens
   # Required scopes: repo, write:repo_hook
   GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

   # Generate with: openssl rand -hex 32
   GITHUB_WEBHOOK_SECRET=your_random_64_char_hex_string

   # OpenRouter API Key
   # Get from: https://openrouter.ai/keys
   OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx

   # AI Model (optional, defaults to claude-3.5-sonnet)
   OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

   # Auto-merge settings
   AUTO_MERGE_ENABLED=false  # Set to true to enable auto-merge
   REVIEW_THRESHOLD_SCORE=7
   ```

6. **Start the webhook server:**
   ```bash
   # Use the deployment script
   ./deploy.sh
   
   # Or manually
   docker-compose up -d
   ```

7. **Verify it's running:**
   ```bash
   docker-compose ps
   docker-compose logs -f
   
   # Test health endpoint
   curl http://localhost:5000/health
   ```

   Expected output:
   ```json
   {
     "status": "healthy",
     "timestamp": "2024-01-01T12:00:00.000000",
     "version": "1.0.0"
   }
   ```

### Option B: Manual Python Deployment

If you prefer not to use Docker:

```bash
# Install Python 3.9+
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Create virtual environment
cd /opt/openleg-webhook
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure .env (same as above)
cp .env.example .env
nano .env

# Run with gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

## Part 2: Expose to Internet

GitHub webhooks need to reach your server. Choose one method:

### Option A: Cloudflare Tunnel (Recommended - Free & Secure)

Best for: Security, ease of use, no port forwarding needed

1. **Sign up for Cloudflare** (free): https://dash.cloudflare.com/sign-up

2. **Add your domain** to Cloudflare (if not already)

3. **Install cloudflared:**
   ```bash
   curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
   chmod +x cloudflared
   sudo mv cloudflared /usr/local/bin/
   ```

4. **Authenticate:**
   ```bash
   cloudflared tunnel login
   ```

5. **Create tunnel:**
   ```bash
   cloudflared tunnel create openleg-webhook
   ```

6. **Configure tunnel:**
   ```bash
   mkdir -p ~/.cloudflared
   nano ~/.cloudflared/config.yml
   ```

   Add:
   ```yaml
   tunnel: openleg-webhook
   credentials-file: /home/user/.cloudflared/<tunnel-id>.json

   ingress:
     - hostname: webhook.yourdomain.com
       service: http://localhost:5000
     - service: http_status:404
   ```

7. **Route DNS:**
   ```bash
   cloudflared tunnel route dns openleg-webhook webhook.yourdomain.com
   ```

8. **Run tunnel:**
   ```bash
   # Test first
   cloudflared tunnel run openleg-webhook

   # Then install as service
   sudo cloudflared service install
   sudo systemctl start cloudflared
   sudo systemctl enable cloudflared
   ```

9. **Your webhook URL:** `https://webhook.yourdomain.com/webhook`

### Option B: Nginx Reverse Proxy + Let's Encrypt

Best for: Full control, existing Nginx setup

1. **Install Nginx and Certbot:**
   ```bash
   sudo apt update
   sudo apt install nginx certbot python3-certbot-nginx
   ```

2. **Configure Nginx:**
   ```bash
   sudo nano /etc/nginx/sites-available/webhook
   ```

   Add:
   ```nginx
   server {
       listen 80;
       server_name webhook.yourdomain.com;

       location / {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_read_timeout 120s;
       }
   }
   ```

3. **Enable site:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/webhook /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

4. **Get SSL certificate:**
   ```bash
   sudo certbot --nginx -d webhook.yourdomain.com
   ```

5. **Open firewall:**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

6. **Your webhook URL:** `https://webhook.yourdomain.com/webhook`

### Option C: Port Forwarding (Simple but less secure)

Best for: Testing, home networks

1. **Find your public IP:**
   ```bash
   curl ifconfig.me
   ```

2. **Configure port forwarding on your router:**
   - External port: 5000
   - Internal IP: Your server's local IP
   - Internal port: 5000
   - Protocol: TCP

3. **Your webhook URL:** `http://YOUR_PUBLIC_IP:5000/webhook`

   ⚠️ **Security Note:** This exposes your server directly. Use HTTPS and firewall rules.

### Option D: ngrok (Testing Only)

Best for: Quick testing, temporary setups

```bash
# Install ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/

# Authenticate (get token from https://dashboard.ngrok.com/)
ngrok config add-authtoken YOUR_NGROK_TOKEN

# Start tunnel
ngrok http 5000
```

Copy the `https://` URL shown (e.g., `https://abc123.ngrok.io`)

⚠️ **Note:** Free ngrok URLs change on restart. Not suitable for production.

## Part 3: Configure GitHub Webhook

1. **Go to your repository** on GitHub

2. **Navigate to Settings → Webhooks → Add webhook**

3. **Configure webhook:**
   - **Payload URL:** `https://webhook.yourdomain.com/webhook`
   - **Content type:** `application/json`
   - **Secret:** Copy from `GITHUB_WEBHOOK_SECRET` in your `.env`
   - **SSL verification:** Enable SSL verification (recommended)
   - **Which events:** Select "Let me select individual events"
     - ✅ Pull requests
     - (Uncheck everything else)
   - **Active:** ✅ Check this box

4. **Add webhook**

5. **Test delivery:**
   - Click on the webhook you just created
   - Click "Recent Deliveries"
   - Click "Redeliver" on any past event to test
   - Or open a new PR to trigger

## Part 4: Test the Setup

### Test 1: Health Check

```bash
curl https://webhook.yourdomain.com/health
```

Expected:
```json
{"status": "healthy", "timestamp": "...", "version": "1.0.0"}
```

### Test 2: Manual Webhook Test

From your local machine (with webhook server files):

```bash
cd webhook-server
python3 test_webhook.py
```

### Test 3: Real PR Test

1. Create a test branch in your repository
2. Make a small code change
3. Open a pull request
4. Check:
   - ✅ Webhook delivery in GitHub Settings
   - ✅ Server logs: `docker-compose logs -f`
   - ✅ AI review comment appears on PR

## Part 5: Enable Auto-Merge (Optional)

⚠️ **Warning:** Only enable if you understand the implications.

1. **Enable auto-merge in GitHub:**
   - Repository Settings → General
   - Scroll to "Pull Requests"
   - ✅ Check "Allow auto-merge"

2. **Configure branch protection (recommended):**
   - Settings → Branches → Add rule
   - Branch name: `main`
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass before merging

3. **Enable in webhook server:**
   ```bash
   nano /opt/openleg-webhook/.env
   ```
   
   Change:
   ```bash
   AUTO_MERGE_ENABLED=true
   REVIEW_THRESHOLD_SCORE=7  # Adjust threshold as needed
   ```

4. **Restart server:**
   ```bash
   docker-compose restart
   ```

## Monitoring & Maintenance

### View Logs

```bash
# Docker logs
docker-compose logs -f

# Or specific files
tail -f logs/access.log
tail -f logs/error.log
```

### Check Status

```bash
# Container status
docker-compose ps

# Server health
curl https://webhook.yourdomain.com/health

# GitHub webhook deliveries
# Go to: Repository Settings → Webhooks → Recent Deliveries
```

### Update Server

```bash
cd /opt/openleg-webhook
git pull  # If you cloned the repo
docker-compose pull
docker-compose up -d
```

### Backup Configuration

```bash
# Backup .env file (important!)
cp /opt/openleg-webhook/.env /secure/backup/location/.env.backup

# Backup logs
tar -czf webhook-logs-$(date +%Y%m%d).tar.gz logs/
```

### Set Up Systemd Service (Auto-start)

```bash
# Copy service file
sudo cp /opt/openleg-webhook/openleg-webhook.service /etc/systemd/system/

# Edit WorkingDirectory if needed
sudo nano /etc/systemd/system/openleg-webhook.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable openleg-webhook
sudo systemctl start openleg-webhook

# Check status
sudo systemctl status openleg-webhook
```

## Troubleshooting

### Server won't start

```bash
# Check logs
docker-compose logs

# Common issues:
# 1. Port 5000 already in use
sudo lsof -i :5000
# Kill process or change port in docker-compose.yml

# 2. Invalid .env file
cat .env
# Make sure no quotes around values

# 3. Docker not running
sudo systemctl status docker
sudo systemctl start docker
```

### Webhook not receiving events

1. **Check GitHub delivery:**
   - Settings → Webhooks → Recent Deliveries
   - Look for 200 response
   - If failed, check error message

2. **Check firewall:**
   ```bash
   sudo ufw status
   # Make sure port 80/443 are open
   ```

3. **Check webhook URL:**
   ```bash
   curl -X POST https://webhook.yourdomain.com/webhook
   # Should return error but proves connectivity
   ```

### AI review not posting

1. **Check logs for errors:**
   ```bash
   docker-compose logs -f | grep -i error
   ```

2. **Verify GitHub token:**
   - Must have `repo` scope
   - Test: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user`

3. **Verify OpenRouter key:**
   - Test at https://openrouter.ai/playground

### Auto-merge not working

1. **Check settings:**
   ```bash
   grep AUTO_MERGE .env
   # Should be: AUTO_MERGE_ENABLED=true
   ```

2. **Check repository settings:**
   - Repository Settings → General
   - "Allow auto-merge" must be enabled

3. **Check branch protection:**
   - If required reviews > 1, auto-merge may fail
   - Adjust branch protection rules

## Security Checklist

- [ ] Using HTTPS (not HTTP)
- [ ] Webhook secret is strong random value (32+ chars)
- [ ] GitHub token has minimal scopes (only `repo`)
- [ ] `.env` file permissions are restricted (600)
- [ ] Server firewall is configured
- [ ] Logs are rotated and monitored
- [ ] SSL certificate is valid and auto-renews
- [ ] Regular updates scheduled

## Next Steps

1. ✅ Test with a few PRs manually
2. ✅ Monitor for 1-2 weeks
3. ✅ Adjust AI model if needed (cost/quality trade-off)
4. ✅ Enable auto-merge for Dependabot PRs
5. ✅ Expand to other repositories
6. ✅ Set up monitoring/alerts

## Getting Help

- **Server logs:** `docker-compose logs -f`
- **GitHub webhook logs:** Repository Settings → Webhooks
- **OpenRouter status:** https://status.openrouter.ai/
- **Issues:** Open issue in repository with `webhook` label

## Cost Optimization

### Reduce OpenRouter Costs

1. **Use cheaper model:**
   ```bash
   OPENROUTER_MODEL=openai/gpt-3.5-turbo  # Cheaper than Claude
   ```

2. **Truncate large diffs:**
   - Already done in code (8000 chars max)
   - Adjust in `app.py` if needed

3. **Skip trivial PRs:**
   - Add logic to skip docs-only changes
   - Skip Dependabot patch updates

### Monitor Usage

```bash
# Check OpenRouter usage
# Dashboard: https://openrouter.ai/dashboard

# Estimate costs:
# Small PR: ~$0.02
# Medium PR: ~$0.10
# Large PR: ~$0.50
# 
# 100 PRs/month ≈ $5-20/month
```

## Advanced Configuration

### Multiple Repositories

Same webhook server can handle multiple repos:

1. Add webhook to each repository
2. All point to same server URL
3. Server handles all automatically

### Custom Rules per Repo

Edit `app.py` and modify `should_auto_merge()`:

```python
def should_auto_merge(pr_data, review_data):
    repo = pr_data['base']['repo']['full_name']
    
    # Never auto-merge production
    if repo == 'org/production-repo':
        return False
    
    # Default logic
    # ...
```

### Integration with Slack

Add to `app.py`:

```python
def notify_slack(pr_number, review_data):
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if not webhook_url:
        return
    
    requests.post(webhook_url, json={
        "text": f"PR #{pr_number} reviewed: {review_data['summary']}"
    })

# Call in webhook() after posting review
notify_slack(pr_number, review_data)
```

## Success Metrics

After 1 month, you should see:

- ✅ 50-100% of PRs reviewed by AI
- ✅ Consistent review quality
- ✅ Faster PR merge times
- ✅ Fewer bugs merged
- ✅ Cost: $5-30/month depending on volume

---

**Questions?** Open an issue or check the main README.md
