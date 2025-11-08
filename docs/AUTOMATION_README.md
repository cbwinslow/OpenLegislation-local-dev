# Automation and CI/CD Features

This directory contains comprehensive automation, CI/CD workflows, AI agents, and scripts for the OpenLegislation project.

## 🚀 Quick Start

```bash
# Run the master setup script
./tools/setup_automation.sh

# Or manually install dependencies
cd tools
pip install -r requirements.txt
pip install crewai langchain requests
```

## 📋 Features Overview

### 1. **GitHub Actions Workflows** (`.github/workflows/`)

#### Core Workflows
- **`ci-cd.yml`**: Complete CI/CD pipeline with testing, security, and deployment
- **`security-scan.yml`**: CodeQL, OWASP dependency check, Trivy, TruffleHog
- **`code-formatting.yml`**: Auto-format Java, Python, YAML, JSON, Markdown

#### Automation Workflows
- **`issue-automation.yml`**: Auto-label, auto-assign, project board integration
- **`project-automation.yml`**: Project board status updates, sprint summaries
- **`ai-code-analysis.yml`**: AI-powered security and quality analysis

#### Existing Workflows
- **`automated-code-review.yml`**: Comprehensive PR reviews
- **`pr-auto-labeler.yml`**: Automatic PR labeling
- **`auto-merge-dependabot.yml`**: Safe dependency updates
- **`federal-data-ingestion.yml`**: Scheduled federal data ingestion

### 2. **CrewAI Agent Teams** (`tools/crewai_automation.py`)

Four specialized AI agent crews:

#### Software Development Crew
- Senior Developer (code review, architecture)
- QA Engineer (testing, quality)
- DevOps Engineer (CI/CD, infrastructure)
- Security Expert (security audits)

#### Legislative Policy Crew
- Legislative Expert (bill processing, legislative data)
- Policy Analyst (categorization, context)
- Integration Specialist (federal/state data mapping)

#### Database Crew
- DB Architect (schema design, optimization)
- DBA (operations, maintenance)
- Search Engineer (Elasticsearch)
- Migration Specialist (data migrations)

#### Documentation Crew
- Technical Writer (docs, guides)
- API Doc Specialist (API documentation)
- Content Organizer (structure, consistency)

**Usage**:
```python
from tools.crewai_automation import OpenLegislationCrews

crews = OpenLegislationCrews()

# Execute code review
result = crews.execute_code_review(code_changes, file_path)

# Analyze legislative data
result = crews.analyze_legislative_data(bill_data)

# Optimize database query
result = crews.optimize_database_query(query, context)

# Generate documentation
result = crews.generate_documentation(code_path, doc_type)
```

### 3. **GitHub Automation** (`tools/github_automation.py`)

Automate GitHub repository management:

```bash
# Set GitHub token
export GITHUB_TOKEN=your_token_here

# Run automation
python3 tools/github_automation.py
```

**Features**:
- Create standard labels (type, priority, domain, status, size)
- Create project milestones (quarterly roadmap)
- Create project boards (Projects v2)
- Bulk create issues
- Link related issues

### 4. **Issue and Project Management**

**Auto-labeling**: Issues automatically get labels based on:
- Content keywords (bug, feature, docs, etc.)
- Priority indicators (urgent, critical)
- Domain (federal-data, database, api, frontend, ci-cd)

**Auto-assignment**: Issues assigned based on labels:
- `federal-data` → Federal data specialists
- `database` → Database team
- `security` → Security team

**Project Boards**: Automatically created boards:
- OpenLegislation Development
- Federal Data Integration Sprint
- Bug Triage & Fixes
- Documentation Improvement

**Status Tracking**: Issues automatically move through:
- Todo → In Progress → In Review → Done

### 5. **Security Automation**

**Pre-commit Hooks** (`.pre-commit-config.yaml`):
- Trailing whitespace removal
- YAML validation
- Large file detection
- Secret detection
- Environment file protection
- XML syntax validation

**Security Scans**:
- CodeQL (Java static analysis)
- OWASP Dependency Check
- Trivy (container scanning)
- TruffleHog (secret detection)
- FOSSA (license compliance)

**Enable pre-commit**:
```bash
pip install pre-commit
pre-commit install
```

### 6. **Code Quality and Formatting**

**Java**:
- Spotless (code formatting)
- PMD (static analysis)
- Checkstyle (style checking)

**Python**:
- Black (formatting)
- isort (import sorting)
- Flake8 (linting)
- Pylint (code analysis)
- mypy (type checking)

**Other**:
- yamllint (YAML)
- prettier (JSON)
- markdown-lint (Markdown)

**Auto-formatting**: PRs automatically get formatted with commits from `github-actions[bot]`

### 7. **AI-Powered Analysis**

**Security Pattern Detection**:
- SQL injection
- XSS vulnerabilities
- Hardcoded credentials
- Unsafe deserialization
- Path traversal

**Code Quality Analysis**:
- Complexity metrics
- Code duplication
- Anti-patterns
- Test coverage

**Improvement Suggestions**:
- Better logging practices
- Exception handling
- Null safety
- TODO/FIXME tracking

### 8. **Repository Rulesets**

See `docs/github-rulesets-guide.md` for detailed setup.

**Recommended Rulesets**:
- Main branch: PR required, 1 approval, all checks pass
- Develop branch: PR required, 1 approval, basic checks
- Release branches: PR required, 2 approvals, signed commits
- Tags: Protected, signed, restricted

