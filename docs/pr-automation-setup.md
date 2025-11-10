# Quick Setup Guide for PR Automation

This guide will help you quickly set up the PR automation system in your repository.

## Prerequisites

- Repository admin access
- GitHub Actions enabled
- Basic understanding of GitHub workflows

## Step 1: Enable Repository Settings

### Enable Auto-Merge

1. Go to **Settings** > **General**
2. Scroll to **Pull Requests**
3. Check **☑ Allow auto-merge**
4. Check **☑ Allow merge commits** (or squash/rebase as preferred)
5. Click **Save**

### Enable Branch Protection

1. Go to **Settings** > **Branches**
2. Click **Add rule** for `main` branch
3. Configure:
   - ☑ Require pull request reviews before merging
     - Required approving reviews: **1**
     - ☑ Dismiss stale pull request approvals when new commits are pushed
   - ☑ Require status checks to pass before merging
     - ☑ Require branches to be up to date before merging
     - Required checks: (add after first workflow run)
       - `test`
       - `security-scan`
       - `code-quality`
   - ☑ Require conversation resolution before merging
4. Click **Create**

## Step 2: Create Repository Labels

Run this script or create labels manually:

```bash
# Via GitHub CLI
gh label create "size/XS" --color "0e8a16" --description "Extra small PR"
gh label create "size/S" --color "1d76db" --description "Small PR"
gh label create "size/M" --color "fbca04" --description "Medium PR"
gh label create "size/L" --color "d93f0b" --description "Large PR"
gh label create "size/XL" --color "b60205" --description "Extra large PR"

gh label create "auto-merge" --color "0366d6" --description "Automatically merged"
gh label create "needs-review" --color "d4c5f9" --description "Needs manual review"
gh label create "high-priority" --color "b60205" --description "High priority"
gh label create "stale" --color "ededed" --description "No recent activity"

gh label create "backend" --color "0052cc" --description "Backend changes"
gh label create "frontend" --color "1d76db" --description "Frontend changes"
gh label create "database" --color "5319e7" --description "Database changes"
gh label create "documentation" --color "0075ca" --description "Documentation"
gh label create "tests" --color "d876e3" --description "Test changes"

gh label create "bug-fix" --color "d73a4a" --description "Bug fix"
gh label create "enhancement" --color "a2eeef" --description "New feature"
gh label create "security" --color "b60205" --description "Security fix"
gh label create "performance" --color "ffff00" --description "Performance improvement"
gh label create "breaking-change" --color "d93f0b" --description "Breaking change"

gh label create "dashboard" --color "e4e669" --description "Dashboard report"
gh label create "automation" --color "0366d6" --description "Automation"
gh label create "keep-open" --color "c2e0c6" --description "Don't auto-close"
gh label create "in-progress" --color "fbca04" --description "Work in progress"
gh label create "blocked" --color "d93f0b" --description "Blocked"
```

Or manually via **Issues** > **Labels** > **New label**

## Step 3: Configure CODEOWNERS

Edit `.github/CODEOWNERS` to add your team members:

```bash
# Replace @cbwinslow with actual usernames/teams

# Example:
/src/main/java/ @your-backend-team
/frontend/ @your-frontend-team
/docs/ @your-docs-team
```

For organizations, use team syntax:
```bash
/src/main/java/ @your-org/backend-team
```

## Step 4: Test the Workflows

### Test Auto-Labeling

1. Create a test branch
2. Make a small change to a Java file
3. Open a PR
4. Verify labels are automatically added

### Test Code Review

1. Open a PR with some Java code
2. Wait for the automated code review workflow
3. Check for comments with Checkstyle/PMD results
4. Verify review checklist is posted

### Test Dashboard

1. Go to **Actions** tab
2. Find "PR Management Dashboard" workflow
3. Click **Run workflow**
4. Check for new issue with dashboard report

### Test Auto-Merge (Optional)

1. Ensure Dependabot has open PRs
2. Wait for auto-merge workflow to run
3. Verify minor/patch updates are auto-approved
4. Verify major updates get warning comments

## Step 5: Customize for Your Needs

### Adjust Auto-Merge Rules

Edit `.github/workflows/auto-merge-dependabot.yml`:

```yaml
# Example: Only auto-merge patch updates
if: steps.metadata.outputs.update-type == 'version-update:semver-patch'
```

