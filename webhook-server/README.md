# Webhook Server for AI-Powered PR Review and Auto-Merge

This webhook server provides automated pull request review and merging capabilities using OpenRouter AI agents and the GitHub API.

## Features

- 🤖 **AI-Powered Code Review**: Uses OpenRouter (Claude, GPT-4, etc.) to analyze code changes
- 🔍 **Detailed Analysis**: Identifies security issues, bugs, style problems, and performance concerns
- ✅ **Auto-Merge**: Optionally auto-merge PRs that meet quality thresholds
- 🔐 **Secure**: Validates webhook signatures to ensure requests come from GitHub
- 📊 **Scoring System**: Provides quality scores (1-10) for each PR
- 🎯 **Customizable**: Configure review thresholds, models, and merge rules

## Architecture

```
GitHub Repository
        ↓
   Webhook Event (PR opened/updated)
        ↓
Your Homelab Server (webhook-server)
        ↓
OpenRouter AI (code analysis)
        ↓
GitHub API (post review, auto-merge)
```

## Prerequisites

- Python 3.9+
- Docker & Docker Compose (recommended)
- GitHub Personal Access Token with `repo` scope
- OpenRouter API key
- A publicly accessible server (or use ngrok for testing)

## Quick Start

### 1. Clone and Setup

```bash
cd webhook-server
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` with your credentials:

```bash
# Get GitHub token from: https://github.com/settings/tokens
GITHUB_TOKEN=ghp_your_token_here

# Generate a random secret: openssl rand -hex 32
GITHUB_WEBHOOK_SECRET=your_random_secret_here

# Get OpenRouter key from: https://openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-v1-your_key_here

# Choose your AI model
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
# Other options: openai/gpt-4-turbo, anthropic/claude-3-opus, etc.

# Auto-merge settings (set to true to enable)
AUTO_MERGE_ENABLED=false
REVIEW_THRESHOLD_SCORE=7
```

### 3. Deploy with Docker (Recommended)

```bash
# Build and start the server
docker-compose up -d

# Check logs
docker-compose logs -f

# Check health
curl http://localhost:5000/health
```

### 4. Alternative: Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```

### 5. Configure GitHub Webhook

1. Go to your repository on GitHub
2. Navigate to **Settings** > **Webhooks** > **Add webhook**
3. Configure:
   - **Payload URL**: `https://your-homelab-server.com:5000/webhook`
   - **Content type**: `application/json`
   - **Secret**: Same as `GITHUB_WEBHOOK_SECRET` in your `.env`
   - **Events**: Select "Pull requests"
   - **Active**: ✓ Checked
4. Click **Add webhook**

### 6. Test the Setup

1. Open a test PR in your repository
2. Check webhook server logs: `docker-compose logs -f`
3. Verify AI review appears as a comment on the PR
4. Check GitHub webhook delivery status in Settings > Webhooks

## Configuration Options

### AI Models

Available models on OpenRouter:

| Model | Description | Cost |
|-------|-------------|------|
| `anthropic/claude-3.5-sonnet` | Balanced quality and speed | $$ |
| `anthropic/claude-3-opus` | Highest quality | $$$ |
| `openai/gpt-4-turbo` | OpenAI's latest | $$ |
| `openai/gpt-3.5-turbo` | Fast and cheap | $ |
| `google/gemini-pro` | Google's model | $$ |