### 9. **Wiki Automation**

See `docs/wiki-automation-guide.md` for details.

**Create wiki pages**:
```bash
python3 tools/wiki_manager.py
```

**Standard pages**:
- Home
- Getting Started
- API Documentation
- Database Schema
- Federal Data Integration
- Deployment Guide

## 📚 Documentation

### Comprehensive Guides
- **`docs/AUTOMATION_GUIDE.md`**: Complete automation setup and usage guide
- **`docs/github-rulesets-guide.md`**: Repository rulesets configuration
- **`docs/wiki-automation-guide.md`**: Wiki management and automation
- **`.github/copilot-instructions-detailed.md`**: GitHub Copilot instructions

### Quick Reference
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [CrewAI Documentation](https://docs.crewai.com/)
- [GitHub API Documentation](https://docs.github.com/en/rest)

## 🔧 Configuration Files

- **`.yamllint`**: YAML linting rules
- **`.github/markdown-link-check-config.json`**: Markdown link checking
- **`.pre-commit-config.yaml`**: Pre-commit hooks configuration
- **`.github/workflows/*.yml`**: GitHub Actions workflows

## 🏃 Usage Examples

### Run Workflows Manually

```bash
# List workflows
gh workflow list

# Run a specific workflow
gh workflow run ci-cd.yml

# View workflow runs
gh run list --limit 5

# View logs
gh run view <run-id> --log
```

### Create Issues Programmatically

```python
from tools.github_automation import GitHubAutomation

automation = GitHubAutomation(token, owner, repo)

automation.create_issue(
    title="Improve federal data error handling",
    body="Add retry logic and better error messages",
    labels=["enhancement", "federal-data", "priority: high"]
)
```

### Run AI Code Review

```python
from tools.crewai_automation import OpenLegislationCrews

crews = OpenLegislationCrews()
review = crews.execute_code_review(code_changes, "BillService.java")
print(review)
```

### Test Pre-commit Hooks

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files
git add .
git commit -m "test commit"  # Hooks run automatically
```

## 🛠️ Setup Requirements

### Required
- Python 3.10+
- Git
- GitHub account with repository access

### Optional
- GitHub CLI (`gh`)
- Maven (for Java builds)
- Docker (for container testing)
- OpenAI API key (for AI features)

### GitHub Secrets

Configure in Settings → Secrets and variables → Actions:

**Required**:
- `GITHUB_TOKEN` (automatically provided)

**Optional**:
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `SONAR_TOKEN`
- `FOSSA_API_KEY`
- `OPENAI_API_KEY`

## 📊 Monitoring

### Workflow Status

```bash
# Check recent runs
gh run list --limit 10

# View failed runs
gh run list --status failure

# View specific workflow
gh workflow view ci-cd.yml
```

### Issue Automation

Check that:
- New issues get labeled automatically
- Issues are assigned to correct team members
- Related issues are linked
- Stale issues are marked

### Code Quality

Monitor:
- Pre-commit hook success rate
- Code formatting compliance
- Security scan results
- Test coverage trends

## 🔒 Security

### Secrets Management
- Never commit secrets or credentials
- Use GitHub Secrets for sensitive data
- Pre-commit hooks prevent accidental commits
- Secret scanning runs on all commits

### Security Scans
- CodeQL runs on every PR and weekly
- Dependency vulnerabilities checked daily
- Container images scanned before deployment
- Security issues create automatic GitHub issues

## 🤝 Contributing

To improve automation:

1. Create feature branch: `feature/automation-improvement`
2. Add or modify workflows/scripts
3. Test thoroughly
4. Update documentation
5. Submit PR with clear description

## 📝 Maintenance

### Weekly
- Review security scan results
- Check stale issues
- Monitor workflow performance

### Monthly
- Update dependencies
- Review labels and assignments
- Audit workflow efficiency

### Quarterly
- Update rulesets
- Review milestones
- Update team assignments

## 🆘 Troubleshooting

### Workflows Not Running

1. Check workflow triggers
2. Verify branch names
3. Review workflow syntax: `gh workflow view <workflow>`
4. Ensure Actions are enabled

### Labels Not Applied

1. Verify GITHUB_TOKEN permissions
2. Check issue content matches patterns
3. Review workflow logs
4. Ensure labels exist

### Pre-commit Hooks Failing

1. Run manually: `pre-commit run --all-files`
2. Review error messages
3. Fix issues or update `.pre-commit-config.yaml`
4. Reinstall: `pre-commit install`

## 📞 Support

- **Documentation**: See `docs/AUTOMATION_GUIDE.md`
- **Issues**: Create issue with label `automation`
- **GitHub Actions**: https://docs.github.com/actions
- **CrewAI**: https://docs.crewai.com/

## 🎯 Roadmap

Future enhancements:
- [ ] Enhanced AI code suggestions with GPT-4
- [ ] Automated performance testing
- [ ] Integration with Linear/Jira
- [ ] Custom GitHub Actions
- [ ] Self-hosted runners
- [ ] Advanced security scanning
- [ ] Automated documentation generation
- [ ] ML-powered issue triage

---

**Last Updated**: November 2025  
**Maintainer**: OpenLegislation Team  
**Version**: 1.0.0

For questions or suggestions, create an issue with the `automation` label.
