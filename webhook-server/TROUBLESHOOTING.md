# Troubleshooting Guide

Common issues and solutions for the webhook server.

## Table of Contents

- [Server Won't Start](#server-wont-start)
- [Webhook Not Receiving Events](#webhook-not-receiving-events)
- [AI Review Not Posting](#ai-review-not-posting)
- [Auto-Merge Not Working](#auto-merge-not-working)
- [High API Costs](#high-api-costs)
- [Performance Issues](#performance-issues)
- [Security Concerns](#security-concerns)

---

## Server Won't Start

### Symptom
`docker-compose up` fails or container exits immediately.

### Diagnosis
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs

# Check if port is in use
sudo lsof -i :5000
```

### Solutions

#### Port Already in Use
```bash
# Find and kill process using port 5000
sudo lsof -i :5000
sudo kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "5001:5000"  # Use 5001 instead
```

#### Invalid .env File
```bash
# Verify .env exists
ls -la .env

# Check for syntax errors (no quotes needed)
cat .env
# Correct: GITHUB_TOKEN=ghp_xxxx
# Wrong:   GITHUB_TOKEN="ghp_xxxx"

# Recreate from template
cp .env.example .env
nano .env
```

#### Docker Not Running
```bash
# Start Docker
sudo systemctl start docker

# Enable on boot
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

#### Missing Dependencies
```bash
# Rebuild with no cache
docker-compose build --no-cache

# Pull base image
docker pull python:3.11-slim
```

---

## Webhook Not Receiving Events

### Symptom
GitHub shows webhook deliveries failing or server never receives events.

### Diagnosis
```bash
# Check server is accessible
curl http://localhost:5000/health

# Check from external
curl https://webhook.yourdomain.com/health

# Check GitHub webhook deliveries
# Go to: Repository Settings → Webhooks → Recent Deliveries
```

### Solutions

#### Server Not Accessible from Internet

**Check Firewall:**
```bash
# Ubuntu/Debian
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# CentOS/RHEL
sudo firewall-cmd --list-all
sudo firewall-cmd --add-service=http --permanent
sudo firewall-cmd --add-service=https --permanent
sudo firewall-cmd --reload
```

**Check Reverse Proxy:**
```bash
# Nginx
sudo nginx -t
sudo systemctl status nginx
sudo journalctl -u nginx -n 50

# Test proxy
curl -I http://localhost:5000/health
curl -I https://webhook.yourdomain.com/health
```

**Check Cloudflare Tunnel:**
```bash
sudo systemctl status cloudflared
cloudflared tunnel info openleg-webhook
```

#### Webhook Signature Mismatch

```bash
# Verify secret in .env matches GitHub
cat .env | grep GITHUB_WEBHOOK_SECRET

# Check GitHub webhook secret
# Go to: Repository Settings → Webhooks → Edit
# Re-enter the same secret

# Test with curl (replace SECRET)
PAYLOAD='{"action":"ping"}'
SECRET="your_webhook_secret_here"
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print "sha256="$2}')

curl -X POST https://webhook.yourdomain.com/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: ping" \
  -H "X-Hub-Signature-256: $SIGNATURE" \
  -d "$PAYLOAD"
```

#### Wrong Webhook URL

```bash
# Verify URL in GitHub matches your deployment
# Should be: https://webhook.yourdomain.com/webhook
#            (with /webhook at the end)

# Test all endpoints
curl https://webhook.yourdomain.com/         # Service info
curl https://webhook.yourdomain.com/health   # Health check
curl -X POST https://webhook.yourdomain.com/webhook  # Webhook (will fail without signature)
```

#### SSL Certificate Issues

```bash
# Check certificate
openssl s_client -connect webhook.yourdomain.com:443

# Renew Let's Encrypt
sudo certbot renew

# Check expiration
echo | openssl s_client -connect webhook.yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

---

## AI Review Not Posting

### Symptom
Webhook receives events but no review appears on GitHub.

### Diagnosis
```bash
# Check logs for errors
docker-compose logs -f | grep -i error

# Verify tokens
echo $GITHUB_TOKEN | cut -c1-10  # Should start with ghp_
echo $OPENROUTER_API_KEY | cut -c1-10  # Should start with sk-or-
```

### Solutions

#### Invalid GitHub Token

```bash
# Test GitHub token
curl -H "Authorization: token YOUR_GITHUB_TOKEN" \
  https://api.github.com/user

# Check scopes
curl -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -I https://api.github.com/user \
  | grep X-OAuth-Scopes

# Should include: repo

# Create new token
# Go to: https://github.com/settings/tokens
# Scopes: repo (all), write:repo_hook
```

#### Invalid OpenRouter Key

```bash
# Test OpenRouter key
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer YOUR_OPENROUTER_KEY"

# Check credits
# Go to: https://openrouter.ai/dashboard

# Get new key
# Go to: https://openrouter.ai/keys
```

#### API Rate Limiting

```bash
# Check GitHub rate limit
curl -H "Authorization: token YOUR_GITHUB_TOKEN" \
  https://api.github.com/rate_limit

# Wait or upgrade token type
# Personal tokens: 5000 requests/hour
# App tokens: Higher limits
```

#### Model Not Available

```bash
# Check model name in .env
cat .env | grep OPENROUTER_MODEL

# Valid models:
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_MODEL=openai/gpt-4-turbo
OPENROUTER_MODEL=openai/gpt-3.5-turbo

# List available models
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer YOUR_OPENROUTER_KEY"
```

#### PR from Draft

```bash
# Server skips draft PRs by default
# Check PR status on GitHub
# Convert to "Ready for review" to trigger
```

---

## Auto-Merge Not Working

### Symptom
PRs get reviewed but don't auto-merge even with good scores.

### Diagnosis
```bash
# Check auto-merge enabled
cat .env | grep AUTO_MERGE_ENABLED

# Check logs for merge attempts
docker-compose logs | grep -i merge
```

### Solutions

#### Auto-Merge Not Enabled in .env

```bash
# Enable in .env
AUTO_MERGE_ENABLED=true

# Restart server
docker-compose restart
```

#### Auto-Merge Not Enabled in GitHub

```bash
# Go to: Repository Settings → General
# Scroll to "Pull Requests"
# Check: ☑ Allow auto-merge
# Save changes
```

#### Branch Protection Rules Too Strict

```bash
# Go to: Repository Settings → Branches → Branch protection rules
# For main branch:

# If "Required approving reviews" > 1:
# - Auto-merge won't work (needs human review)
# - Set to 1 or allow bot approvals

# If "Required status checks" includes failing checks:
# - PR can't merge until checks pass
# - Wait for CI to complete
```

#### Score Below Threshold

```bash
# Check threshold in .env
cat .env | grep REVIEW_THRESHOLD_SCORE

# Lower threshold if needed (not recommended)
REVIEW_THRESHOLD_SCORE=6

# Or improve code to get higher scores
```

#### High Severity Issues Found

```bash
# Auto-merge blocked if AI finds high-severity issues
# Review the AI comment on PR
# Fix issues and push new commit
```

---

## High API Costs

### Symptom
OpenRouter bills are higher than expected.

### Diagnosis
```bash
# Check usage on OpenRouter dashboard
# https://openrouter.ai/dashboard

# Count PRs reviewed
# GitHub: Insights → Pulse → Pull requests merged

# Review logs for API calls
docker-compose logs | grep "Analyzing PR" | wc -l
```

### Solutions

#### Switch to Cheaper Model

```bash
# Edit .env
# From: OPENROUTER_MODEL=anthropic/claude-3-opus (expensive)
# To:   OPENROUTER_MODEL=openai/gpt-3.5-turbo (70% cheaper)

# Or: openai/gpt-4-turbo (good balance)

# Restart
docker-compose restart
```

#### Skip Trivial PRs

Edit `app.py`, add to `webhook()` function:

```python
# Skip docs-only changes
files = get_pr_files(owner, repo, pr_number)
if all(f['filename'].startswith('docs/') for f in files):
    app.logger.info(f"Skipping docs-only PR #{pr_number}")
    return jsonify({'message': 'Skipping docs-only PR'}), 200

# Skip Dependabot patch updates
if pr_data['user']['login'] == 'dependabot[bot]':
    if 'patch' in pr_data['title'].lower():
        app.logger.info(f"Skipping Dependabot patch PR #{pr_number}")
        return jsonify({'message': 'Skipping Dependabot patch'}), 200
```

#### Reduce Diff Size

Already implemented (8000 chars max), but can reduce further in `app.py`:

```python
# In analyze_code_with_ai()
max_diff_length = 5000  # Reduce from 8000
```

#### Set Monthly Budget

```bash
# On OpenRouter dashboard
# Settings → Billing → Set spending limit
# Example: $20/month
```

---

## Performance Issues

### Symptom
Webhook takes too long to respond or times out.

### Diagnosis
```bash
# Check response time
time curl http://localhost:5000/health

# Check worker count
docker-compose exec webhook-server ps aux | grep gunicorn

# Check system resources
docker stats webhook-server
```

### Solutions

#### Increase Workers

Edit `Dockerfile`:

```dockerfile
# From: --workers 4
# To:   --workers 8
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "8", ...]
```

Rebuild:
```bash
docker-compose build
docker-compose up -d
```

#### Increase Timeout

Edit `Dockerfile`:

```dockerfile
# Add: --timeout 180 (3 minutes)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "180", ...]
```

#### Upgrade Server Resources

```bash
# Check current resources
free -h
df -h

# If running out of RAM:
# - Upgrade server
# - Or reduce workers

# If CPU bottleneck:
# - Upgrade CPU cores
# - Or reduce parallel requests
```

#### Use Async Processing

For advanced users, modify to use Celery workers:

```bash
# Add Redis for queue
docker-compose.yml:
  redis:
    image: redis:alpine
    
# Install celery
requirements.txt:
  celery==5.3.4
  redis==5.0.1
```

---

## Security Concerns

### Symptom
Security audit finds issues or suspicious activity.

### Solutions

#### Rotate Credentials

```bash
# Generate new webhook secret
openssl rand -hex 32

# Update .env
nano .env
# GITHUB_WEBHOOK_SECRET=<new_secret>

# Update GitHub webhook
# Repository Settings → Webhooks → Edit
# Secret: <new_secret>

# Restart server
docker-compose restart
```

#### Restrict .env Permissions

```bash
chmod 600 .env
ls -la .env
# Should show: -rw------- (owner read/write only)
```

#### Enable HTTPS Only

```bash
# Disable HTTP in Nginx config
# Remove: listen 80;
# Keep only: listen 443 ssl;

# Or redirect HTTP to HTTPS
server {
    listen 80;
    return 301 https://$host$request_uri;
}
```

#### Add Rate Limiting

Edit `app.py`, add Flask-Limiter:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/webhook', methods=['POST'])
@limiter.limit("10 per minute")
def webhook():
    # ...
```

#### Review Logs for Anomalies

```bash
# Check for failed authentications
docker-compose logs | grep "Invalid signature" | wc -l

# Check for unusual IPs
docker-compose logs | grep "Processing PR" | awk '{print $NF}' | sort | uniq -c

# Set up log monitoring
# Use: Loki, Elasticsearch, or CloudWatch
```

---

## Getting More Help

### Collect Diagnostic Info

```bash
# Save to file
{
  echo "=== System Info ==="
  uname -a
  docker --version
  docker-compose --version
  
  echo -e "\n=== Container Status ==="
  docker-compose ps
  
  echo -e "\n=== Recent Logs ==="
  docker-compose logs --tail 50
  
  echo -e "\n=== Environment (sanitized) ==="
  cat .env | grep -v "TOKEN\|SECRET\|KEY" || echo "No .env file"
  
  echo -e "\n=== Disk Space ==="
  df -h
  
  echo -e "\n=== Memory ==="
  free -h
} > diagnostic-report.txt

echo "Diagnostic report saved to diagnostic-report.txt"
```

### Resources

- **Documentation**: README.md, SETUP.md
- **Architecture**: ARCHITECTURE.md
- **Quick Reference**: QUICK-REFERENCE.md
- **Logs**: `docker-compose logs -f`
- **GitHub Webhook Logs**: Repository Settings → Webhooks → Recent Deliveries
- **OpenRouter Status**: https://status.openrouter.ai/
- **OpenRouter Support**: support@openrouter.ai

### Open an Issue

Include in your issue:
1. Symptom description
2. What you've tried
3. Relevant log excerpts (sanitize tokens!)
4. Diagnostic report (if applicable)
5. Environment details (OS, Docker version)

---

**Last Updated**: 2024-01-01
