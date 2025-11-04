# GitHub Repository Settings Configuration

This document describes the recommended GitHub repository settings for optimal PR automation.

## Repository Settings (Settings > General)

### Features

#### Wikis
- [ ] Enable Wikis (optional)

#### Issues
- [x] Enable Issues
- [x] Enable issue templates

#### Sponsorships
- [ ] Enable Sponsorships (optional)

#### Projects
- [x] Enable Projects (optional for project management)

#### Preserve this repository
- [ ] Archive this repository (NO)

### Pull Requests

#### Allow merge commits
- [x] **Enable** - Allow merge commits
  - Title: Default to pull request title
  - Description: Default to pull request description

#### Allow squash merging
- [x] **Enable** - Allow squash merging (recommended)
  - Title: Default to pull request title
  - Description: Default to pull request description

#### Allow rebase merging
- [x] **Enable** - Allow rebase merging
  - Update with rebase

#### Auto-merge
- [x] **Enable** - Allow auto-merge ⭐ **REQUIRED**
  - This is critical for automated PR merging

#### Automatically delete head branches
- [x] **Enable** - Automatically delete head branches after PRs are merged
  - Keeps repository clean

## Branch Protection Rules (Settings > Branches)

### Main Branch Protection

**Branch name pattern**: `main`

#### Protect matching branches

##### Require a pull request before merging
- [x] **Enable**
  - Required approvals: **1** (adjust based on team size)
  - [x] Dismiss stale pull request approvals when new commits are pushed
  - [ ] Require review from Code Owners (enable after configuring CODEOWNERS)
  - [x] Restrict who can dismiss pull request reviews (optional)
  - [ ] Allow specified actors to bypass required pull requests (optional)

##### Require status checks to pass before merging
- [x] **Enable**
  - [x] Require branches to be up to date before merging
  - **Required status checks** (add after first workflow run):
    - `test` (from CI/CD)
    - `security-scan` (from security workflow)
    - `code-quality` (from CI/CD)
    - `code-quality-checks` (from automated code review)
    - `pr-size-labeler` (from automated code review)

##### Require conversation resolution before merging
- [x] **Enable** - All PR conversations must be resolved

##### Require signed commits
- [ ] Enable (optional, recommended for sensitive repos)

##### Require linear history
- [ ] Enable (optional, prevents merge commits)

##### Require deployments to succeed before merging
- [ ] Enable (optional, if using deployment environments)

##### Lock branch
- [ ] Enable (NO - would prevent all pushes)

##### Do not allow bypassing the above settings
- [x] Enable (recommended)
  - [ ] Allow specified actors to bypass (add admin users if needed)

##### Restrict who can push to matching branches
- [ ] Enable (optional)

##### Allow force pushes
- [ ] Enable (NO - prevents history rewriting)

##### Allow deletions
- [ ] Enable (NO - prevents accidental deletion)

### Develop Branch Protection (if using)

**Branch name pattern**: `develop`

Similar settings to main, but potentially:
- Required approvals: **1** (same as main)
- Status checks: Same as main
- Less restrictive on some rules (team discretion)

## Integrations and Services (Settings > Integrations)

### Installed GitHub Apps

#### Recommended Apps
- **Dependabot** - Already configured via `.github/dependabot.yml`
- **CodeQL** - For security scanning
- **Codecov** - For code coverage (optional)

#### Optional Apps
- **Slack/Discord** - For notifications
- **Linear/Jira** - For issue tracking integration
- **Sentry** - For error tracking

## Code Security and Analysis (Settings > Security & analysis)

### Dependency graph
- [x] **Enable** - Track dependencies

### Dependabot alerts
- [x] **Enable** - Get alerts for vulnerable dependencies

### Dependabot security updates
- [x] **Enable** - Automatic security updates

### Dependabot version updates
- [x] **Enable** - Configured via `.github/dependabot.yml`

### Code scanning
- [x] **Enable** - CodeQL analysis via workflows

### Secret scanning
- [x] **Enable** - Scan for exposed secrets
- [x] **Enable** - Push protection (prevents secrets in commits)

## Actions (Settings > Actions)

### Actions permissions
- [x] **Allow all actions and reusable workflows**
  - Or: Allow select actions and reusable workflows (more restrictive)

