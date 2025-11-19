# PR Automation Guide

This guide explains the automated PR management, code review, and merging system implemented in this repository.

## Overview

The repository uses GitHub Actions to automate:
- 🤖 **Automatic PR merging** for low-risk changes (Dependabot updates)
- 🔍 **Automated code review** with quality checks and feedback
- 🏷️ **Smart PR labeling** based on changed files and content
- 📊 **PR management dashboard** for tracking and prioritizing PRs
- ⏰ **Stale PR management** to keep the PR list clean

## Features

### 1. Auto-Merge for Dependabot PRs

**Workflow:** `.github/workflows/auto-merge-dependabot.yml`

Automatically handles Dependabot dependency update PRs:

- **Minor/Patch Updates**: Automatically approved and merged if all checks pass
- **Major Updates**: Flagged for manual review with warning comment
- **Labels**: Automatically labeled based on update type
- **Safety**: Only merges after all CI checks pass

**How it works:**
1. Dependabot opens a PR
2. Workflow detects the update type (major/minor/patch)
3. For minor/patch: auto-approves and enables auto-merge
4. For major: adds "needs-review" label and warning comment
5. PR merges automatically when all required checks pass

**To disable auto-merge for specific dependencies:**
Edit `.github/dependabot.yml` and add to the `ignore` section.

### 2. Automated Code Review

**Workflow:** `.github/workflows/automated-code-review.yml`

Provides automated code quality checks and feedback:

#### Quality Checks
- **Checkstyle**: Enforces code style standards
- **PMD**: Detects potential code issues
- **SpotBugs**: Finds bugs using static analysis
- **Complexity Analysis**: Reports on code complexity

#### PR Size Labeling
Automatically labels PRs by size:
- `size/XS`: < 10 lines changed
- `size/S`: 10-50 lines
- `size/M`: 50-200 lines
- `size/L`: 200-500 lines
- `size/XL`: > 500 lines (triggers warning comment)

#### Review Checklist
Posts a comprehensive checklist for reviewers covering:
- Code quality
- Functionality
- Security
- Testing
- Documentation

**Configuration:**
The workflow runs on all PRs targeting `main` or `develop` branches.

### 3. PR Auto-Labeling

**Workflow:** `.github/workflows/pr-auto-labeler.yml`

Automatically labels PRs based on:

#### File-based Labels
- `backend`: Java code changes
- `frontend`: UI/React changes
- `database`: SQL migrations or database code
- `documentation`: Markdown/docs changes
- `tests`: Test file changes
- `ci-cd`: GitHub Actions workflow changes
- `infrastructure`: Ansible/Docker/infra changes
- `tooling`: Tools directory changes

#### Content-based Labels
- `bug-fix`: Title contains "fix" or "bug"
- `enhancement`: Title contains "feat" or "feature"
- `security`: Security-related changes (high priority)
- `performance`: Performance improvements
- `breaking-change`: Breaking changes (needs review)
- `high-priority`: Urgent/critical changes

#### Component Labels
- `api`: API endpoint changes
- `data-processing`: Data processor changes
- `federal-integration`: Federal data integration

### 4. Code Owners

**File:** `.github/CODEOWNERS`

Defines code ownership for automatic review assignments:

- Backend Java code → Backend team
- API endpoints → API team
- Federal integration → Federal team
- Database migrations → Database team
- Infrastructure → DevOps team

**To configure:**
Edit `.github/CODEOWNERS` and replace `@cbwinslow` with actual team/user names.

### 5. PR Management Dashboard

**Workflow:** `.github/workflows/pr-management-dashboard.yml`

Generates a weekly PR summary report:

#### Dashboard Sections
1. **High Priority PRs**: Urgent/critical PRs
2. **Approved PRs**: Ready to merge
3. **PRs Needing Review**: Awaiting reviewer attention
4. **Dependabot PRs**: Automated dependency updates
5. **Stale PRs**: No activity in 7+ days
6. **Draft PRs**: Work in progress

#### Schedule
- Runs every Monday at 9 AM UTC
- Can be triggered manually via workflow_dispatch

#### Stale PR Management
- Marks PRs as stale after 30 days of inactivity
- Closes stale PRs after 7 more days
- Exempt labels: `keep-open`, `in-progress`, `blocked`

## Configuration

### Branch Protection Rules

Recommended settings for `main` branch:

1. **Require pull request reviews before merging**
   - Required approving reviews: 1
   - Dismiss stale reviews: Enabled
   - Require review from Code Owners: Enabled

2. **Require status checks to pass**
   - Require branches to be up to date: Enabled
   - Required checks:
     - `test` (from CI/CD)
     - `security-scan`
     - `code-quality`

3. **Require conversation resolution before merging**

4. **Enable auto-merge**

5. **Allow merge queue**
   - Use merge queue: Enabled
   - Group pull requests: Enabled

### Setting Up Auto-Merge

To enable auto-merge in the repository:

```bash
# Via GitHub CLI
gh repo edit --enable-auto-merge

# Or via Settings > General > Pull Requests
# Check "Allow auto-merge"
```

### Customizing Labels

Create these labels in your repository (Settings > Labels):

**Size Labels:**
- `size/XS`, `size/S`, `size/M`, `size/L`, `size/XL`

