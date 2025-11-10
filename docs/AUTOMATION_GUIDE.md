# Comprehensive Automation Setup Guide

This guide provides a complete overview of all automation, CI/CD, and AI agent features available in the OpenLegislation repository.

## Table of Contents

1. [GitHub Actions Workflows](#github-actions-workflows)
2. [Issue and Project Automation](#issue-and-project-automation)
3. [AI-Powered Code Analysis](#ai-powered-code-analysis)
4. [CrewAI Agent Teams](#crewai-agent-teams)
5. [Security Automation](#security-automation)
6. [Repository Rulesets](#repository-rulesets)
7. [Setup Instructions](#setup-instructions)
8. [Troubleshooting](#troubleshooting)

## GitHub Actions Workflows

### Core CI/CD Workflows

#### 1. **CI/CD Pipeline** (`.github/workflows/ci-cd.yml`)
- Runs tests with PostgreSQL
- Performs security scans
- Checks code quality
- Builds and deploys on main branch
- Creates releases

**Triggers**: Push to main/develop, Pull requests
**Required Secrets**: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, `SONAR_TOKEN`

#### 2. **Security Scan** (`.github/workflows/security-scan.yml`)
- CodeQL analysis for Java
- OWASP dependency checking
- Container security scanning with Trivy
- Secret detection with TruffleHog
- License compliance scanning

**Triggers**: Push, PR, Weekly schedule
**Required Secrets**: `FOSSA_API_KEY` (optional)

#### 3. **Code Formatting and Linting** (`.github/workflows/code-formatting.yml`)
- Java: Spotless, PMD, Checkstyle
- Python: Black, isort, Flake8, Pylint, mypy
- YAML/JSON: yamllint, prettier
- Markdown: link checking, linting
- **Auto-fixes** code style issues on PRs

**Triggers**: Push, Pull requests

### Automation Workflows

#### 4. **Issue Automation** (`.github/workflows/issue-automation.yml`)
- Auto-labels new issues based on content
- Auto-assigns issues to team members
- Adds issues to project boards
- Manages stale issues
- Links related issues
- Creates milestones for epics

**Triggers**: Issue events, Schedule (every 6 hours)

#### 5. **Project Board Automation** (`.github/workflows/project-automation.yml`)
- Updates project item status automatically
- Creates sprint boards for milestones
- Syncs issue statuses
- Organizes items by priority
- Generates weekly sprint summaries

**Triggers**: Issue events, PR events, Schedule

#### 6. **AI Code Analysis** (`.github/workflows/ai-code-analysis.yml`)
- AI-powered security pattern detection
- Code complexity analysis
- Automated improvement suggestions
- Test coverage reporting
- Documentation completeness checks

**Triggers**: Pull requests

### Existing Workflows

#### 7. **Automated Code Review** (`.github/workflows/automated-code-review.yml`)
- Comprehensive PR analysis
- Suggests improvements
- Checks best practices

#### 8. **PR Auto-Labeler** (`.github/workflows/pr-auto-labeler.yml`)
- Labels PRs by changed files
- Categorizes by domain

#### 9. **Auto-merge Dependabot** (`.github/workflows/auto-merge-dependabot.yml`)
- Safely auto-merges dependency updates
- Runs full test suite first

#### 10. **Federal Data Ingestion** (`.github/workflows/federal-data-ingestion.yml`)
- Automated federal data updates
- Scheduled data pulls from Congress.gov

## Issue and Project Automation

### Automatic Labels

Issues are automatically labeled based on content:

**Type Labels**:
- `type: bug` - Bug reports
- `type: feature` - New features
- `type: enhancement` - Improvements
- `type: documentation` - Docs
- `type: refactor` - Code refactoring

**Priority Labels**:
- `priority: critical` - Critical issues
- `priority: high` - High priority
- `priority: medium` - Medium priority
- `priority: low` - Low priority

**Domain Labels**:
- `domain: federal-data` - Federal integration
- `domain: database` - Database work
- `domain: api` - API changes
- `domain: frontend` - UI changes
- `domain: ci-cd` - Automation

**Status Labels**:
- `status: in-progress` - Being worked on
- `status: needs-review` - Ready for review
- `status: blocked` - Blocked
- `status: ready` - Ready to start

### Project Boards

Project boards are automatically created and maintained:

1. **OpenLegislation Development** - Main development board
2. **Federal Data Integration Sprint** - Federal data work
3. **Bug Triage & Fixes** - Bug tracking
4. **Documentation Improvement** - Documentation tasks

### Milestones

Quarterly milestones are automatically created:
- Q1 2025 - Federal Data Integration
- Q2 2025 - API Enhancements
- Q3 2025 - Performance Optimization
- Q4 2025 - Documentation & Testing

## AI-Powered Code Analysis

### Security Pattern Detection

The AI analysis workflow detects:
- SQL injection vulnerabilities
- XSS vulnerabilities
- Hardcoded credentials
- Unsafe deserialization
- Path traversal issues

### Code Quality Checks

Automatically analyzes:
- Code complexity (cyclomatic, NPath)
- Method length
- Code duplication
- Anti-patterns

### Improvement Suggestions

Provides suggestions for:
- Better logging practices
- Exception handling
- TODO/FIXME tracking
- Null safety

### Test Coverage

Reports coverage metrics:
- Line coverage percentage
- Missed vs covered lines
- Comparison with previous runs

## CrewAI Agent Teams

### 1. Software Development Crew

**Agents**:
- **Senior Developer**: Code review, architecture
- **QA Engineer**: Testing, quality assurance
- **DevOps Engineer**: CI/CD, infrastructure
- **Security Expert**: Security audits, compliance

**Usage**:
```python
from tools.crewai_automation import OpenLegislationCrews

crews = OpenLegislationCrews()
result = crews.execute_code_review(code_changes, file_path)
```

### 2. Legislative Policy Crew

**Agents**:
- **Legislative Expert**: Legislative processes, bill analysis
- **Policy Analyst**: Policy categorization, context
- **Integration Specialist**: Federal/state data mapping

**Usage**:
```python
result = crews.analyze_legislative_data(bill_data)
```

### 3. Database Crew

**Agents**:
- **DB Architect**: Schema design, optimization
- **DBA**: Operations, maintenance
- **Search Engineer**: Elasticsearch optimization
- **Migration Specialist**: Data migrations

**Usage**:
```python
result = crews.optimize_database_query(query, context)
```

### 4. Documentation Crew

**Agents**:
- **Technical Writer**: User/developer documentation
- **API Doc Specialist**: API documentation, OpenAPI specs
- **Content Organizer**: Structure, consistency

**Usage**:
```python
result = crews.generate_documentation(code_path, doc_type)
```

## Security Automation

### Automated Security Scans

1. **CodeQL**: Static analysis for Java code
2. **Dependency Check**: Vulnerability scanning for dependencies
3. **Trivy**: Container security scanning
4. **TruffleHog**: Secret detection in code
5. **FOSSA**: License compliance

### Security Issue Creation

Failed security scans automatically create issues with:
- `security` label
- `urgent` label if critical
- Detailed findings
- Remediation suggestions

### Pre-commit Hooks

Installed pre-commit hooks (`.pre-commit-config.yaml`):
- Trailing whitespace removal
- YAML validation
- Large file detection
- Secret detection
- Environment file protection
- XML syntax validation

**Enable pre-commit hooks**:
```bash
pip install pre-commit
pre-commit install
```

## Repository Rulesets

See [GitHub Rulesets Guide](github-rulesets-guide.md) for detailed configuration.

### Quick Setup

1. **Main Branch**: Requires PR, 1 approval, all checks pass
2. **Develop Branch**: Requires PR, 1 approval, basic checks
3. **Release Branches**: Requires PR, 2 approvals, all checks, signed commits
4. **Tags**: Protected, signed, restricted creation

## Setup Instructions

### Prerequisites

- GitHub repository access
- GitHub token with appropriate permissions
- Docker (for local testing)
- Python 3.10+ (for automation scripts)
- Maven and Java 17 (for building)

### Initial Setup

#### 1. Configure GitHub Secrets

Go to Settings → Secrets and variables → Actions:

**Required Secrets**:
```
GITHUB_TOKEN (automatically provided)
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN
SONAR_TOKEN (for SonarCloud)
```

**Optional Secrets**:
```
FOSSA_API_KEY (license scanning)
OPENAI_API_KEY (for AI features)
```

#### 2. Install Python Dependencies

```bash
cd tools
pip install -r requirements.txt
pip install crewai langchain requests
```

#### 3. Set Up GitHub Automation

```bash
# Export your GitHub token
export GITHUB_TOKEN="your_github_token_here"

# Run setup script
python3 tools/github_automation.py
```

This creates:
- Standard labels
- Project milestones
- Project boards
- Sample issues

#### 4. Enable Workflows

All workflows are in `.github/workflows/` and will run automatically when:
- Code is pushed
- PRs are created
- Issues are opened
- Scheduled times occur

#### 5. Configure Rulesets

Follow [GitHub Rulesets Guide](github-rulesets-guide.md):

```bash
# Via GitHub web interface
# Settings → Rules → Rulesets → New ruleset

# Or via GitHub CLI
gh api repos/cbwinslow/OpenLegislation-local-dev/rulesets \
  -X POST --input .github/rulesets/main-branch-protection.json
```

#### 6. Set Up CrewAI (Optional)

```bash
# Install CrewAI
pip install crewai

# Set up OpenAI API key (if using OpenAI)
export OPENAI_API_KEY="your_openai_key"

# Test crews
python3 tools/crewai_automation.py
```

### Verification

#### Test Workflows

```bash
# Trigger a workflow manually
gh workflow run ci-cd.yml

# Check workflow status
gh run list --limit 5

# View workflow logs
gh run view <run-id>
```

#### Test Issue Automation

```bash
# Create a test issue
gh issue create \
  --title "Test: Federal data ingestion bug" \
  --body "This is a test issue for automation"

# Check if labels were auto-applied
gh issue view <issue-number>
```

#### Test Pre-commit Hooks

```bash
# Stage a file
git add some-file.java

# Commit (hooks will run)
git commit -m "test: verify pre-commit hooks"
```

## Maintenance

### Regular Tasks

**Weekly**:
- Review security scan results
- Check stale issues
- Review project board status

**Monthly**:
- Update dependencies (Dependabot handles this)
- Review and update labels
- Audit workflow performance

**Quarterly**:
- Review and update rulesets
- Update milestones
- Review team assignments

### Monitoring

#### Workflow Health

```bash
# Check recent workflow runs
gh run list --limit 10

# View failed runs
gh run list --status failure

# View workflow logs
gh run view <run-id> --log
```

#### Issue Automation

Check automation is working:
- New issues get labeled
- Issues get assigned
- Related issues are linked
- Stale issues are marked

#### Project Boards

Verify:
- Issues added to boards
- Status updates correctly
- Sprint summaries generated

## Troubleshooting

### Common Issues

#### Issue: Workflows not running

**Solutions**:
1. Check workflow trigger configuration
2. Verify branch names match triggers
3. Check workflow syntax with `gh workflow view`
4. Ensure repository actions are enabled

#### Issue: Auto-labeling not working

**Solutions**:
1. Check GITHUB_TOKEN permissions
2. Verify issue content matches patterns
3. Check workflow logs for errors
4. Ensure labels exist in repository

#### Issue: Security scans failing

**Solutions**:
1. Check secret configuration
2. Review scan output for actual issues
3. Update vulnerable dependencies
4. Configure scan exceptions if needed

#### Issue: CrewAI not working

**Solutions**:
1. Verify OpenAI API key is set
2. Check CrewAI installation
3. Review error logs
4. Try with simpler examples first

### Getting Help

1. **Check workflow logs**: Most detailed error information
2. **Review documentation**: Check specific workflow docs
3. **GitHub Actions documentation**: https://docs.github.com/actions
4. **Create an issue**: Use the repository issue tracker

## Advanced Configuration

### Custom Workflows

Create custom workflows in `.github/workflows/`:

```yaml
name: Custom Workflow
on:
  push:
    branches: [ main ]
jobs:
  custom-job:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Custom step
      run: echo "Custom automation"
```

### Custom AI Agents

Extend CrewAI crews:

```python
from tools.crewai_automation import OpenLegislationCrews

class CustomCrews(OpenLegislationCrews):
    def create_custom_crew(self):
        # Define custom agents and tasks
        pass
```

### Webhook Integration

For advanced automation, set up webhooks:

See [webhook-server/README.md](../webhook-server/README.md) for AI-powered webhook server setup.

## Best Practices

1. **Start Simple**: Enable workflows gradually
2. **Monitor Performance**: Check workflow execution times
3. **Iterate**: Refine automation based on team feedback
4. **Document Changes**: Keep this guide updated
5. **Security First**: Never commit secrets
6. **Test Locally**: Test workflows before merging
7. **Use Caching**: Cache dependencies to speed up workflows
8. **Fail Fast**: Configure workflows to fail quickly on errors

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [CrewAI Documentation](https://docs.crewai.com/)
- [OpenLegislation API](http://legislation.nysenate.gov/static/docs/html/)

## Contributing

To improve automation:

1. Create feature branch: `feature/automation-improvement`
2. Add/modify workflows
3. Test thoroughly
4. Document changes
5. Submit PR with clear description

---

**Last Updated**: November 2025
**Maintainer**: OpenLegislation Team
**Questions**: Create an issue with label `automation`