### Workflow permissions
- [x] **Read and write permissions** ⭐ **REQUIRED**
  - Workflows need write access for:
    - Creating/updating issues
    - Adding labels to PRs
    - Posting comments
    - Enabling auto-merge
- [x] **Allow GitHub Actions to create and approve pull requests**
  - Required for Dependabot auto-merge

### Required workflows
- [ ] Configure if using enterprise (optional)

## Secrets and Variables (Settings > Secrets and variables)

### Actions Secrets

Create these secrets if needed:

```
# Docker Hub (if using container registry)
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN

# Database (if running migrations in CI)
DB_USER
DB_PASS

# Deployment
STAGING_SERVER
DEPLOY_USER

# Third-party integrations
SONAR_TOKEN (for SonarCloud)
FOSSA_API_KEY (for license scanning)
SLACK_WEBHOOK (for notifications)
```

### Actions Variables

Create these variables if needed:

```
JAVA_VERSION=17
MAVEN_VERSION=3.9.4
NODE_VERSION=18
```

## Environments (Settings > Environments)

### Recommended Environments

#### Staging
- **Deployment branches**: `develop` only
- **Environment secrets**: Staging-specific credentials
- **Required reviewers**: Optional
- **Wait timer**: 0 minutes

#### Production
- **Deployment branches**: `main` only
- **Environment secrets**: Production credentials
- **Required reviewers**: 1-2 reviewers
- **Wait timer**: 0-5 minutes

## Labels (Issues > Labels)

### Required Labels for Automation

Create these labels using GitHub CLI or UI:

```bash
# Size labels
gh label create "size/XS" --color "0e8a16" --description "Extra small PR (< 10 lines)"
gh label create "size/S" --color "1d76db" --description "Small PR (10-50 lines)"
gh label create "size/M" --color "fbca04" --description "Medium PR (50-200 lines)"
gh label create "size/L" --color "d93f0b" --description "Large PR (200-500 lines)"
gh label create "size/XL" --color "b60205" --description "Extra large PR (> 500 lines)"

# Status labels
gh label create "auto-merge" --color "0366d6" --description "Will be automatically merged"
gh label create "needs-review" --color "d4c5f9" --description "Needs manual review"
gh label create "high-priority" --color "b60205" --description "High priority"
gh label create "stale" --color "ededed" --description "No recent activity"
gh label create "keep-open" --color "c2e0c6" --description "Don't auto-close"
gh label create "in-progress" --color "fbca04" --description "Work in progress"
gh label create "blocked" --color "d93f0b" --description "Blocked"

# Type labels
gh label create "bug-fix" --color "d73a4a" --description "Bug fix"
gh label create "enhancement" --color "a2eeef" --description "New feature"
gh label create "security" --color "b60205" --description "Security fix"
gh label create "performance" --color "ffff00" --description "Performance improvement"
gh label create "breaking-change" --color "d93f0b" --description "Breaking change"
gh label create "refactoring" --color "5319e7" --description "Code refactoring"

# Component labels
gh label create "backend" --color "0052cc" --description "Backend changes"
gh label create "frontend" --color "1d76db" --description "Frontend changes"
gh label create "database" --color "5319e7" --description "Database changes"
gh label create "api" --color "0e8a16" --description "API changes"
gh label create "documentation" --color "0075ca" --description "Documentation"
gh label create "tests" --color "d876e3" --description "Test changes"
gh label create "ci-cd" --color "1d76db" --description "CI/CD changes"
gh label create "infrastructure" --color "0052cc" --description "Infrastructure changes"
gh label create "tooling" --color "fbca04" --description "Tooling changes"

# Other labels
gh label create "dashboard" --color "e4e669" --description "Dashboard report"
gh label create "automation" --color "0366d6" --description "Automation"
gh label create "dependencies" --color "0366d6" --description "Dependency updates"
gh label create "java" --color "b07219" --description "Java code"
gh label create "python" --color "3572A5" --description "Python code"
gh label create "javascript" --color "f1e05a" --description "JavaScript code"
gh label create "docker" --color "0db7ed" --description "Docker"
gh label create "github-actions" --color "2088FF" --description "GitHub Actions"
gh label create "federal-integration" --color "d4c5f9" --description "Federal integration"
gh label create "data-processing" --color "c5def5" --description "Data processing"
gh label create "business-logic" --color "bfd4f2" --description "Business logic"
gh label create "ui" --color "1d76db" --description "UI changes"
gh label create "migration" --color "5319e7" --description "Database migration"
gh label create "build" --color "fbca04" --description "Build system"
gh label create "configuration" --color "ededed" --description "Configuration"
```

