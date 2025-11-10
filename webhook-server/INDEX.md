# Webhook Server Documentation Index

Welcome to the AI-Powered PR Review Webhook Server documentation!

## 📚 Documentation Guide

Choose the document that matches your needs:

### 🚀 Getting Started

**[GETTING-STARTED.md](GETTING-STARTED.md)** - **START HERE**
- 5-minute quick start guide
- Step-by-step setup instructions
- For first-time users
- Includes credential setup, deployment, and testing

### 📖 Core Documentation

**[README.md](README.md)** - **Feature Overview**
- What the webhook server does
- Features and capabilities
- Architecture overview
- Use cases and benefits
- Configuration options

**[SETUP.md](SETUP.md)** - **Detailed Setup Guide**
- Complete deployment instructions
- Multiple deployment methods (Docker, manual, cloud)
- Network configuration (Cloudflare, Nginx, etc.)
- Security best practices
- Monitoring and maintenance

### 🔧 Reference Materials

**[QUICK-REFERENCE.md](QUICK-REFERENCE.md)** - **Command Reference**
- Environment variables
- Common commands
- API endpoints
- AI models list
- Quick troubleshooting

**[ARCHITECTURE.md](ARCHITECTURE.md)** - **System Architecture**
- Technical architecture diagrams
- Data flow explanations
- Component details
- Integration points
- Scaling considerations

### 🔍 Troubleshooting

