# 🤖 PR Automation System

Automated pull request management, code review, and merging system for OpenLegislation.

## 🎯 What Does This Do?

This automation system helps manage pull requests by:

1. **🔄 Auto-merging Dependabot PRs** - Safely merge dependency updates automatically
2. **🔍 Automated Code Review** - Run quality checks and provide feedback on every PR
3. **🏷️ Smart Labeling** - Automatically categorize PRs based on content and changes
4. **📊 Weekly Dashboard** - Get a comprehensive view of all open PRs
5. **⏰ Stale PR Management** - Keep the PR list clean by closing inactive PRs

## 🚀 Quick Benefits

- **Save Time**: No more manually reviewing and merging Dependabot PRs
- **Consistent Quality**: Every PR gets the same quality checks
- **Better Organization**: PRs are automatically categorized and prioritized
- **Stay on Top**: Weekly dashboard helps track what needs attention
- **Clean Repo**: Stale PRs are automatically managed

## 📁 What Was Added

### Workflows (`.github/workflows/`)

| File | Purpose |
|------|---------|
| `auto-merge-dependabot.yml` | Automatically merge safe Dependabot updates |
| `automated-code-review.yml` | Run quality checks and post feedback |
| `pr-auto-labeler.yml` | Label PRs based on changes |
| `pr-management-dashboard.yml` | Generate weekly PR summary report |

### Configuration Files

| File | Purpose |
|------|---------|
| `.github/CODEOWNERS` | Automatic reviewer assignments |

### Documentation (`.docs/`)

| File | Purpose |
|------|---------|
| `pr-automation-guide.md` | Complete guide to using the system |
| `pr-automation-setup.md` | Step-by-step setup instructions |
| `pr-automation-README.md` | This file - overview |

## 🏃 Quick Start

### For Users

**No setup required!** The automation works automatically on all PRs.

When you open a PR:
1. It will be automatically labeled
2. Code quality checks will run
3. A review checklist will be posted
4. Reviewers will be assigned (if configured)

### For Administrators

**Complete setup in 30 minutes:**

1. **Read the setup guide**: [docs/pr-automation-setup.md](pr-automation-setup.md)
2. **Enable auto-merge**: Repository Settings → Allow auto-merge
3. **Create labels**: Use provided script in setup guide
4. **Configure CODEOWNERS**: Add your team members
5. **Set branch protection**: Require reviews and checks
6. **Test it**: Open a test PR to verify

See [Setup Guide](pr-automation-setup.md) for detailed instructions.

## 📖 How It Works

### 1. Auto-Merge Workflow

```
Dependabot opens PR
         ↓
Workflow checks update type
         ↓
    ┌────┴────┐
    ↓         ↓
Minor/Patch  Major
    ↓         ↓
Auto-approve  Flag for
    ↓         review
    ↓            
Wait for CI
    ↓
Auto-merge! ✅
```

**Safety:** Only merges after all CI checks pass.

### 2. Code Review Workflow

```
PR opened/updated
         ↓
Run quality checks
    ↓    ↓    ↓
Checkstyle PMD SpotBugs
         ↓
Aggregate results
         ↓
Post feedback comment
         ↓
Add size label
         ↓
Post review checklist
```

### 3. Auto-Labeling Workflow

```
PR opened
    ↓
Analyze changed files
    ↓
Detect:
  • Backend/Frontend
  • Database changes
  • Documentation
  • Tests
  • Infrastructure
    ↓
Analyze title/description
    ↓
Detect:
  • Bug fix
  • Feature
  • Security
  • Breaking change
    ↓
Apply labels
```

### 4. Dashboard Workflow

```
Monday 9 AM UTC
         ↓
Fetch all open PRs
         ↓
Categorize by:
  • Priority
  • Status
  • Age
  • Type
         ↓
Generate report
         ↓
Create/update issue
```

## 🎨 Available Labels

### Size Labels
- `size/XS` - < 10 lines
- `size/S` - 10-50 lines
- `size/M` - 50-200 lines
- `size/L` - 200-500 lines
- `size/XL` - > 500 lines

### Type Labels
- `bug-fix` - Bug fixes
- `enhancement` - New features
- `refactoring` - Code improvements
- `breaking-change` - Breaking changes
- `security` - Security fixes
- `performance` - Performance improvements

### Component Labels
- `backend` - Java/backend changes
- `frontend` - UI/React changes
- `database` - Database/SQL changes
- `api` - API endpoint changes
- `documentation` - Docs changes
- `tests` - Test changes
- `ci-cd` - GitHub Actions changes
- `infrastructure` - Infra/deployment changes

### Status Labels
- `needs-review` - Awaiting review
- `auto-merge` - Will auto-merge
- `high-priority` - Urgent
- `stale` - No recent activity
- `keep-open` - Don't auto-close
- `in-progress` - Work in progress
- `blocked` - Blocked

## 📊 Metrics & Monitoring

### View Workflow Runs
Go to **Actions** tab to see:
- Workflow success/failure rates
- Execution times
- Logs for debugging

### View Dashboard
Check for issues with label `dashboard` to see:
- Open PR summary
- PRs by category
- Weekly statistics

### Key Metrics to Track
1. **Time to merge** - How long PRs stay open
2. **Auto-merge rate** - % of Dependabot PRs auto-merged
3. **Review coverage** - % of PRs reviewed on time
4. **Stale PR trend** - Growing or shrinking?

## 🔧 Customization

### Adjust Auto-Merge Rules

