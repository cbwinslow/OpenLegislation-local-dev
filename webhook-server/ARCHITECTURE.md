# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          GitHub Repository                           │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Pull       │  │   Code       │  │   Reviews    │              │
│  │   Request    │  │   Changes    │  │   Comments   │              │
│  └──────┬───────┘  └──────────────┘  └──────▲───────┘              │
│         │                                     │                      │
└─────────┼─────────────────────────────────────┼──────────────────────┘
          │                                     │
          │ 1. Webhook Event                    │ 4. Post Review
          │ (PR opened/updated)                 │    Comment
          ▼                                     │
┌─────────────────────────────────────────────────────────────────────┐
│                     Your Homelab Server                              │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                  Webhook Server (Flask)                       │ │
│  │                                                               │ │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │ │
│  │  │  Webhook    │  │   Security   │  │   GitHub     │       │ │
│  │  │  Handler    │─▶│  Validation  │─▶│   API        │       │ │
│  │  └─────────────┘  └──────────────┘  │   Client     │       │ │
│  │                                      └──────┬───────┘       │ │
│  │                                             │               │ │
│  │  ┌─────────────────────────────────────────▼─────────────┐ │ │
│  │  │           PR Analysis Workflow                         │ │ │
│  │  │                                                         │ │ │
│  │  │  1. Fetch PR diff & files                              │ │ │
│  │  │  2. Prepare context for AI                             │ │ │
│  │  │  3. Send to OpenRouter                                 │ │ │
│  │  │  4. Parse AI response                                  │ │ │
│  │  │  5. Format review comment                              │ │ │
│  │  │  6. Post to GitHub                                     │ │ │
│  │  │  7. Check auto-merge criteria                          │ │ │
│  │  └─────────────────────────────────────────┬─────────────┘ │ │
│  │                                             │               │ │
│  └─────────────────────────────────────────────┼───────────────┘ │
│                                                │                   │
│  ┌─────────────────────────────────────────────▼───────────────┐ │
│  │                   Docker Container                          │ │
│  │                                                             │ │
│  │  • Python 3.11                                              │ │
│  │  • Flask web server                                         │ │
│  │  • Gunicorn (4 workers)                                     │ │
│  │  • Environment config (.env)                                │ │
│  │  • Log files                                                │ │
│  └─────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────┼───────────────────────────────┘
                                    │ 2. API Request
                                    │ 3. AI Analysis
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         OpenRouter Platform                          │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Claude     │  │    GPT-4     │  │   Gemini     │              │
│  │   3.5        │  │    Turbo     │  │    Pro       │              │
│  │   Sonnet     │  │              │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
│  • Code analysis                                                     │
│  • Security scanning                                                 │
│  • Best practices check                                              │
│  • Quality scoring                                                   │
└───────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. PR Opened/Updated
```
Developer → Pushes Code → GitHub → Triggers Webhook
```

### 2. Webhook Processing
```
GitHub Webhook → Your Server → Validates Signature → Accepts Request
                                      ↓
                                Signature Invalid → Reject (403)
```

### 3. PR Analysis
```
Server → Fetch PR Data (diff, files, metadata)
       ↓
     Prepare AI Prompt (context + code changes)
       ↓
     Send to OpenRouter (via API)
       ↓
     Receive AI Analysis (JSON response)
       ↓
     Parse Results (score, issues, suggestions)
```

### 4. Review Posting
```
Server → Format Review Comment (markdown)
       ↓
     Post to GitHub (via GitHub API)
       ↓
     Comment Appears on PR
```

### 5. Auto-Merge Decision (if enabled)
```
Check Criteria:
  • AUTO_MERGE_ENABLED = true?
  • Score >= threshold?
  • Recommendation = APPROVE?
  • No high-severity issues?
        ↓
    All Yes → Merge PR
        ↓
       No → Wait for manual review
```

## Component Details

### Flask Application (app.py)

```
app.py
├── Configuration (from .env)
│   ├── GitHub credentials
│   ├── OpenRouter API key
│   └── Auto-merge settings
│
├── Endpoints
│   ├── GET  /         → Service info
│   ├── GET  /health   → Health check
│   └── POST /webhook  → Main webhook handler
│
├── Core Functions
│   ├── verify_signature()      → Security
│   ├── get_pr_diff()           → GitHub API
│   ├── get_pr_files()          → GitHub API
│   ├── analyze_code_with_ai()  → OpenRouter API
│   ├── post_review_comment()   → GitHub API
│   ├── should_auto_merge()     → Decision logic
│   └── merge_pr()              → GitHub API
│
└── Error Handling
    ├── Invalid signature → 403
    ├── API errors → Log & continue
    └── Unexpected errors → 500
```