**[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - **Problem Solving**
- Common issues and solutions
- Diagnostic commands
- Error message explanations
- Performance optimization
- Security hardening

## 📂 File Overview

### Application Files
- `app.py` - Main Flask application
- `requirements.txt` - Python dependencies
- `.env.example` - Configuration template
- `.gitignore` - Git exclusions

### Deployment Files
- `Dockerfile` - Container image definition
- `docker-compose.yml` - Docker deployment config
- `deploy.sh` - Automated deployment script
- `openleg-webhook.service` - Systemd service file

### Testing & Validation
- `test_webhook.py` - Test suite for webhook functionality
- `validate.sh` - Setup validation script

## 🎯 Quick Navigation

### I want to...

**Deploy the webhook server for the first time**
→ Read [GETTING-STARTED.md](GETTING-STARTED.md)

**Understand what this does**
→ Read [README.md](README.md)

**Learn about deployment options**
→ Read [SETUP.md](SETUP.md)

**Find a specific command**
→ Read [QUICK-REFERENCE.md](QUICK-REFERENCE.md)

**Understand how it works internally**
→ Read [ARCHITECTURE.md](ARCHITECTURE.md)

**Fix a problem**
→ Read [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**Customize the code**
→ Read [README.md](README.md) → "Advanced Usage" section

**Deploy to production**
→ Read [SETUP.md](SETUP.md) → "Homelab Deployment" section

**Reduce costs**
→ Read [QUICK-REFERENCE.md](QUICK-REFERENCE.md) → "Cost Estimation" section

**Monitor the system**
→ Read [SETUP.md](SETUP.md) → "Monitoring" section

**Secure my deployment**
→ Read [SETUP.md](SETUP.md) → "Security Best Practices" section

## 🔄 Typical Workflow

### First-Time Setup
1. **GETTING-STARTED.md** - Follow the quick start guide
2. **README.md** - Understand features and options
3. **Test** - Create a test PR and verify it works
4. **SETUP.md** - Review detailed setup for production deployment

### Day-to-Day Usage
1. **QUICK-REFERENCE.md** - Look up commands as needed
2. **Monitor** - Check logs and health endpoint
3. **TROUBLESHOOTING.md** - Refer to when issues arise

### Advanced Configuration
1. **ARCHITECTURE.md** - Understand system internals
2. **Modify app.py** - Customize behavior
3. **SETUP.md** - Deploy changes

## 📊 Document Sizes

| Document | Size | Reading Time |
|----------|------|--------------|
| GETTING-STARTED.md | 11 KB | 15 min |
| README.md | 12 KB | 20 min |
| SETUP.md | 14 KB | 30 min |
| QUICK-REFERENCE.md | 7 KB | 10 min |
| ARCHITECTURE.md | 11 KB | 20 min |
| TROUBLESHOOTING.md | 12 KB | 25 min |

**Total documentation:** ~70 KB, ~2 hours of reading

## 🆘 Need Help?

### Check These First
1. **Health endpoint:** `curl http://localhost:5000/health`
2. **Server logs:** `docker-compose logs -f`
3. **GitHub webhook deliveries:** Repository Settings → Webhooks
4. **TROUBLESHOOTING.md:** Common issues and solutions

### Still Stuck?
1. Collect diagnostic info:
   ```bash
   docker-compose logs > webhook-logs.txt
   cat .env | grep -v "TOKEN\|SECRET\|KEY" > config-sanitized.txt
   ```
2. Open an issue with:
   - What you're trying to do
   - What's happening instead
   - Relevant logs (sanitize tokens!)
   - Steps you've already tried

## 🔐 Security Notes

**Before deploying:**
- ✅ Review [SETUP.md](SETUP.md) → "Security Best Practices"
- ✅ Use HTTPS (not HTTP)
- ✅ Keep credentials in .env (not in code)
- ✅ Set `.env` permissions to 600
- ✅ Use strong webhook secret (32+ chars)
- ✅ Limit GitHub token scopes to `repo` only

## 📋 Checklist for Production

Before going live, verify:

### Configuration
- [ ] `.env` file created with real credentials
- [ ] GitHub token has `repo` scope
- [ ] OpenRouter API key is valid and has credits
- [ ] Webhook secret is strong (32+ chars)
- [ ] AI model is appropriate for your needs
- [ ] Auto-merge settings match your policy

### Deployment
- [ ] Docker and docker-compose installed
- [ ] Server is running (`docker-compose ps`)
- [ ] Health check passes (`curl http://localhost:5000/health`)
- [ ] Server is accessible from internet
- [ ] HTTPS is enabled (not HTTP)
- [ ] Logs are being written

### GitHub
- [ ] Webhook is configured in repository
- [ ] Webhook secret matches .env
- [ ] Webhook URL is correct (ends with /webhook)
- [ ] "Pull requests" event is selected
- [ ] Webhook delivery shows green checkmark
- [ ] Test PR received AI review

### Monitoring
- [ ] Can view logs: `docker-compose logs -f`
- [ ] Can check health: `curl https://webhook.yourdomain.com/health`
- [ ] GitHub webhook deliveries are being recorded
- [ ] OpenRouter dashboard shows API usage

### Security
- [ ] Using HTTPS (not HTTP)
- [ ] .env file permissions are 600
- [ ] Webhook signature validation is working
- [ ] No tokens in logs
- [ ] Firewall rules are configured

## 🎓 Learning Path

### Beginner
1. Read GETTING-STARTED.md
2. Deploy with Docker
3. Test with a PR
4. Read README.md for features

### Intermediate
1. Review SETUP.md for deployment options
2. Configure Cloudflare Tunnel or Nginx
3. Enable auto-merge
4. Read ARCHITECTURE.md

### Advanced
1. Modify app.py for custom logic
2. Add Slack/Discord integration
3. Set up monitoring (Prometheus, etc.)
4. Scale with multiple workers

## 🌟 Key Features

- **AI-Powered Reviews**: Uses OpenRouter (Claude, GPT-4, etc.)
- **Auto-Merge**: Optional automatic PR merging
- **Secure**: Webhook signature verification
- **Flexible**: Multiple deployment options
- **Well-Documented**: 6 comprehensive guides
- **Production-Ready**: Docker, systemd, monitoring
- **Cost-Effective**: $5-20/month for typical usage

## 📈 What to Expect

### Week 1
- Deploy and test
- Review a few PRs manually
- Adjust AI model if needed
- Monitor costs

### Week 2-4
- All PRs get AI reviews
- Start trusting automation more
- Enable auto-merge for simple PRs
- Optimize settings

### Month 2+
- System runs on autopilot
- Focus on high-value PR reviews
- Expand to more repositories
- Share with team

## 🤝 Contributing

To improve this webhook server:

1. **Documentation**: Suggest improvements or fix typos
2. **Features**: Add new capabilities (custom rules, integrations)
3. **Bug Fixes**: Report and fix issues
4. **Examples**: Share your deployment stories

## 📝 Version History

**v1.0.0** (Current)
- Initial release
- Flask-based webhook server
- OpenRouter AI integration
- Docker deployment
- Comprehensive documentation

## 📜 License

Same as OpenLegislation repository - Dual BSD/GPL

## 🙏 Acknowledgments

Built with:
- Flask web framework
- OpenRouter AI platform
- GitHub API
- Docker containerization
- Community best practices

---

**Last Updated:** 2024-01-01  
**Maintained By:** @cbwinslow  
**Repository:** OpenLegislation-local-dev

**Questions?** Open an issue with `webhook` label  
**Working well?** Star the repo and share your experience!
