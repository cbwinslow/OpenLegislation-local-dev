# 🤖 OpenLegislation Automation & CI/CD Setup Guide

## Overview

This repository features a comprehensive automation suite that leverages GitHub Actions, webhooks, and AI-powered tools to streamline development, code review, project management, and deployment processes.

## 🏗️ Architecture

```
GitHub Repository
├── 🤖 AI Agents (CrewAI)
├── 🔄 GitHub Actions Workflows
├── 🪝 Webhook Server (AI Review & Automation)
├── 📊 Projects v2 (Issue/Project Tracking)
└── 🚀 CI/CD Pipeline (Build/Test/Deploy)
```

## 🚀 Quick Start

### 1. Enable Required GitHub Features

1. **Projects v2**: Enable Projects in repository settings
2. **Webhooks**: Configure webhook endpoint for AI automation
3. **Actions**: Ensure GitHub Actions are enabled
4. **Copilot**: Enable GitHub Copilot for the repository

### 2. Set Up Webhook Server

```bash
cd webhook-server
cp .env.example .env
# Edit .env with your tokens
docker-compose up -d
```

### 3. Configure Repository Settings

- **Branches**: Set up branch protection rules
- **Labels**: Ensure standard labels exist
- **Projects**: Create initial project boards

## 📋 Workflows Overview

### 🔄 CI/CD Pipeline (`ci-cd.yml`)
- **Triggers**: Push/PR to main/develop
- **Features**:
  - Java 21 + Maven build
  - PostgreSQL test database
  - Unit & integration tests
  - Security scanning (Trivy)
  - Code coverage reporting
  - Docker image build

### 🤖 AI Code Review (`automated-code-review.yml`)
- **Triggers**: PR opened/synchronized
- **Features**:
  - Multi-language linting
  - Security vulnerability scanning
  - Code quality analysis
  - Automated PR labeling
  - Review checklist generation

### 🤖 Copilot Enhanced Review (`copilot-enhanced-review.yml`)
- **Triggers**: PR events and comments
- **Features**:
  - AI-powered code analysis
  - Intelligent suggestions
  - Security review
  - Performance analysis
  - Comprehensive summary

### 📊 Projects v2 Automation (`projects-v2-automation.yml`)
- **Triggers**: Issues, PRs, milestones
- **Features**:
  - Auto-link items to projects
  - Milestone project creation
  - Status synchronization
  - Progress tracking

### 🎫 Issue Automation (`issue-automation.yml`)
- **Triggers**: Issue events
- **Features**:
  - Auto-labeling based on content
  - Priority assignment
  - Milestone linking
  - Status comments

## 🪝 Webhook Server Configuration

### Environment Variables

```bash
# GitHub Configuration
GITHUB_TOKEN=your_github_token
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# AI Configuration
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Automation Settings
AUTO_MERGE_ENABLED=true
REVIEW_THRESHOLD_SCORE=7
```

### Webhook Events

Configure these events in GitHub webhook settings:
- `pull_request` (opened, synchronize, reopened)
- `issues` (opened, labeled, assigned, closed)
- `issue_comment` (created)
- `milestone` (opened, closed)
- `project_card` (created, moved)

## 🎯 Copilot Integration

### Commands
Use these commands in PR/issue comments:

```
@copilot analyze    - Analyze code/issues
@copilot review     - Detailed code review
@copilot test       - Generate/run tests
@copilot docs       - Documentation suggestions
```

### AI Agents
- **Kilo Code**: Development and code generation
- **Qwen**: Data processing specialist
- **Claude**: Documentation expert
- **Grok**: Monitoring and alerts
- **Nova**: Research and content generation
- **Intelli**: Analytics engine
- **Sentinel**: Security monitoring
- **Atlas**: Data mapping specialist

## 📊 Projects v2 Setup

### Creating Project Boards

