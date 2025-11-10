# Bot PR Management - Quick Reference Guide

## 🚀 Quick Start

**What is it?** Automated system to manage PRs from 8+ bots (Dependabot, Copilot, CodeRabbit, Jules, etc.)

**Where is it?** `.github/workflows/bot-pr-management.yml`

**When does it run?** 
- Automatically on every PR event (open, update, label)
- Daily at midnight UTC for stale management
- Manually via Actions → "Bot PR Management" → "Run workflow"

## 🏷️ Label Reference

### Bot Type Labels
| Label | Bot |
|-------|-----|
| `bot:dependabot` | Dependency updates |
| `bot:copilot` | Code suggestions |
| `bot:coderabbit` | AI reviews |
| `bot:jules` | Development assistant |
| `bot:keploy` | Test generation |
| `bot:codeant` | Code analysis |
| `bot:qodo-merge` | Merge automation |
| `bot:agentfarmx` | Development automation |

### Size Labels (by lines changed)
- `size:XS` - Less than 10 lines
- `size:S` - 10-99 lines
- `size:M` - 100-499 lines
- `size:L` - 500-999 lines
- `size:XL` - 1000+ lines

### Status Labels
- `auto-merge-candidate` - Safe to auto-merge (Dependabot patch/minor)
- `needs-review` - Requires manual review (major updates)
- `possible-duplicate` - Similar to another open PR
- `bot-coordination-needed` - Multiple bots on same issue
- `stale` - No activity for 30+ days

### Type Labels
- `bug-fix` - Fixes a bug
- `enhancement` - New feature
- `refactoring` - Code cleanup
- `tests` - Test changes
- `documentation` - Doc updates

## ⚡ Common Scenarios

### Dependabot PR Created
1. ✅ Auto-labeled with bot type and size
2. 🔍 Update type detected (major/minor/patch)
3. 🤖 **Patch/Minor**: Auto-approved → CI checks → Auto-merged
4. ⚠️ **Major**: Flagged for review with warning comment

### Copilot/Bot PR Created
1. ✅ Auto-labeled with bot type and size
2. 🔍 Checked for duplicates
3. 🔍 Checked for bot coordination issues
4. 🏥 Health check performed
5. 📝 Ready for manual review

### PR Goes Stale
1. ⏰ 30 days no activity → Marked as `stale`
2. 📝 Comment added explaining next steps
3. ⏰ 37 days total → Automatically closed
4. 🛡️ Can prevent with `keep-open` label

### Multiple Bots on Same Issue
1. 🤖 Bot coordination detects conflict
2. 📝 Comment lists related bot PRs
3. 🏷️ `bot-coordination-needed` label added
4. 👤 Maintainer reviews and consolidates

## 🛡️ Exemption Labels

Add these labels to prevent automatic actions:

- `keep-open` - Never mark as stale
- `blocked` - Waiting on external dependency
- `in-progress` - Actively being worked on
- `high-priority` - Important, don't close

## 🎛️ Manual Controls

### Manually Trigger Workflow
1. Go to **Actions** tab
2. Select **"Bot PR Management"**
3. Click **"Run workflow"**
4. Select branch (usually `main`)
5. Click **"Run workflow"** button

### Force Re-labeling a PR
1. Remove all bot-related labels
2. Close and reopen the PR
3. Or manually trigger workflow with PR number

### Prevent Auto-Merge
1. Add `needs-review` label to Dependabot PR
2. Or close and manually create new PR

### Keep Stale PR Open
1. Add `keep-open` label
2. Or add any comment to reset activity timer
3. Or push new commits

## 📊 Dashboard Access

**Weekly PR Dashboard** runs every Monday at 9 AM UTC:
- Go to Issues tab
- Look for "PR Management Dashboard" issue
- View categorized PR summary

## 🔧 Customization

### Change Stale Timeframes
Edit `.github/workflows/bot-pr-management.yml`:
```yaml
days-before-stale: 30  # Change this
days-before-close: 7   # Change this
```

### Add Exempt Labels
```yaml
exempt-pr-labels: 'keep-open,blocked,in-progress,high-priority,YOUR-LABEL'
```

### Adjust Auto-Merge Criteria
Modify `auto-merge-dependabot` job conditions:
```yaml
if: |
  steps.metadata.outputs.update-type == 'version-update:semver-patch'
  # Add more conditions here
```

## 🐛 Troubleshooting

### PR Not Auto-Labeled
**Check:**
- Is author username in bot patterns?
- Check workflow logs in Actions tab
- Verify PR is not draft

**Fix:**
- Add bot username to detection patterns
- Manually trigger workflow

### Dependabot Not Auto-Merging
**Check:**
- Is it patch/minor update? (Major requires manual review)
- Are all CI checks passing?
- Is `needs-review` label present?

**Fix:**
- Wait for CI to complete
- Remove `needs-review` if added by mistake
- Check workflow logs for errors

### False Duplicate Detection
**Check:**
- Are titles actually similar?
- Is it coincidental overlap?

**Fix:**
- Comment explaining the difference
- Remove `possible-duplicate` label
- Adjust title to be more distinct

### PR Marked Stale Too Early
**Check:**
- When was last activity?
- Is it truly inactive?

**Fix:**
- Add `keep-open` label
- Comment or push commits
- Reopen if already closed

## 📞 Getting Help

1. **Check workflow logs**: Actions tab → Bot PR Management → Latest run
2. **Review documentation**: 
   - Full guide: `docs/bot-pr-management.md`
   - Diagrams: `docs/bot-pr-workflow-diagram.md`
   - Overview: `docs/automation-summary.md`
3. **Open issue**: Label with `automation` and tag maintainers
4. **Check past issues**: Search for similar problems

## 📈 Monitoring

### Check Workflow Status
```bash
# View recent workflow runs
gh run list --workflow=bot-pr-management.yml --limit 10

# View specific run details
gh run view <run-id>

# Download logs
gh run download <run-id>
```

### List Bot PRs
```bash
# All bot PRs
gh pr list --label "bot:*"

# Specific bot
gh pr list --label "bot:dependabot"

# Stale PRs
gh pr list --label "stale"

# Auto-merge candidates
gh pr list --label "auto-merge-candidate"
```

## 💡 Best Practices

### For Maintainers
1. ✅ Review bot PRs weekly
2. ✅ Consolidate duplicates promptly
3. ✅ Monitor auto-merge results
4. ✅ Keep exempt labels updated
5. ✅ Review stale PRs before closure

### For Contributors
1. ✅ Keep PRs active with updates
2. ✅ Add `keep-open` if need more time
3. ✅ Check duplicate warnings
4. ✅ Respond to health check recommendations
5. ✅ Request review when ready

## 🔗 Related Workflows

- `pr-auto-labeler.yml` - Labels by changed files
- `pr-management-dashboard.yml` - Weekly summary
- `issue-automation.yml` - Issue management
- `dependabot.yml` - Dependabot config

## 📝 Feedback

Found a bug? Have a suggestion?
1. Open issue with `automation` label
2. Describe the problem or enhancement
3. Tag with `bot-pr-management`
4. Assign to maintainers

---

**Version:** 1.0  
**Last Updated:** November 2024  
**Maintainer:** OpenLegislation Team
