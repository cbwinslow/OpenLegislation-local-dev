# PR Automation Quick Reference

Quick reference card for the PR automation system.

## 🚀 For Contributors

### Opening a PR

1. **Title Format**: Use clear, descriptive titles
   - ✅ `feat: Add federal bill ingestion API`
   - ✅ `fix: Resolve database migration issue`
   - ✅ `docs: Update API documentation`
   - ❌ `Update code`
   - ❌ `Fixed bug`

2. **What Happens Automatically**:
   - ✅ PR gets labeled based on files changed
   - ✅ Size label added (XS, S, M, L, XL)
   - ✅ Code quality checks run
   - ✅ Review checklist posted
   - ✅ Reviewers assigned (via CODEOWNERS)

3. **Keeping PR Small**:
   - 🎯 Aim for `size/S` or `size/M` (< 200 lines)
   - 🎯 Break large changes into multiple PRs
   - 🎯 One feature/fix per PR

### During Review

1. **Address Automated Feedback**:
   - Fix Checkstyle issues
   - Resolve PMD warnings
   - Fix SpotBugs findings

2. **Complete Review Checklist**:
   - Check off items as you complete them
   - Add comments for items that don't apply

3. **Draft PRs**:
   - Use draft status for work-in-progress
   - Mark "Ready for review" when complete

### Preventing Auto-Close

If your PR needs to stay open longer:
- Add label: `keep-open` or `in-progress`
- Comment regularly to show activity

## 👀 For Reviewers

### Daily Tasks

1. **Check Notifications**: Review assigned PRs
2. **Use Checklist**: Follow automated review checklist
3. **Review Within 2-3 Days**: Keep PRs moving

### Weekly Tasks

1. **Check Dashboard**: Review weekly PR summary issue
2. **Prioritize**: Focus on high-priority PRs first
3. **Close Stale**: Clean up old, inactive PRs

### Review Guidelines

- ✅ All checklist items completed
- ✅ Code quality checks pass
- ✅ Tests added/updated
- ✅ Documentation updated
- ✅ No security issues

### Trust Automation

- ✅ Dependabot minor/patch updates: Let auto-merge handle
- ✅ Major updates: Review carefully
- ✅ Code quality checks: Address issues before approving

## 🔧 For Maintainers

### Weekly Maintenance

**Monday Morning**:
1. Check PR dashboard issue
2. Prioritize high-priority PRs
3. Assign additional reviewers if needed

**Throughout Week**:
1. Monitor workflow runs in Actions tab
2. Merge approved PRs
3. Close/update stale PRs

### Monthly Maintenance

1. **Review Metrics**:
   - Time to merge
   - Auto-merge rate
   - Review coverage
   - Stale PR trends

2. **Update Configuration**:
   - Adjust CODEOWNERS
   - Refine auto-merge rules
   - Update labels
   - Tune stale timeouts

3. **Team Feedback**:
   - Gather input
   - Identify pain points
   - Adjust workflows

### Quarterly Maintenance

1. Review overall effectiveness
2. Update documentation
3. Train new team members
4. Optimize workflow performance

## 🏷️ Label Reference

### Size Labels (Auto-applied)
- `size/XS` - < 10 lines
- `size/S` - 10-50 lines
- `size/M` - 50-200 lines
- `size/L` - 200-500 lines
- `size/XL` - > 500 lines

### Type Labels (Auto-applied)
- `bug-fix` - Bug fixes
- `enhancement` - New features
- `security` - Security fixes
- `performance` - Performance improvements
- `breaking-change` - Breaking changes

### Component Labels (Auto-applied)
- `backend` - Java/backend code
- `frontend` - UI/React code
- `database` - SQL/database changes
- `api` - API endpoints
- `documentation` - Docs
- `tests` - Test code
- `ci-cd` - Workflow changes
- `infrastructure` - Infra/deployment

### Status Labels (Manual/Auto)
- `needs-review` - Awaiting review
- `auto-merge` - Will auto-merge
- `high-priority` - Urgent
- `stale` - No recent activity
- `keep-open` - Don't auto-close
- `in-progress` - WIP
- `blocked` - Blocked