1. **Sprint Boards**: Auto-created for milestones
2. **Feature Boards**: For enhancement tracking
3. **Bug Boards**: For issue management
4. **Release Boards**: For deployment tracking

### Automation Rules

- Issues auto-link to milestone projects
- PRs update project status
- Milestones track completion percentage
- Labels control project placement

## 🔐 Security & Permissions

### Required Permissions

**GitHub Actions**:
```
contents: read
pull-requests: write
issues: write
repository-projects: write
security-events: write
```

**Webhook Server**:
- `repo` scope for GitHub token
- Webhook secret for signature validation

### Branch Protection

```yaml
required_status_checks:
  - ci-cd
  - security-scan
required_pull_request_reviews:
  required_approving_review_count: 1
restrictions: []
```

## 📈 Monitoring & Analytics

### Dashboard Features
- **CI/CD Metrics**: Build success rates, test coverage
- **AI Review Stats**: Review scores, common issues
- **Project Progress**: Milestone completion tracking
- **Issue Analytics**: Resolution times, label distribution

### Alerts
- Failed builds
- Security vulnerabilities
- High-risk PRs
- Milestone delays

## 🛠️ Marketplace Integrations

### Recommended Actions

1. **CodeQL** - Advanced security scanning
2. **Dependabot** - Automated dependency updates
3. **Codecov** - Code coverage reporting
4. **SonarCloud** - Code quality analysis
5. **Snyk** - Vulnerability scanning

### Setup Commands

```bash
# Enable CodeQL
gh api -X PUT repos/{owner}/{repo}/vulnerability-alerts -F state=enabled

# Configure Dependabot
# Add .github/dependabot.yml

# Set up Codecov
# Add CODECOV_TOKEN to secrets
```

## 🚀 Deployment Automation

### Environments
- **Development**: Auto-deploy on merge to develop
- **Staging**: Manual deployment for testing
- **Production**: Protected deployment with approvals

### Docker Integration

```yaml
# Build and push Docker image
- name: Build and push Docker image
  uses: docker/build-push-action@v4
  with:
    context: .
    push: true
    tags: ${{ github.repository }}:${{ github.sha }}
```

## 📚 Best Practices

### Workflow Organization
- Use consistent naming conventions
- Group related jobs in workflows
- Use matrix builds for multi-environment testing
- Implement proper error handling

### AI Integration
- Set clear boundaries for AI automation
- Require human review for critical changes
- Monitor AI performance and accuracy
- Update prompts based on feedback

### Security
- Rotate tokens regularly
- Use least-privilege permissions
- Audit webhook payloads
- Monitor for abuse

## 🐛 Troubleshooting

### Common Issues

1. **Webhook not firing**
   - Check webhook URL and secret
   - Verify event types are selected
   - Check server logs

2. **Actions not running**
   - Verify workflow syntax
   - Check repository permissions
   - Review action versions

3. **AI review failures**
   - Check API keys and quotas
   - Verify model availability
   - Review error logs

### Debug Commands

```bash
# Test webhook locally
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -d @test-payload.json

# Check workflow status
gh run list --repo {owner}/{repo}

# View action logs
gh run view {run-id} --log
```

## 📞 Support

- **Documentation**: Check `docs/` directory
- **Issues**: Create GitHub issues with `automation` label
- **Discussions**: Use GitHub Discussions for questions

## 🎯 Success Metrics

- **CI/CD**: >95% build success rate
- **Reviews**: <4 hour average review time
- **Automation**: >80% of routine tasks automated
- **Quality**: >90% code coverage, <5 critical vulnerabilities

---

**Status**: 🟢 **FULLY AUTOMATED**
**Coverage**: 🚀 **COMPREHENSIVE**
**AI Integration**: 🤖 **ADVANCED**
**Scalability**: 📈 **ENTERPRISE-READY**</content>
<parameter name="filePath">/home/cbwinslow/OpenLegislation-local-dev/.github/AUTOMATION_SETUP_GUIDE.md