### Docker Stack

```
docker-compose.yml
└── webhook-server service
    ├── Build: Dockerfile
    ├── Ports: 5000:5000
    ├── Env: .env file
    ├── Volumes: ./logs
    ├── Restart: unless-stopped
    └── Health check: /health endpoint
```

## Security Model

### Webhook Signature Verification

```
GitHub → Creates HMAC-SHA256 signature
       ↓
     Sends in X-Hub-Signature-256 header
       ↓
     Server recalculates signature
       ↓
     Compares (constant-time comparison)
       ↓
     Match? → Process request
       ↓
     No match? → Reject with 403
```

### API Authentication

```
GitHub API:
  • Personal Access Token
  • Scopes: repo (read/write)
  • Sent in Authorization header

OpenRouter API:
  • API Key
  • Sent in Authorization header
  • Supports rate limiting
```

## Deployment Options

### Option 1: Docker (Recommended)
```
Your Server
├── Docker Engine
│   └── webhook-server container
│       ├── Flask app
│       ├── Gunicorn
│       └── Python environment
└── Reverse Proxy (optional)
    ├── Nginx
    ├── Cloudflare Tunnel
    └── or Direct exposure
```

### Option 2: Manual Python
```
Your Server
├── Python 3.9+
├── Virtual environment
│   ├── Flask
│   ├── Dependencies
│   └── Application code
└── Process Manager
    ├── Systemd
    └── or Supervisor
```

## Network Topology

### With Cloudflare Tunnel (Recommended)
```
GitHub → Cloudflare CDN → Tunnel → localhost:5000
         (HTTPS)           (encrypted)  (webhook-server)
```

### With Nginx Reverse Proxy
```
GitHub → Your Domain → Nginx → localhost:5000
         (HTTPS)       (443)    (webhook-server)
                        ↓
                    Let's Encrypt
```

### Direct Exposure (Testing)
```
GitHub → Your Public IP:5000 → webhook-server
         (HTTP/HTTPS)
```

## Scaling Considerations

### Single Server (Current)
- Handles: ~1000 PRs/day
- Response time: 5-30 seconds per PR
- Cost: $5-30/month (OpenRouter)

### Future Scaling (if needed)
```
Load Balancer
├── Webhook Server 1
├── Webhook Server 2
└── Webhook Server 3
    ↓
Queue System (Redis/RabbitMQ)
    ↓
Worker Pool
├── Worker 1
├── Worker 2
└── Worker 3
```

## Monitoring & Observability

### Logs
```
Docker Container
├── STDOUT (docker logs)
├── /app/logs/access.log
└── /app/logs/error.log
```

### Metrics (via Health Check)
```
GET /health
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "version": "1.0.0"
}
```

### GitHub Webhook Status
```
Repository Settings → Webhooks → Recent Deliveries
├── Request timestamp
├── Response status
├── Request payload
└── Response body
```

## Integration Points

### GitHub API Endpoints Used
- `GET /repos/{owner}/{repo}/pulls/{number}` - Get PR diff
- `GET /repos/{owner}/{repo}/pulls/{number}/files` - Get changed files
- `POST /repos/{owner}/{repo}/pulls/{number}/reviews` - Post review
- `PUT /repos/{owner}/{repo}/pulls/{number}/merge` - Merge PR

### OpenRouter API
- `POST /api/v1/chat/completions` - AI code analysis
- Compatible with OpenAI API format

## Error Handling Flow

```
Webhook Received
    ↓
Signature Valid? → No → Return 403
    ↓ Yes
Event Type = PR? → No → Return 200 (ignore)
    ↓ Yes
Fetch PR Data → Error? → Log error, return 500
    ↓ Success
Call OpenRouter → Error? → Log, use fallback response
    ↓ Success
Post Review → Error? → Log error, return 500
    ↓ Success
Check Auto-Merge → Error? → Log, skip merge
    ↓
Return 200
```

## Configuration Matrix

| Feature | Disabled | Enabled | Effect |
|---------|----------|---------|--------|
| Auto-merge | `false` | `true` | PRs can be auto-merged |
| Debug mode | `false` | `true` | Verbose logging |
| High threshold | `score=7` | `score=9` | Stricter auto-merge |

## Dependencies Graph

```
webhook-server
├── flask (web framework)
├── python-dotenv (config)
├── requests (HTTP client)
├── openai (OpenRouter SDK)
└── gunicorn (production server)
```

---

**Architecture Version**: 1.0.0  
**Last Updated**: 2024-01-01
