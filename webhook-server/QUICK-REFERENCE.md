# Webhook Server Quick Reference

## URLs

- **Health Check**: `GET /health`
- **Webhook Endpoint**: `POST /webhook`
- **Service Info**: `GET /`

## Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GITHUB_TOKEN` | Yes | GitHub PAT with `repo` scope | `ghp_xxxx...` |
| `GITHUB_WEBHOOK_SECRET` | Yes | Secret for webhook signature validation | `abc123...` |
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key | `sk-or-v1-xxx...` |
| `OPENROUTER_MODEL` | No | AI model to use | `anthropic/claude-3.5-sonnet` |
| `PORT` | No | Server port (default: 5000) | `5000` |
| `DEBUG` | No | Enable debug mode | `false` |
| `AUTO_MERGE_ENABLED` | No | Enable auto-merge | `false` |
| `REVIEW_THRESHOLD_SCORE` | No | Min score for auto-merge | `7` |

## Quick Start Commands

```bash
# Setup
cd webhook-server
cp .env.example .env
# Edit .env with your credentials

# Deploy with Docker
docker-compose up -d

# View logs
docker-compose logs -f

# Test
curl http://localhost:5000/health

# Stop
docker-compose down
```

## AI Models Available

| Model | Speed | Quality | Cost | Use Case |
|-------|-------|---------|------|----------|
| `anthropic/claude-3.5-sonnet` | Fast | High | $$ | Recommended default |
| `anthropic/claude-3-opus` | Slow | Highest | $$$ | Critical reviews |
| `openai/gpt-4-turbo` | Medium | High | $$ | Alternative to Claude |
| `openai/gpt-3.5-turbo` | Fastest | Good | $ | High volume/cost savings |
| `google/gemini-pro` | Fast | Good | $$ | Google ecosystem |

See full list: https://openrouter.ai/models

## Review Response Format

```json
{
  "recommendation": "APPROVE|REQUEST_CHANGES|COMMENT",
  "score": 8,
  "summary": "Brief summary",
  "issues": [
    {
      "severity": "high|medium|low",
      "category": "security|bug|style|performance",
      "description": "Issue description",
      "file": "path/to/file.java",
      "line": 42
    }
  ],
  "positives": ["Good thing 1", "Good thing 2"],
  "suggestions": ["Suggestion 1", "Suggestion 2"]
}
```

## Auto-Merge Logic

PR will auto-merge if:
1. `AUTO_MERGE_ENABLED=true`
2. **AND** (PR from Dependabot **OR** score >= threshold)
3. **AND** recommendation is `APPROVE`
4. **AND** no high-severity issues

## Common Tasks

### Update AI Model
```bash
# Edit .env
OPENROUTER_MODEL=openai/gpt-4-turbo

# Restart
docker-compose restart
```

### View Logs
```bash
# Container logs
docker-compose logs -f

# Access logs
docker-compose exec webhook-server tail -f /app/logs/access.log

# Error logs
docker-compose exec webhook-server tail -f /app/logs/error.log
```

### Update Server
```bash
git pull
docker-compose build
docker-compose up -d
```

### Backup Configuration
```bash
cp .env .env.backup
tar -czf webhook-backup-$(date +%Y%m%d).tar.gz .env logs/
```

### Monitor Health
```bash
# Manual check
curl http://localhost:5000/health

# With watch (every 10s)
watch -n 10 curl -s http://localhost:5000/health

# Add to cron (every 5 min)
*/5 * * * * curl -f http://localhost:5000/health || echo "Webhook down!" | mail -s "Alert" admin@example.com
```

## GitHub Webhook Configuration

**Repository Settings → Webhooks → Add webhook**

- **Payload URL**: `https://your-domain.com/webhook`
- **Content type**: `application/json`
- **Secret**: Value from `GITHUB_WEBHOOK_SECRET` in .env
- **Events**: Select "Pull requests" only
- **Active**: ✓

## Testing

### Test Health Endpoint
```bash
curl http://localhost:5000/health
# Expected: {"status":"healthy","timestamp":"...","version":"1.0.0"}
```

### Test Webhook (with test script)
```bash
cd webhook-server
python3 test_webhook.py
```

### Test Webhook (manual curl)
```bash
# Note: Replace SECRET with your actual webhook secret
PAYLOAD='{"action":"opened","pull_request":{"number":1}}'
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "SECRET" | awk '{print "sha256="$2}')

curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -H "X-Hub-Signature-256: $SIGNATURE" \
  -d "$PAYLOAD"
```

## Troubleshooting

### Server won't start
```bash
# Check if port is in use
sudo lsof -i :5000

# Check Docker
docker-compose ps
docker-compose logs

# Validate .env
cat .env | grep -E "GITHUB_TOKEN|OPENROUTER_API_KEY"
```

### Webhook returns 403
- Check webhook secret matches between GitHub and .env
- Verify signature validation in GitHub webhook delivery logs

### AI review not posting
- Check GitHub token has `repo` scope: `curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user`
- Check OpenRouter key: https://openrouter.ai/playground
- Review logs: `docker-compose logs -f | grep -i error`

### Auto-merge not working
- Verify `AUTO_MERGE_ENABLED=true` in .env
- Check repository settings: "Allow auto-merge" enabled
- Check branch protection rules
- Review server logs for merge attempt

## Cost Estimation

### Per PR Review (Claude 3.5 Sonnet)
- Small PR (< 500 lines): $0.01 - $0.05
- Medium PR (500-2000 lines): $0.05 - $0.20
- Large PR (> 2000 lines): $0.20 - $1.00

### Monthly (Claude 3.5 Sonnet)
- 100 PRs/month: $5 - $20
- 500 PRs/month: $25 - $100

### Cost Reduction Tips
1. Use `openai/gpt-3.5-turbo` (70% cheaper)
2. Skip trivial PRs (docs-only, whitespace)
3. Truncate large diffs (already done)

## Architecture

```
GitHub → Webhook Event → Your Server → OpenRouter AI → Analysis
                              ↓
                         GitHub API
                              ↓
                    Post Review Comment
                              ↓
                      (Optional) Auto-Merge
```

## Files Reference

| File | Purpose |
|------|---------|
| `app.py` | Main Flask application |
| `Dockerfile` | Container image |
| `docker-compose.yml` | Deployment config |
| `requirements.txt` | Python dependencies |
| `.env` | Configuration (not in git) |
| `.env.example` | Configuration template |
| `deploy.sh` | Deployment automation |
| `test_webhook.py` | Test suite |
| `openleg-webhook.service` | Systemd service |
| `README.md` | Full documentation |
| `SETUP.md` | Setup instructions |

## Support Resources

- **Documentation**: README.md and SETUP.md
- **Logs**: `docker-compose logs -f`
- **GitHub Webhooks**: Repository Settings → Webhooks
- **OpenRouter**: https://openrouter.ai/dashboard
- **OpenRouter Status**: https://status.openrouter.ai/

## Security Checklist

- [ ] HTTPS enabled (not HTTP)
- [ ] Strong webhook secret (32+ chars)
- [ ] Minimal GitHub token scopes
- [ ] `.env` permissions restricted (600)
- [ ] Firewall configured
- [ ] Regular updates scheduled
- [ ] Logs monitored
- [ ] SSL certificate valid

---

**Last Updated**: 2024-01-01
**Version**: 1.0.0