### Adjust Stale PR Timeouts

Edit `.github/workflows/pr-management-dashboard.yml`:

```yaml
days-before-stale: 30  # Change to your preference
days-before-close: 7   # Change to your preference
```

### Add Custom Labels

Edit `.github/workflows/pr-auto-labeler.yml`:

```javascript
// Example: Add label for specific directory
if (path.includes('your-custom-dir/')) {
  labels.add('your-custom-label');
}
```

### Customize Review Checklist

Edit `.github/workflows/automated-code-review.yml`:

```javascript
const checklist = `
## Your Custom Checklist
- [ ] Custom check 1
- [ ] Custom check 2
`;
```

## Step 6: Train Your Team

Share these guidelines with your team:

### For Contributors

1. **PR Title Format**: Use descriptive titles (e.g., "feat: Add federal bill API")
2. **Keep PRs Small**: Aim for < 200 lines for faster reviews
3. **Use Draft PRs**: For work-in-progress
4. **Address Feedback**: Respond to automated checks
5. **Check Review Checklist**: Complete all items

### For Reviewers

1. **Check Dashboard**: Review weekly PR summary
2. **Prioritize**: Focus on high-priority PRs first
3. **Review Quickly**: Within 2-3 days to prevent staleness
4. **Use Checklist**: Follow the automated review checklist
5. **Trust Automation**: Let auto-merge handle Dependabot minor/patch updates

## Step 7: Monitor and Adjust

### Week 1-2: Observation

- Monitor workflow runs in Actions tab
- Check for any failing workflows
- Observe which PRs get auto-merged
- Note any issues or edge cases

### Week 3-4: Refinement

- Adjust stale PR timeouts if needed
- Fine-tune auto-merge rules
- Add/remove labels based on usage
- Update CODEOWNERS as needed

### Ongoing: Optimization

- Review metrics monthly
- Gather team feedback
- Optimize workflows for your needs
- Update documentation

## Common Issues and Solutions

### Issue: Auto-merge not triggering

**Solution:**
- Verify auto-merge enabled in settings
- Check branch protection rules
- Ensure all required checks pass
- Verify PR is from Dependabot

### Issue: Labels not applying

**Solution:**
- Verify labels exist in repository
- Check workflow permissions
- Review file patterns in labeler workflow

### Issue: Too many Dependabot PRs

**Solution:**
- Reduce `open-pull-requests-limit` in `.github/dependabot.yml`
- Group updates by package ecosystem
- Schedule updates less frequently

### Issue: Dashboard not updating

**Solution:**
- Check workflow permissions
- Verify cron schedule
- Try manual trigger via Actions tab

### Issue: Stale PRs not closing

**Solution:**
- Check `stale` workflow configuration
- Verify no exempt labels are applied
- Check days-before-stale/close settings

## Verification Checklist

After setup, verify:

- [ ] Auto-merge enabled in repository settings
- [ ] Branch protection rules configured
- [ ] All required labels created
- [ ] CODEOWNERS file updated with correct usernames
- [ ] All workflows appear in Actions tab
- [ ] Test PR gets auto-labeled correctly
- [ ] Code review workflow runs on test PR
- [ ] Dashboard workflow can run manually
- [ ] Team members understand the system
- [ ] Documentation is accessible

## Next Steps

Once setup is complete:

1. **Announce to Team**: Share the [PR Automation Guide](pr-automation-guide.md)
2. **Run Training Session**: Walk through the features
3. **Monitor First Week**: Watch for issues
4. **Gather Feedback**: Ask team for input
5. **Iterate**: Adjust based on usage

## Resources

- [Full PR Automation Guide](pr-automation-guide.md) - Detailed documentation
- [GitHub Actions Docs](https://docs.github.com/en/actions) - Official documentation
- [Dependabot Docs](https://docs.github.com/en/code-security/dependabot) - Dependency updates
- [Workflow Files](.github/workflows/) - Actual workflow definitions

## Support

If you encounter issues:

1. Check workflow logs in Actions tab
2. Review this guide and the main documentation
3. Open an issue with the `automation` label
4. Contact: cbwinslow

---

**Estimated Setup Time:** 30-60 minutes
**Difficulty:** Intermediate
**Prerequisites:** Repository admin access, GitHub Actions knowledge