## ⚡ Quick Commands

### Via GitHub CLI

```bash
# Create PR
gh pr create --title "feat: My feature" --body "Description"

# Add label
gh pr edit <number> --add-label "high-priority"

# Request review
gh pr edit <number> --add-reviewer @username

# Enable auto-merge
gh pr merge <number> --auto --squash

# Check status
gh pr status

# View checks
gh pr checks <number>
```

### Via Git

```bash
# Create branch
git checkout -b feature/my-feature

# Commit changes
git add .
git commit -m "feat: My feature"

# Push and create PR
git push -u origin feature/my-feature
# Then create PR via GitHub UI
```

## 🔍 Workflow Triggers

### Auto-Merge Dependabot
- **Triggers**: When Dependabot opens/updates PR
- **Actions**: Auto-approve minor/patch, flag major

### Automated Code Review
- **Triggers**: PR opened/synchronized/reopened
- **Actions**: Run checks, post feedback, add labels

### PR Auto-Labeler
- **Triggers**: PR opened/synchronized/reopened
- **Actions**: Analyze files, apply labels

### PR Management Dashboard
- **Triggers**: Weekly (Monday 9 AM UTC) or manual
- **Actions**: Generate report, update issue

## 🐛 Common Issues

### PR Not Auto-Merging

**Check**:
1. ✅ All CI checks passing?
2. ✅ Required approvals received?
3. ✅ Branch up to date?
4. ✅ Auto-merge enabled in repo?

**Fix**:
- Wait for checks to complete
- Get required approvals
- Update branch: `git pull origin main`

### Labels Not Applying

**Check**:
1. ✅ Workflow ran in Actions tab?
2. ✅ Labels exist in repository?
3. ✅ Files changed match patterns?

**Fix**:
- Manually add labels if needed
- Check workflow logs for errors

### Code Checks Failing

**Check**:
1. ✅ Build passes locally?
2. ✅ Checkstyle/PMD/SpotBugs configured?
3. ✅ Java version correct (17)?

**Fix**:
- Run locally: `mvn checkstyle:check pmd:check spotbugs:check`
- Fix reported issues
- Push changes

## 📞 Getting Help

### Resources
- 📚 [Full Guide](pr-automation-guide.md)
- 🚀 [Setup Guide](pr-automation-setup.md)
- 📖 [Overview](pr-automation-README.md)

### Support
1. Check workflow logs in Actions tab
2. Search issues with `automation` label
3. Create issue with `automation` label
4. Contact: @cbwinslow

## 💡 Pro Tips

### For Faster Reviews
1. Keep PRs small (< 200 lines)
2. Write clear description
3. Add screenshots for UI changes
4. Link related issues
5. Request specific reviewers

### For Better Quality
1. Run checks locally first
2. Address automated feedback
3. Write/update tests
4. Update documentation
5. Follow style guidelines

### For Efficient Management
1. Use draft PRs for WIP
2. Respond to feedback promptly
3. Keep PRs up to date
4. Close PRs you won't finish
5. Communicate blockers

## 📊 Metrics Dashboard

### View PR Dashboard
1. Go to **Issues** tab
2. Filter by label: `dashboard`
3. Open latest dashboard issue

### View Workflow Runs
1. Go to **Actions** tab
2. Select workflow
3. View runs and logs

### Check PR Status
```bash
# Via GitHub CLI
gh pr status

# View specific PR
gh pr view <number>
```

## ⚙️ Configuration Files

### Workflows
- `.github/workflows/auto-merge-dependabot.yml`
- `.github/workflows/automated-code-review.yml`
- `.github/workflows/pr-auto-labeler.yml`
- `.github/workflows/pr-management-dashboard.yml`

### Configuration
- `.github/CODEOWNERS` - Reviewer assignments
- `.github/dependabot.yml` - Dependency updates

### Documentation
- `docs/pr-automation-README.md` - Overview
- `docs/pr-automation-guide.md` - Full guide
- `docs/pr-automation-setup.md` - Setup guide
- `docs/pr-automation-quick-reference.md` - This file

---

**Last Updated**: 2025-11-04
**Version**: 1.0
**Contact**: @cbwinslow
