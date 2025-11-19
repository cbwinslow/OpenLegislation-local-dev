# Getting Started with Webhook Server

**5-Minute Quick Start Guide**

Welcome! This guide will get your AI-powered PR review webhook server up and running quickly.

## What You'll Build

A self-hosted webhook server that:
- ✅ Receives GitHub webhook events when PRs are opened/updated
- ✅ Analyzes code changes using AI (Claude, GPT-4, etc.)
- ✅ Posts detailed review comments on PRs
- ✅ Optionally auto-merges PRs that meet quality standards

## Prerequisites

Before starting, ensure you have:

- [ ] A Linux server (homelab, VPS, or cloud instance)
- [ ] Docker installed (or ability to install it)
- [ ] GitHub account with admin access to a repository
- [ ] OpenRouter account (sign up at https://openrouter.ai)
- [ ] Domain name (optional but recommended for HTTPS)

**Time Required:** 30-45 minutes for first-time setup

## Step 1: Get Your Credentials

### 1.1 GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: "Webhook Server"
4. Scopes: Check **only** `repo` (all sub-items)
5. Click "Generate token"
6. **Copy the token** (starts with `ghp_`) - you won't see it again!

### 1.2 OpenRouter API Key

1. Go to https://openrouter.ai/keys
2. Click "Create Key"
3. Name: "OpenLegislation Webhook"
4. **Copy the key** (starts with `sk-or-v1-`)
5. Add $5-10 credits to your account (Settings → Billing)

### 1.3 Webhook Secret

Generate a random secret:

```bash
openssl rand -hex 32
```

Copy the output - this is your webhook secret.

## Step 2: Deploy to Your Server

### 2.1 Connect to Server

```bash
ssh user@your-server.com
```

### 2.2 Install Docker (if needed)

```bash
# Run this if Docker isn't installed
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
exit
ssh user@your-server.com
```

### 2.3 Download Webhook Server

```bash
# Create directory
mkdir -p /opt/openleg-webhook
cd /opt/openleg-webhook

# Option A: Clone full repository
git clone https://github.com/cbwinslow/OpenLegislation-local-dev.git
cd OpenLegislation-local-dev/webhook-server

# Option B: Or copy files from your local machine
# (From your local terminal)
# cd /path/to/OpenLegislation-local-dev
# scp -r webhook-server/* user@your-server.com:/opt/openleg-webhook/
```

### 2.4 Configure Environment

```bash
cd /opt/openleg-webhook  # or wherever you placed files
cp .env.example .env
nano .env  # or use vim, emacs, etc.
```

Fill in your credentials:

```bash
# Paste your GitHub token (from step 1.1)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Paste your webhook secret (from step 1.3)
GITHUB_WEBHOOK_SECRET=your_64_character_hex_string_here

# Paste your OpenRouter key (from step 1.2)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Choose your AI model (optional, this is the default)
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Keep auto-merge disabled for now
AUTO_MERGE_ENABLED=false
REVIEW_THRESHOLD_SCORE=7
```

Save and exit (Ctrl+X, then Y, then Enter in nano).

### 2.5 Start the Server

```bash
# Option A: Use the deploy script
./deploy.sh

# Option B: Or manually with docker-compose
docker-compose up -d
```

### 2.6 Verify It's Running

```bash
# Check container status
docker-compose ps
# Should show: State: Up

# Test health endpoint
curl http://localhost:5000/health
# Should return: {"status":"healthy",...}

# View logs
docker-compose logs -f
# Press Ctrl+C to exit logs
```

If you see "healthy" and no errors in logs, you're good to go! 🎉

## Step 3: Expose to Internet

Your server needs to be accessible from GitHub. Choose one method:

### Option A: Cloudflare Tunnel (Recommended - Free & Secure)

**Best for:** Most users, no port forwarding needed

```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/

# Authenticate (opens browser)
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create openleg-webhook

# Configure tunnel
mkdir -p ~/.cloudflared
nano ~/.cloudflared/config.yml
```

Add this content (replace with your tunnel ID from previous command):

```yaml
tunnel: openleg-webhook
credentials-file: /home/youruser/.cloudflared/YOUR-TUNNEL-ID.json

ingress:
  - hostname: webhook.yourdomain.com
    service: http://localhost:5000
  - service: http_status:404
```

```bash
# Route DNS
cloudflared tunnel route dns openleg-webhook webhook.yourdomain.com

# Install as service
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared

# Test
curl https://webhook.yourdomain.com/health
```

**Your webhook URL:** `https://webhook.yourdomain.com/webhook`

### Option B: ngrok (Testing - Easiest but Temporary)

**Best for:** Quick testing, demos

```bash
# Install ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/

# Get free auth token from https://dashboard.ngrok.com/
ngrok config add-authtoken YOUR_NGROK_TOKEN

# Start tunnel
ngrok http 5000
```

Copy the `https://` URL shown (e.g., `https://abc123.ngrok.io`)

**Your webhook URL:** `https://abc123.ngrok.io/webhook`

⚠️ **Note:** Free ngrok URLs change when you restart. For production, use Cloudflare Tunnel.

### Option C: Direct (Advanced)

See SETUP.md for Nginx reverse proxy configuration.

## Step 4: Configure GitHub Webhook

1. **Go to your repository** on GitHub

2. **Click Settings** (repository settings, not account settings)

3. **Click Webhooks** (in left sidebar)

4. **Click "Add webhook"**

5. **Configure webhook:**

   | Field | Value |
   |-------|-------|
   | **Payload URL** | Your URL from Step 3 (e.g., `https://webhook.yourdomain.com/webhook`) |
   | **Content type** | `application/json` |
   | **Secret** | Your webhook secret from .env (the 64-char hex string) |
   | **SSL verification** | Enable SSL verification |
   | **Which events?** | "Let me select individual events" |
   | **Events** | ✅ Pull requests (uncheck everything else) |
   | **Active** | ✅ Check this box |

6. **Click "Add webhook"**

7. **Verify webhook is working:**
   - You'll see a green checkmark next to the webhook
   - Click on the webhook
   - Click "Recent Deliveries"
   - You should see a "ping" event with 200 response

## Step 5: Test with a Real PR

### 5.1 Create Test PR

```bash
# Clone your repository
git clone https://github.com/yourusername/your-repo.git
cd your-repo

# Create test branch
git checkout -b test-webhook-review

# Make a small change
echo "// Test webhook" >> README.md

# Commit and push
git add README.md
git commit -m "Test webhook review"
git push origin test-webhook-review
```

### 5.2 Open Pull Request

1. Go to your repository on GitHub
2. Click "Pull requests" → "New pull request"
3. Select `test-webhook-review` branch
4. Click "Create pull request"
5. Add title: "Test: Webhook review"
6. Click "Create pull request"

### 5.3 Verify AI Review

Within 30-60 seconds, you should see:

1. **On GitHub PR:** A new comment from your account with:
   - 🤖 AI-Powered Code Review header
   - Overall assessment (APPROVE/REQUEST_CHANGES/COMMENT)
   - Quality score (1-10)
   - Analysis of changes

2. **In server logs:**
   ```bash
   docker-compose logs -f
   ```
   You should see:
   - "Processing PR #X"
   - "Analyzing PR #X with AI"
   - "Posting review for PR #X"

3. **In GitHub webhook deliveries:**
   - Settings → Webhooks → Recent Deliveries
   - Click on the latest delivery
   - Response should be 200

## Step 6: Enable Auto-Merge (Optional)

⚠️ **Only enable if you understand the implications!**

### 6.1 Enable in GitHub

1. Repository Settings → General
2. Scroll to "Pull Requests" section
3. ✅ Check "Allow auto-merge"
4. Save

### 6.2 Enable in Webhook Server

```bash
nano /opt/openleg-webhook/.env

# Change this line:
AUTO_MERGE_ENABLED=true

# Save and restart
docker-compose restart
```

### 6.3 Configure Branch Protection (Recommended)

1. Repository Settings → Branches
2. Add rule for `main` branch:
   - ✅ Require pull request reviews (1 approval)
   - ✅ Require status checks to pass
3. Save

Now PRs with:
- Score ≥ 7
- AI recommendation = APPROVE
- No high-severity issues

Will automatically merge after CI checks pass!

## You're Done! 🎉

Your webhook server is now:
- ✅ Receiving GitHub PR events
- ✅ Analyzing code with AI
- ✅ Posting review comments
- ✅ (Optional) Auto-merging quality PRs

## What's Next?

### Monitor Your Setup

```bash
# View live logs
docker-compose logs -f

# Check health
curl https://webhook.yourdomain.com/health

# Check GitHub webhook deliveries
# Repository Settings → Webhooks → Recent Deliveries
```

### Customize

- **Try different AI models:** Edit `OPENROUTER_MODEL` in .env
- **Adjust auto-merge threshold:** Change `REVIEW_THRESHOLD_SCORE`
- **Skip certain PRs:** Edit logic in app.py

### Cost Management

- **Monitor usage:** https://openrouter.ai/dashboard
- **Typical costs:** $5-20/month for 100 PRs
- **Optimize:** See QUICK-REFERENCE.md for tips

### Expand

- Add webhook to more repositories
- Integrate with Slack/Discord
- Create custom review rules

## Getting Help

### Troubleshooting

If something isn't working, check:

1. **Server logs:** `docker-compose logs -f`
2. **GitHub webhook deliveries:** Settings → Webhooks → Recent Deliveries
3. **TROUBLESHOOTING.md** in this directory
4. **Test health endpoint:** `curl http://localhost:5000/health`

### Common Issues

| Problem | Solution |
|---------|----------|
| Webhook returns 403 | Check webhook secret matches |
| No review posted | Verify GitHub token and OpenRouter key |
| Server won't start | Check .env file syntax, port availability |
| Can't reach server | Check firewall, reverse proxy config |

### Documentation

- **README.md** - Feature overview
- **SETUP.md** - Detailed deployment guide
- **QUICK-REFERENCE.md** - Command reference
- **ARCHITECTURE.md** - System architecture
- **TROUBLESHOOTING.md** - Common issues and solutions

### Support

- Open an issue in the repository with `webhook` label
- Include logs (sanitize tokens!)
- Describe what you tried

## Checklist

Use this to track your progress:

- [ ] Got GitHub Personal Access Token
- [ ] Got OpenRouter API Key
- [ ] Generated webhook secret
- [ ] Installed Docker on server
- [ ] Deployed webhook server
- [ ] Created .env file with credentials
- [ ] Server is running (health check passes)
- [ ] Exposed server to internet
- [ ] Configured GitHub webhook
- [ ] Tested with a PR
- [ ] Saw AI review comment on PR
- [ ] (Optional) Enabled auto-merge

## Success Metrics

After 1 week, you should see:

- 📈 All PRs getting AI reviews within 60 seconds
- 📊 Consistent review quality (scores 6-9 typically)
- 💰 OpenRouter costs: $1-5 depending on volume
- ⏱️ Faster PR merge times
- 🐛 Fewer bugs making it to main

---

**Congratulations!** You've successfully deployed an AI-powered code review system! 🚀

**Questions?** Check the documentation or open an issue.

**Working well?** Consider expanding to more repositories!
