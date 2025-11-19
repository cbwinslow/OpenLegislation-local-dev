# Bot PR Management Automation

## Overview

This repository uses multiple automation tools (bots) to assist with development tasks. To manage the PRs created by these bots effectively, we have implemented an automated Bot PR Management system.

## Supported Bots

The system currently recognizes and manages PRs from:

- **Dependabot** - Dependency updates
- **GitHub Copilot** - Code suggestions and fixes
- **CodeRabbit** - AI-powered code reviews
- **Jules (Google Labs)** - Code assistance
- **Keploy** - Test generation
- **CodeAnt** - Code analysis
- **Qodo Merge** - Merge automation
- **AgentFarmX** - Development automation

## Features

### 1. Automatic Labeling

Bot PRs are automatically labeled with:

- **Bot Type Labels**: `bot:dependabot`, `bot:copilot`, `bot:coderabbit`, etc.
- **Size Labels**: `size:XS`, `size:S`, `size:M`, `size:L`, `size:XL` based on lines changed
- **Type Labels**: `bug-fix`, `enhancement`, `refactoring`, `tests`, `documentation`
- **Update Type Labels** (for Dependabot): `major-update`, `minor-update`, `patch-update`

### 2. Duplicate Detection

When a new PR is opened, the system:
- Compares the title with existing open PRs
- Identifies potential duplicates
- Adds a comment listing similar PRs
- Adds a `possible-duplicate` label for manual review

This helps consolidate efforts and avoid confusion when multiple bots create PRs for the same issue.

### 3. Dependabot Auto-Merge

For Dependabot PRs, the system:

**Patch and Minor Updates:**
- Automatically approves the PR
- Waits for all CI checks to pass
- Enables auto-merge with squash strategy
- Adds `auto-merge-candidate` label

**Major Updates:**
- Adds a comment warning about potential breaking changes
- Adds `needs-review` and `major-update` labels
- Requires manual review and approval

### 4. Stale PR Management

PRs that become inactive are automatically managed:

- **After 30 days**: PR is marked as stale with a comment
- **After 37 days** (30 + 7 grace period): PR is automatically closed
- **Exemptions**: PRs with `keep-open`, `blocked`, `in-progress`, or `high-priority` labels are exempt
- **Draft PRs**: Are exempt from stale management

### 5. Bot Coordination

When multiple bots create PRs referencing the same issues:
- System detects potential conflicts
- Adds a comment listing related bot PRs
- Adds `bot-coordination-needed` label
- Recommends reviewing and consolidating approaches

### 6. PR Health Check

For all new PRs, the system checks:
- PR description quality (minimum 50 characters)
- Number of changed files (warns if >50)
- Age and staleness (warns if no updates for 7+ days)
- Merge conflict status
- Provides recommendations for improvement

## Workflow Configuration

The automation runs via `.github/workflows/bot-pr-management.yml`:

**Triggers:**
- `pull_request`: opened, synchronize, labeled, reopened, ready_for_review
- `schedule`: Daily at midnight UTC
- `workflow_dispatch`: Manual trigger

**Permissions:**
- `contents: write`
- `pull-requests: write`
- `issues: write`
- `checks: read`

## Managing Bot PRs

### For Repository Maintainers

**Reviewing Bot PRs:**
1. Check the bot type label to understand the source
2. Review the size label to estimate review effort
3. For duplicates, compare approaches and close redundant PRs
4. For Dependabot PRs, review the changelog before approving major updates

**Keeping PRs Active:**
- Add the `keep-open` label to prevent stale marking
- Add the `in-progress` label for PRs actively being worked on
- Add the `blocked` label with a comment explaining blockers

**Bot Coordination:**
- When `bot-coordination-needed` label appears, review related PRs
- Choose the best approach or combine solutions
- Close redundant PRs with a reference to the chosen solution

### For Contributors

**If Your PR is Marked Stale:**
- Comment on the PR to indicate you're still working on it
- Push new commits to show activity
- Add the `keep-open` label if you need more time

**If Your PR is Marked as Duplicate:**
- Review the similar PRs mentioned in the comment
- If yours offers a different/better approach, comment explaining why
- If it's truly duplicate, close your PR with a reference to the original

## Customization

### Adjusting Stale Timeframes

Edit `.github/workflows/bot-pr-management.yml`:

```yaml
days-before-stale: 30  # Days before marking as stale
days-before-close: 7   # Additional days before closing
```

### Exempting Labels

Add labels to the exempt list:

```yaml
exempt-pr-labels: 'keep-open,blocked,in-progress,high-priority,custom-label'
```

### Adding New Bot Detection

Add to the bot type labeling section:

```javascript
else if (author.includes('newbot')) {
  labels.add('bot:newbot');
}
```

## Monitoring

### Weekly Dashboard

A weekly PR Management Dashboard is generated every Monday at 9 AM UTC by the `pr-management-dashboard.yml` workflow. This provides:
- Summary statistics
- High priority PRs
- PRs ready to merge
- PRs needing review
- Stale PRs
- Bot PR breakdown

### Manual Trigger

You can manually trigger the bot management workflow:
1. Go to Actions tab
2. Select "Bot PR Management" workflow
3. Click "Run workflow"

## Best Practices

1. **Review Bot PRs Promptly**: Helps prevent accumulation and staleness
2. **Use Labels Effectively**: Apply `keep-open`, `blocked`, or `high-priority` as needed
3. **Consolidate Duplicates**: When bots create duplicate PRs, review and close extras
4. **Monitor Dependabot**: Review dependency updates regularly, especially major versions
5. **Provide Feedback**: If bot PRs are unhelpful, adjust bot configurations or workflows

## Troubleshooting

**Issue**: Bot PRs not being labeled
- Check workflow logs in Actions tab
- Verify bot username matches detection patterns
- Ensure required labels exist in repository

**Issue**: Dependabot PRs not auto-merging
- Check if CI checks are passing
- Verify it's a patch/minor update
- Check workflow permissions

**Issue**: False positive duplicates
- Comment explaining the difference
- Remove `possible-duplicate` label manually

**Issue**: PR closed as stale prematurely
- Reopen the PR
- Add `keep-open` label
- Comment to show activity

## Related Workflows

- `pr-auto-labeler.yml` - Labels PRs by changed files
- `pr-management-dashboard.yml` - Weekly PR summary
- `auto-merge-dependabot.yml` - Original Dependabot auto-merge (deprecated, now in bot-pr-management.yml)
- `issue-automation.yml` - Issue labeling and management

## Support

For questions or issues with bot PR management:
1. Check workflow logs in the Actions tab
2. Review this documentation
3. Open an issue with the `automation` label
4. Tag `@cbwinslow` for assistance

## Changelog

### Initial Release (November 2024)
- Automatic bot PR labeling
- Duplicate PR detection
- Dependabot auto-merge for safe updates
- Stale PR management (30-day threshold)
- Bot coordination checks
- PR health checks