See [OpenRouter models](https://openrouter.ai/models) for full list.

### Auto-Merge Rules

The server auto-merges PRs when:

1. `AUTO_MERGE_ENABLED=true`
2. **AND** one of:
   - PR is from Dependabot, **OR**
   - AI review score >= `REVIEW_THRESHOLD_SCORE`
3. **AND** AI recommendation is `APPROVE`
4. **AND** No high-severity issues found

Customize in `.env`:

```bash
# Disable auto-merge (only review)
AUTO_MERGE_ENABLED=false

# Require score of 8+ for auto-merge
REVIEW_THRESHOLD_SCORE=8
```

### Review Categories

The AI analyzes code for:

- 🔴 **Security**: Vulnerabilities, exposed secrets, injection risks
- 🔴 **Bugs**: Logic errors, null pointer issues, race conditions
- 🟡 **Performance**: Inefficient algorithms, memory leaks, N+1 queries
- 🟢 **Style**: Code formatting, naming conventions, documentation

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service info |
| `/health` | GET | Health check |
| `/webhook` | POST | GitHub webhook handler |

## Homelab Deployment

### Using Docker Compose (Recommended)

1. **Ensure Docker is installed** on your homelab server:
   ```bash
   docker --version
   docker-compose --version
   ```

2. **Copy files to server**:
   ```bash
   scp -r webhook-server/ user@homelab-server:/opt/openleg-webhook/
   ```

3. **Configure on server**:
   ```bash
   ssh user@homelab-server
   cd /opt/openleg-webhook
   cp .env.example .env
   nano .env  # Edit with your credentials
   ```

4. **Start the service**:
   ```bash
   docker-compose up -d
   ```

5. **Set up auto-restart** (systemd):
   ```bash
   # Create systemd service
   sudo nano /etc/systemd/system/openleg-webhook.service
   ```

   Add:
   ```ini
   [Unit]
   Description=OpenLegislation Webhook Server
   Requires=docker.service
   After=docker.service

   [Service]
   Type=oneshot
   RemainAfterExit=yes
   WorkingDirectory=/opt/openleg-webhook
   ExecStart=/usr/bin/docker-compose up -d
   ExecStop=/usr/bin/docker-compose down
   TimeoutStartSec=0

   [Install]
   WantedBy=multi-user.target
   ```

   Enable:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable openleg-webhook
   sudo systemctl start openleg-webhook
   ```

### Exposing to Internet

#### Option 1: Nginx Reverse Proxy

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
    }
}
```

Then use Let's Encrypt for HTTPS:
```bash
sudo certbot --nginx -d webhook.yourdomain.com
```

#### Option 2: Cloudflare Tunnel (Recommended)

```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/

# Create tunnel
cloudflared tunnel create openleg-webhook

# Configure tunnel
cloudflared tunnel route dns openleg-webhook webhook.yourdomain.com

# Run tunnel
cloudflared tunnel --url http://localhost:5000 run openleg-webhook
```

#### Option 3: ngrok (Testing Only)

```bash
ngrok http 5000
```

Use the ngrok URL (e.g., `https://abc123.ngrok.io/webhook`) in GitHub webhook settings.

### Monitoring

#### View Logs

```bash
# Docker logs
docker-compose logs -f

# Or specific log files
tail -f logs/access.log
tail -f logs/error.log
```

#### Health Check

```bash
# Local
curl http://localhost:5000/health

# Remote
curl https://webhook.yourdomain.com/health
```

#### Monitor with cron

```bash
# Add to crontab
*/5 * * * * curl -f http://localhost:5000/health || echo "Webhook server down!" | mail -s "Alert" admin@example.com
```

## Security Best Practices

1. **Always use HTTPS** for webhook endpoint
2. **Keep webhook secret secure** - use strong random value
3. **Restrict GitHub token scope** - only `repo` permission needed
4. **Use firewall rules** to limit access to webhook port
5. **Rotate credentials regularly**
6. **Monitor logs** for suspicious activity
7. **Keep dependencies updated**: `docker-compose pull && docker-compose up -d`

## Troubleshooting

### Webhook not receiving events

1. Check GitHub webhook delivery history (Settings > Webhooks)
2. Verify firewall allows incoming traffic on port 5000
3. Test with curl: `curl -X POST https://your-server.com/webhook`
4. Check logs: `docker-compose logs -f`

### AI review not posting

1. Verify `GITHUB_TOKEN` has `repo` scope
2. Check OpenRouter API key is valid
3. Review error logs for API failures
4. Test OpenRouter connection manually

### Auto-merge not working

1. Ensure `AUTO_MERGE_ENABLED=true`
2. Verify GitHub repository allows auto-merge (Settings > General)
3. Check branch protection rules aren't blocking
4. Review webhook logs for merge attempt

### Server not starting

1. Check `.env` file exists and is valid
2. Verify port 5000 isn't already in use: `sudo lsof -i :5000`
3. Check Docker is running: `docker ps`
4. Review logs: `docker-compose logs`

## Advanced Usage

### Custom Review Prompts

Edit `app.py` and modify the `analyze_code_with_ai()` function to customize the AI prompt.

### Webhook Retries

GitHub automatically retries failed webhook deliveries. Check delivery history in webhook settings.

### Rate Limiting

Add rate limiting with Flask-Limiter:

```python
from flask_limiter import Limiter
limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/webhook', methods=['POST'])
@limiter.limit("10 per minute")
def webhook():
    # ...
```

### Multiple Repositories

The server can handle webhooks from multiple repositories. Just configure the webhook in each repo pointing to the same server.

### Custom Rules per Repository

Modify the `should_auto_merge()` function to add repository-specific logic:

```python
def should_auto_merge(pr_data: Dict[str, Any], review_data: Dict[str, Any]) -> bool:
    repo_name = pr_data['base']['repo']['full_name']
    
    # Different rules for different repos
    if repo_name == 'org/production-repo':
        return False  # Never auto-merge production
    
    # Default rules
    # ...
```

## Cost Estimates

### OpenRouter Usage

Typical costs per PR review:

- Small PR (< 500 lines): $0.01 - $0.05
- Medium PR (500-2000 lines): $0.05 - $0.20
- Large PR (> 2000 lines): $0.20 - $1.00

For 100 PRs/month with Claude 3.5 Sonnet: ~$5-20/month

### Server Costs

- Homelab: $0 (electricity only)
- VPS (DigitalOcean, Linode): $5-10/month
- Cloud (AWS, GCP): $10-30/month

## Alternatives and Integration

### With GitHub Actions

This webhook server complements GitHub Actions. Use both:

- **GitHub Actions**: CI/CD, testing, linting
- **Webhook Server**: AI code review, smart auto-merge

### With Other CI Systems

Works with any CI system. The webhook server is independent and uses GitHub API directly.

### Integration with Slack/Discord

Add notifications by installing webhook packages and modifying `post_review_comment()`:

```python
import requests

def notify_slack(pr_number, review_data):
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    message = {
        "text": f"PR #{pr_number} reviewed: {review_data['summary']}"
    }
    requests.post(webhook_url, json=message)
```

## Contributing

Contributions welcome! Areas for improvement:

- Support for other AI providers (Anthropic API direct, Hugging Face)
- Web dashboard for review history
- Slack/Discord integration
- Support for inline code comments
- ML model for predicting merge-ability

## License

Same as OpenLegislation - Dual BSD/GPL

## Support

- Check logs: `docker-compose logs -f`
- Test health endpoint: `curl http://localhost:5000/health`
- GitHub webhook deliveries: Repository Settings > Webhooks
- OpenRouter status: https://status.openrouter.ai/

## Credits

Built for OpenLegislation by @cbwinslow using:
- Flask web framework
- OpenRouter AI platform
- GitHub API
- Docker containerization