Edit `.github/workflows/auto-merge-dependabot.yml`:

```yaml
# Only auto-merge patch updates
if: steps.metadata.outputs.update-type == 'version-update:semver-patch'
```

### Change Stale PR Timeouts

Edit `.github/workflows/pr-management-dashboard.yml`:

```yaml
days-before-stale: 45  # Instead of 30
days-before-close: 14  # Instead of 7
```

### Add Custom Labels

Edit `.github/workflows/pr-auto-labeler.yml`:

```javascript
// Add your custom logic
if (path.includes('your-directory/')) {
  labels.add('your-label');
}
```

### Disable a Workflow

Rename the workflow file or add:

```yaml
on:
  workflow_dispatch: # Manual trigger only
```

## 🤔 Common Questions

### Q: Will this auto-merge my code PRs?
**A:** No, only Dependabot dependency updates (minor/patch versions).

### Q: Can I disable auto-merge for a specific dependency?
**A:** Yes, add it to the `ignore` section in `.github/dependabot.yml`.

### Q: What if I want to review a Dependabot PR?
**A:** Major version updates require manual review. For others, add the `needs-review` label.

### Q: How do I prevent a PR from being closed as stale?
**A:** Add the `keep-open` or `in-progress` label.

### Q: Can I customize the review checklist?
**A:** Yes, edit the checklist in `.github/workflows/automated-code-review.yml`.

### Q: How do I add more reviewers?
**A:** Update `.github/CODEOWNERS` with usernames or team names.

### Q: What if the automated checks fail?
**A:** The PR won't auto-merge. Fix the issues and the checks will re-run.

### Q: Can I run the dashboard more frequently?
**A:** Yes, change the cron schedule in `pr-management-dashboard.yml`.

## 🐛 Troubleshooting

### Auto-merge not working

1. ✅ Check auto-merge enabled in Settings → General
2. ✅ Verify branch protection rules
3. ✅ Ensure all required checks pass
4. ✅ Confirm PR is from Dependabot
5. ✅ Check workflow logs in Actions tab

### Labels not applying

1. ✅ Verify labels exist in repository
2. ✅ Check workflow has `pull-requests: write` permission
3. ✅ Review file patterns in auto-labeler workflow
4. ✅ Check workflow logs for errors

### Code review not posting comments

1. ✅ Verify Maven build succeeds
2. ✅ Check Checkstyle/PMD plugins in pom.xml
3. ✅ Ensure Java 17 is used
4. ✅ Review workflow logs

### Dashboard not updating

1. ✅ Check workflow has `issues: write` permission
2. ✅ Verify cron schedule is correct
3. ✅ Try manual trigger via Actions tab
4. ✅ Check for existing dashboard issue

## 📚 Documentation

- **[Setup Guide](pr-automation-setup.md)** - Detailed setup instructions
- **[Full Guide](pr-automation-guide.md)** - Complete documentation
- **[GitHub Actions Docs](https://docs.github.com/en/actions)** - Official GitHub docs
- **[Dependabot Docs](https://docs.github.com/en/code-security/dependabot)** - Dependency updates

## 🎯 Best Practices

### For Contributors
- ✅ Keep PRs small (< 200 lines)
- ✅ Use descriptive titles
- ✅ Draft PRs for work-in-progress
- ✅ Address automated feedback
- ✅ Complete review checklist

### For Reviewers
- ✅ Review within 2-3 days
- ✅ Check weekly dashboard
- ✅ Prioritize high-priority PRs
- ✅ Trust automation for Dependabot
- ✅ Use review checklist

### For Maintainers
- ✅ Monitor workflow runs
- ✅ Update CODEOWNERS regularly
- ✅ Review metrics monthly
- ✅ Adjust settings as needed
- ✅ Keep documentation current

## 🔄 Maintenance

### Weekly
- Review PR dashboard
- Check for failing workflows
- Merge approved PRs

### Monthly
- Review automation metrics
- Update CODEOWNERS if needed
- Adjust stale PR settings
- Gather team feedback

### Quarterly
- Optimize workflow performance
- Update documentation
- Train new team members
- Review and refine labels

## 🆘 Support

Need help?

1. **Check Documentation**: [Setup Guide](pr-automation-setup.md) or [Full Guide](pr-automation-guide.md)
2. **Check Workflow Logs**: Actions tab → Failed workflow → View logs
3. **Search Issues**: Look for similar issues with `automation` label
4. **Open Issue**: Create new issue with `automation` label
5. **Contact**: @cbwinslow

## 📈 Success Metrics

After implementing this system, you should see:

- ⬇️ **50-70% reduction** in manual PR reviews (Dependabot)
- ⬇️ **30-40% reduction** in time to merge
- ⬆️ **Consistent code quality** checks on all PRs
- ⬆️ **Better PR organization** with labels
- ⬆️ **Fewer stale PRs** in the backlog

## 🎉 What's Next?

1. **Complete Setup**: Follow [Setup Guide](pr-automation-setup.md)
2. **Train Team**: Share [Full Guide](pr-automation-guide.md)
3. **Monitor**: Watch workflows for first week
4. **Optimize**: Adjust based on your workflow
5. **Expand**: Add more custom rules as needed

## 📝 License

Same as the main OpenLegislation repository (Dual BSD/GPL).

## 🙏 Credits

Built with:
- GitHub Actions
- GitHub Scripts
- Dependabot
- Community best practices

---

**Questions?** Open an issue with the `automation` label
**Feedback?** We'd love to hear how this works for you!
