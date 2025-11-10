# GitHub Repository Rulesets Configuration Guide

This guide helps you create rulesets for the OpenLegislation repository to enforce code quality, security, and collaboration standards.

## Overview

GitHub Rulesets allow you to enforce branch protection, require status checks, and control how code changes are made to your repository. Rulesets are more flexible than traditional branch protection rules.

## Creating Rulesets

### Via GitHub Web Interface

1. Go to your repository on GitHub
2. Click **Settings** → **Rules** → **Rulesets**
3. Click **New ruleset** → **New branch ruleset**
4. Configure as described below

### Via GitHub CLI

```bash
# Install GitHub CLI if not already installed
# https://cli.github.com/

# Create ruleset (requires JSON configuration)
gh api repos/cbwinslow/OpenLegislation-local-dev/rulesets \
  -X POST \
  -f name='Main Branch Protection' \
  -f enforcement='active' \
  -f target='branch' \
  --input ruleset-main.json
```

## Recommended Rulesets

### 1. Main Branch Protection

**Name**: `Main Branch Protection`
**Target**: Branch `main`
**Enforcement**: Active

**Rules**:
- ✅ Require pull request before merging
  - Required approvals: 1
  - Dismiss stale reviews: Yes
  - Require review from code owners: Yes
- ✅ Require status checks to pass
  - Required checks:
    - `test`
    - `security-scan`
    - `code-quality`
    - `build-and-deploy`
- ✅ Require conversation resolution before merging
- ✅ Require signed commits (recommended)
- ✅ Block force pushes
- ✅ Require linear history
- ✅ Restrict deletions

**Configuration JSON**:
```json
{
  "name": "Main Branch Protection",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/main"],
      "exclude": []
    }
  },
  "rules": [
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": true,
        "require_last_push_approval": false
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "required_status_checks": [
          {"context": "test"},
          {"context": "security-scan"},
          {"context": "code-quality"}
        ],
        "strict_required_status_checks_policy": true
      }
    },
    {
      "type": "non_fast_forward"
    },
    {
      "type": "deletion"
    }
  ]
}
```

### 2. Develop Branch Protection

**Name**: `Develop Branch Protection`
**Target**: Branch `develop`
**Enforcement**: Active

**Rules**:
- ✅ Require pull request before merging
  - Required approvals: 1
- ✅ Require status checks to pass
  - Required checks:
    - `test`
    - `code-quality`
- ✅ Block force pushes
- ✅ Allow specific users to bypass (for hotfixes)

**Configuration JSON**:
```json
{
  "name": "Develop Branch Protection",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/develop"],
      "exclude": []
    }
  },
  "bypass_actors": [
    {
      "actor_id": 1,
      "actor_type": "OrganizationAdmin",
      "bypass_mode": "always"
    }
  ],
  "rules": [
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": true
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "required_status_checks": [
          {"context": "test"},
          {"context": "code-quality"}
        ]
      }
    },
    {
      "type": "non_fast_forward"
    }
  ]
}
```

### 3. Release Branch Protection

**Name**: `Release Branch Protection`
**Target**: Branches matching `release/*`
**Enforcement**: Active

**Rules**:
- ✅ Require pull request before merging
  - Required approvals: 2
- ✅ Require all status checks
- ✅ Block force pushes
- ✅ Restrict deletions
- ✅ Require signed commits

**Configuration JSON**:
```json
{
  "name": "Release Branch Protection",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/release/*"],
      "exclude": []
    }
  },
  "rules": [
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 2,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": true
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "required_status_checks": [
          {"context": "test"},
          {"context": "security-scan"},
          {"context": "code-quality"},
          {"context": "build-and-deploy"}
        ],
        "strict_required_status_checks_policy": true
      }
    },
    {
      "type": "required_signatures"
    },
    {
      "type": "non_fast_forward"
    },
    {
      "type": "deletion"
    }
  ]
}
```

### 4. Tag Protection

**Name**: `Tag Protection`
**Target**: Tags matching `v*`
**Enforcement**: Active

**Rules**:
- ✅ Restrict tag creation to specific roles
- ✅ Restrict tag deletion
- ✅ Require signed tags

**Configuration JSON**:
```json
{
  "name": "Tag Protection",
  "target": "tag",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/tags/v*"],
      "exclude": []
    }
  },
  "rules": [
    {
      "type": "creation"
    },
    {
      "type": "deletion"
    },
    {
      "type": "required_signatures"
    }
  ]
}
```