## Collaborators and Teams (Settings > Collaborators)

### Team Structure

#### Core Team
- **Permissions**: Admin or Write
- **Members**: Core maintainers
- **Review requirements**: Can approve PRs

#### Contributors
- **Permissions**: Triage or Write
- **Members**: Regular contributors
- **Review requirements**: Can review but may not be able to approve

#### Read-Only
- **Permissions**: Read
- **Members**: External observers
- **Review requirements**: Can comment but not approve

### Outside Collaborators
- Add as needed with appropriate permissions
- Use CODEOWNERS to auto-assign reviews

## Notifications (Settings > Notifications)

### Configure Personal Notifications

Recommended settings for team members:

#### Participating and @mentions
- [x] Email + Web
- Choose notification frequency

#### Pull requests
- [x] Enable notifications for:
  - Reviews requested
  - Assigned
  - @mentions
  - Participating

#### Actions
- [x] Failed workflows (via email)
- [ ] Successful workflows (can be noisy)

## Moderation (Settings > Moderation)

### Interaction limits
- Configure if needed to prevent spam
- Default: No limits

### Code review limits
- Configure if needed
- Default: No limits

## API and Webhooks (Settings > Webhooks)

### Webhooks

Add webhooks for external services:

#### Slack/Discord
- Payload URL: Your webhook URL
- Content type: application/json
- Events: Pull requests, Issues, Push

#### CI/CD Services
- Configure as needed for external CI systems

## Pages (Settings > Pages)

### GitHub Pages (optional)
- Source: Deploy from branch or GitHub Actions
- Branch: `gh-pages` or `docs`
- Folder: `/` or `/docs`

## Verification

After configuring, verify:

```bash
# Check if auto-merge is enabled
gh repo view --json autoMergeAllowed

# Check branch protection
gh api repos/:owner/:repo/branches/main/protection

# List labels
gh label list

# Check workflow permissions
gh api repos/:owner/:repo/actions/permissions
```

## Recommended Settings Summary

### ✅ MUST CONFIGURE
1. Enable auto-merge (Settings > General > Pull Requests)
2. Set up branch protection for `main`
3. Enable workflow write permissions (Settings > Actions)
4. Create required labels
5. Configure CODEOWNERS

### ⭐ HIGHLY RECOMMENDED
1. Require status checks before merging
2. Require PR reviews (1 approval minimum)
3. Enable conversation resolution requirement
4. Enable secret scanning with push protection
5. Automatically delete merged branches

### 💡 OPTIONAL BUT USEFUL
1. Set up environments for deployment
2. Configure Slack/Discord notifications
3. Enable code scanning (CodeQL)
4. Set up code coverage tracking
5. Configure merge queue (GitHub Enterprise)

## Verification Checklist

After setup, verify:

- [ ] Auto-merge enabled in repository settings
- [ ] Branch protection rules created for `main`
- [ ] Required status checks configured
- [ ] All required labels created
- [ ] CODEOWNERS file configured
- [ ] Workflow permissions set to read+write
- [ ] Actions allowed to create/approve PRs
- [ ] Dependabot configuration present
- [ ] Secret scanning enabled
- [ ] All workflows visible in Actions tab

## Maintenance

### Weekly
- Review branch protection effectiveness
- Check workflow success rates
- Verify label usage

### Monthly
- Audit collaborators and permissions
- Review and update required checks
- Update CODEOWNERS if team changes

### Quarterly
- Review security settings
- Audit webhooks and integrations
- Update documentation

## Support

Need help configuring?

1. Check [GitHub Docs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features)
2. Review [Setup Guide](pr-automation-setup.md)
3. Create issue with `automation` label
4. Contact: @cbwinslow

---

**Note**: Some features (like merge queue) require GitHub Enterprise. Check your plan for availability.