**Type Labels:**
- `bug-fix`, `enhancement`, `refactoring`, `breaking-change`

**Component Labels:**
- `backend`, `frontend`, `database`, `api`, `ci-cd`

**Priority Labels:**
- `high-priority`, `needs-review`

**Auto Labels:**
- `auto-merge`, `dependencies`, `stale`

**Other Labels:**
- `dashboard`, `automation`, `keep-open`, `in-progress`, `blocked`

## Usage Examples

### Example 1: Dependabot PR Auto-Merge

```yaml
# Dependabot opens PR: "Bump spring-boot from 2.7.0 to 2.7.1"
# ↓
# Auto-merge workflow runs
# ↓
# Detects: Minor version update
# ↓
# Auto-approves PR
# ↓
# Enables auto-merge
# ↓
# Waits for CI checks to pass
# ↓
# PR automatically merged!
```

### Example 2: Manual PR with Auto-Review

```yaml
# Developer opens PR: "Add federal bill ingestion endpoint"
# ↓
# Auto-labeler adds: backend, api, federal-integration
# ↓
# Code review workflow runs checks:
#   - Checkstyle: ✅ Pass
#   - PMD: ❌ 3 issues found
#   - SpotBugs: ✅ Pass
# ↓
# Posts comment with results and review checklist
# ↓
# CODEOWNERS assigns reviewers automatically
# ↓
# Developer fixes PMD issues
# ↓
# Re-runs checks automatically
# ↓
# Reviewer approves
# ↓
# PR merged!
```

### Example 3: Weekly Dashboard

```yaml
# Monday 9 AM UTC
# ↓
# Dashboard workflow runs
# ↓
# Scans all open PRs
# ↓
# Categorizes by status
# ↓
# Creates/updates dashboard issue
# ↓
# Team reviews dashboard
# ↓
# Prioritizes PRs for the week
```

## Best Practices

### For Contributors

1. **Keep PRs small**: Aim for `size/S` or `size/M` for faster reviews
2. **Use descriptive titles**: Help auto-labeling work correctly
3. **Draft PRs**: Use draft status for work-in-progress
4. **Review checklist**: Address all items before requesting review
5. **Respond to automated feedback**: Fix issues found by automated checks

### For Maintainers

1. **Review dashboard weekly**: Prioritize high-priority and approved PRs
2. **Keep PRs moving**: Review within 2-3 days to prevent staleness
3. **Update CODEOWNERS**: Keep ownership assignments current
4. **Monitor auto-merge**: Occasionally audit auto-merged PRs
5. **Adjust thresholds**: Tune stale PR timeouts based on your workflow

### For Dependabot PRs

1. **Let automation work**: Don't manually merge Dependabot minor/patch updates
2. **Review major updates**: Always review major version bumps manually
3. **Group updates**: Dependabot can group updates - configure in `dependabot.yml`
4. **Test after merge**: Automated tests should catch issues, but verify in staging

## Troubleshooting

### Auto-merge not working

**Check:**
1. Auto-merge enabled in repository settings?
2. Branch protection rules configured correctly?
3. All required status checks passing?
4. PR approved by required reviewers?

### Labels not applying

**Check:**
1. Workflow permissions in `.github/workflows/*.yml`
2. Labels exist in repository
3. Changed files match patterns in auto-labeler workflow

### Code review workflow failing

**Check:**
1. Maven build succeeds locally?
2. Checkstyle/PMD/SpotBugs plugins configured in `pom.xml`?
3. Java version matches (17)?

### Dashboard not updating

**Check:**
1. Workflow has `issues: write` permission
2. Schedule cron expression correct
3. Can trigger manually via Actions tab

## Advanced Configuration

### Custom Review Rules

Add custom review logic in `.github/workflows/automated-code-review.yml`:

```javascript
// Example: Require security review for auth changes
if (files.some(f => f.filename.includes('/auth/'))) {
  await github.rest.pulls.requestReviewers({
    owner: context.repo.owner,
    repo: context.repo.repo,
    pull_number: context.issue.number,
    reviewers: ['security-team']
  });
}
```

### Merge Queue Configuration

Configure merge queue (GitHub Enterprise feature):

```yaml
# .github/merge_queue.yml
name: Merge Queue
on:
  merge_group:

jobs:
  validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run all checks
        run: mvn verify
```

### Slack Notifications

Add Slack notifications for PR events:

```yaml
- name: Notify Slack
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "PR #${{ github.event.pull_request.number }} is ready for review"
      }
```

## Monitoring

### Key Metrics to Track

1. **Time to merge**: How long PRs stay open
2. **Review coverage**: % of PRs reviewed within SLA
3. **Auto-merge rate**: % of Dependabot PRs auto-merged
4. **Stale PR count**: Trend over time
5. **Code quality trends**: Issues found by automated checks

### GitHub Insights

Use GitHub's built-in insights:
- Insights > Pull requests > Time to merge
- Insights > Contributors > PR activity
- Actions > Workflow runs > Success rate

## Support

For issues or questions:
1. Check workflow logs in Actions tab
2. Review this documentation
3. Open an issue with `automation` label
4. Contact repository maintainers

## Related Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Dependabot Configuration](https://docs.github.com/en/code-security/dependabot)
- [Code Owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Branch Protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches)