### 5. Feature Branch Standards

**Name**: `Feature Branch Standards`
**Target**: Branches matching `feature/*`, `bugfix/*`, `hotfix/*`
**Enforcement**: Evaluate (warning only)

**Rules**:
- ⚠️ Require status checks (warning mode)
- ⚠️ Suggest linear history

This ruleset is in evaluate mode to guide developers without blocking work.

## Custom Rulesets for OpenLegislation

### Federal Data Integration Branches

**Name**: `Federal Data Branches`
**Target**: Branches matching `federal/*`

**Special Rules**:
- Require federal-data integration tests to pass
- Require review from federal data team
- Auto-assign to federal data specialists

### Database Migration Branches

**Name**: `Database Migration Branches`
**Target**: Branches matching `db/*`, `migration/*`

**Special Rules**:
- Require database migration validation
- Require DBA review
- Require rollback script
- Run migration tests in CI

## Bypass Permissions

Configure bypass actors who can override rulesets:

1. **Repository Admins**: Full bypass for emergencies
2. **GitHub Actions**: Bypass for automated processes
3. **Release Managers**: Bypass for release branches

## Step-by-Step Setup

### 1. Enable Required Status Checks

First, ensure your workflows are configured and running:

```bash
# Check workflow status
gh workflow list

# Make sure these workflows exist and run on PRs:
# - CI/CD Pipeline
# - Security Scan
# - Code Quality Check
```

### 2. Create Main Branch Ruleset

```bash
# Via GitHub CLI
gh api repos/cbwinslow/OpenLegislation-local-dev/rulesets \
  -X POST \
  --input .github/rulesets/main-branch-protection.json
```

Or via web interface:
1. Settings → Rules → Rulesets
2. New ruleset → New branch ruleset
3. Name: "Main Branch Protection"
4. Target: `main`
5. Configure rules as described above
6. Save

### 3. Create Additional Rulesets

Repeat for:
- Develop branch
- Release branches
- Tag protection

### 4. Test Rulesets

```bash
# Try to push to main (should fail)
git checkout main
git push origin main  # Should be blocked

# Create a PR instead
git checkout -b test-ruleset
git push origin test-ruleset
gh pr create --base main
```

## Monitoring and Maintenance

### View Ruleset Status

```bash
# List all rulesets
gh api repos/cbwinslow/OpenLegislation-local-dev/rulesets

# View specific ruleset
gh api repos/cbwinslow/OpenLegislation-local-dev/rulesets/{ruleset_id}
```

### Update Rulesets

```bash
# Update via API
gh api repos/cbwinslow/OpenLegislation-local-dev/rulesets/{ruleset_id} \
  -X PUT \
  --input updated-ruleset.json
```

### Monitor Bypass Events

Check who bypasses rulesets:
1. Settings → Rules → Rulesets
2. Click on ruleset
3. View "Bypass list"

## Common Issues and Solutions

### Issue: Status checks not appearing

**Solution**: 
- Ensure workflows run on `pull_request` events
- Check workflow names match required check names exactly
- Wait for workflows to complete at least once

### Issue: Cannot merge PR despite passing checks

**Solution**:
- Verify all conversations are resolved
- Check if additional reviews are required
- Ensure branch is up to date with base

### Issue: Need to bypass ruleset for hotfix

**Solution**:
1. Request bypass from repository admin
2. Create bypass token (if configured)
3. Use bypass mechanism for critical fixes
4. Document bypass reason

## Best Practices

1. **Start with evaluate mode**: Test rulesets before enforcing
2. **Gradually increase strictness**: Add rules incrementally
3. **Document exceptions**: Keep bypass list minimal
4. **Regular reviews**: Review and update rulesets quarterly
5. **Team communication**: Notify team before enabling strict rules
6. **Emergency procedures**: Document hotfix bypass process

## Additional Resources

- [GitHub Rulesets Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets)
- [Branch Protection Best Practices](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches)
- [Status Check Configuration](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks)

## Automation Script

Save these rulesets as JSON files in `.github/rulesets/` and use the included script:

```bash
# Apply all rulesets
./tools/apply_github_rulesets.sh
```

This will apply all configured rulesets to your repository automatically.
