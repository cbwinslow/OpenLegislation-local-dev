# PR Automation Troubleshooting Guide

Common issues and solutions for the PR automation system.

## Table of Contents
1. [Auto-Merge Issues](#auto-merge-issues)
2. [Labeling Issues](#labeling-issues)
3. [Code Review Issues](#code-review-issues)
4. [Dashboard Issues](#dashboard-issues)
5. [Workflow Permission Issues](#workflow-permission-issues)
6. [Performance Issues](#performance-issues)
7. [General Debugging](#general-debugging)

---

## Auto-Merge Issues

### Issue: Auto-merge not triggering for Dependabot PRs

**Symptoms:**
- Dependabot PR opens but doesn't get auto-approved
- No auto-merge comment appears
- PR stays open even after checks pass

**Possible Causes & Solutions:**

1. **Auto-merge not enabled in repository**
   ```bash
   # Check status
   gh repo view --json autoMergeAllowed
   
   # Fix: Enable in Settings > General > Pull Requests
   # Check "Allow auto-merge"
   ```

2. **Workflow permissions insufficient**
   ```yaml
   # Check .github/workflows/auto-merge-dependabot.yml has:
   permissions:
     contents: write
     pull-requests: write
   ```

3. **Required status checks not passing**
   ```bash
   # Check PR checks
   gh pr checks <PR_NUMBER>
   
   # View details
   gh pr view <PR_NUMBER> --json statusCheckRollup
   ```

4. **Branch protection rules blocking**
   ```bash
   # Check branch protection
   gh api repos/:owner/:repo/branches/main/protection
   
   # Ensure required checks are configured correctly
   ```

5. **Major version update (by design)**
   - Major updates require manual review
   - Check PR labels for "needs-review"
   - Review and approve manually

**Debug Steps:**
```bash
# 1. Check workflow ran
gh run list --workflow=auto-merge-dependabot.yml

# 2. View specific run
gh run view <RUN_ID>

# 3. Check workflow logs
gh run view <RUN_ID> --log

# 4. Verify PR is from Dependabot
gh pr view <PR_NUMBER> --json author
```

### Issue: Auto-merge enabling but not completing

**Symptoms:**
- Auto-merge enabled but PR never merges
- All checks pass but PR stays open

**Solutions:**

1. **Branch not up to date**
   ```bash
   # Update branch
   gh pr review <PR_NUMBER> --approve
   # Then the bot should update the branch
   ```

2. **Approval not counted**
   ```bash
   # Check approvals
   gh pr view <PR_NUMBER> --json reviewDecision,reviews
   
   # Manually approve if needed
   gh pr review <PR_NUMBER> --approve
   ```

3. **Merge conflicts**
   ```bash
   # Check for conflicts
   gh pr view <PR_NUMBER> --json mergeable
   
   # If conflicts, update branch or close/reopen PR
   ```

---

## Labeling Issues

### Issue: Labels not being applied to PRs

**Symptoms:**
- PR opens but no labels appear
- Some labels apply but not others

**Solutions:**

1. **Labels don't exist in repository**
   ```bash
   # List existing labels
   gh label list
   
   # Create missing labels (see github-settings-configuration.md)
   gh label create "size/XS" --color "0e8a16"
   ```

2. **Workflow didn't run**
   ```bash
   # Check if workflow ran
   gh run list --workflow=pr-auto-labeler.yml --branch <BRANCH>
   
   # Trigger manually
   gh workflow run pr-auto-labeler.yml
   ```

3. **Workflow permissions**
   ```yaml
   # Ensure workflow has:
   permissions:
     pull-requests: write
   ```

4. **File patterns not matching**
   - Edit `.github/workflows/pr-auto-labeler.yml`
   - Check file path patterns
   - Test with actual changed files

**Debug Steps:**
```bash
# 1. List changed files in PR
gh pr diff <PR_NUMBER> --name-only

# 2. Check workflow logs
gh run list --workflow=pr-auto-labeler.yml
gh run view <RUN_ID> --log

# 3. Manually add label to test
gh pr edit <PR_NUMBER> --add-label "backend"
```

### Issue: Wrong labels being applied

**Solutions:**

1. **Review labeling logic**
   - Check `.github/workflows/pr-auto-labeler.yml`
   - Verify file path matching patterns
   - Adjust patterns as needed

2. **Multiple rules matching**
   - This is expected - PRs can have multiple labels
   - If too many labels, make patterns more specific

3. **Title/description patterns too broad**
   ```javascript
   // Example fix in workflow:
   // Make patterns more specific
   if (title.toLowerCase().includes('fix bug')) {
     // instead of just 'fix'
   }
   ```

---

## Code Review Issues

### Issue: Code quality checks not running

**Symptoms:**
- No automated review comment posted
- Checkstyle/PMD/SpotBugs not executing

**Solutions:**

1. **Maven plugins not configured**
   ```bash
   # Check pom.xml has required plugins
   grep -A 10 "maven-checkstyle-plugin" pom.xml
   grep -A 10 "maven-pmd-plugin" pom.xml
   
   # Test locally
   mvn checkstyle:check
   mvn pmd:check
   mvn spotbugs:check
   ```

2. **Java version mismatch**
   ```yaml
   # Check workflow uses correct Java version
   - name: Set up JDK
     uses: actions/setup-java@v4
     with:
       java-version: '17'  # Match project version
   ```

3. **Build failure**
   ```bash
   # Test build locally
   mvn clean compile
   
   # Check workflow logs
   gh run view <RUN_ID> --log
   ```

**Debug Steps:**
```bash
# 1. Run checks locally
mvn clean compile checkstyle:check pmd:check spotbugs:check

# 2. Check workflow logs
gh run list --workflow=automated-code-review.yml
gh run view <RUN_ID> --log

# 3. View PR comments
gh pr view <PR_NUMBER> --comments
```

### Issue: Review checklist not posted

**Symptoms:**
- Code checks run but no checklist comment

**Solutions:**

1. **Check workflow permissions**
   ```yaml
   permissions:
     pull-requests: write
   ```

2. **Comment already exists**
   - Workflow checks for existing checklist
   - Updates existing instead of creating new
   - Check PR comments

3. **Workflow failed**
   ```bash
   # Check for errors
   gh run view <RUN_ID> --log
   ```

---

## Dashboard Issues

### Issue: Dashboard not generating

**Symptoms:**
- Scheduled workflow doesn't run
- No dashboard issue created

**Solutions:**

1. **Cron schedule issue**
   ```yaml
   # Check schedule in pr-management-dashboard.yml
   schedule:
     - cron: '0 9 * * 1'  # Every Monday 9 AM UTC
   
   # Note: Scheduled workflows may have delays
   # Can take up to 15-30 minutes after scheduled time
   ```

2. **Manual trigger**
   ```bash
   # Trigger manually
   gh workflow run pr-management-dashboard.yml
   
   # Check status
   gh run list --workflow=pr-management-dashboard.yml
   ```

3. **Insufficient permissions**
   ```yaml
   permissions:
     issues: write
     pull-requests: read
   ```

4. **Rate limiting**
   - Too many API calls
   - Wait and retry
   - Consider reducing PR scan frequency

**Debug Steps:**
```bash
# 1. Check workflow runs
gh run list --workflow=pr-management-dashboard.yml

# 2. View logs
gh run view <RUN_ID> --log

# 3. Check for dashboard issue
gh issue list --label dashboard

# 4. Manual trigger
gh workflow run pr-management-dashboard.yml
```

### Issue: Dashboard not updating

**Symptoms:**
- Dashboard issue exists but isn't updated
- Old data showing

**Solutions:**

1. **Issue not found**
   - Check issue has `dashboard` label
   - Check issue is open
   - Check issue title matches exactly

2. **Permissions issue**
   - Workflow needs `issues: write`
   - Check workflow logs for 403 errors

3. **Force recreation**
   ```bash
   # Close existing dashboard issue
   gh issue close <ISSUE_NUMBER>
   
   # Trigger workflow to create new one
   gh workflow run pr-management-dashboard.yml
   ```

---

## Workflow Permission Issues

### Issue: Workflows failing with permission errors

**Symptoms:**
- Workflow fails with 403 errors
- "Resource not accessible by integration" errors
- Cannot create comments/labels

**Solutions:**

1. **Enable workflow permissions**
   - Go to Settings > Actions > General
   - Under "Workflow permissions"
   - Select "Read and write permissions"
   - Check "Allow GitHub Actions to create and approve pull requests"

2. **Check individual workflow permissions**
   ```yaml
   # Each workflow should have appropriate permissions
   permissions:
     contents: write       # For pushing commits
     pull-requests: write  # For PR comments/labels
     issues: write         # For creating/updating issues
     checks: read          # For reading check status
   ```

3. **Organization restrictions**
   - Check if organization has restrictions
   - Contact org admin to adjust policies

**Debug Steps:**
```bash
# Check repository action permissions
gh api repos/:owner/:repo/actions/permissions

# View workflow run with errors
gh run view <RUN_ID> --log | grep -i "permission\|403\|forbidden"
```

---

## Performance Issues

### Issue: Workflows taking too long

**Symptoms:**
- Workflows timeout
- CI/CD runs take > 10 minutes
- PRs delayed in merging

**Solutions:**

1. **Maven build optimization**
   ```bash
   # Use cached dependencies
   # Check .github/workflows have:
   - uses: actions/cache@v4
     with:
       path: ~/.m2
       key: ${{ runner.os }}-m2-${{ hashFiles('**/pom.xml') }}
   ```

2. **Parallel job execution**
   ```yaml
   # Run independent jobs in parallel
   jobs:
     test:
       # ...
     security:
       # No "needs: test" dependency
   ```

3. **Skip unnecessary checks**
   ```yaml
   # Skip checks for docs-only changes
   if: |
     !contains(github.event.pull_request.title, 'docs:') &&
     !contains(github.event.head_commit.message, '[skip ci]')
   ```

4. **Optimize check tools**
   ```bash
   # Run only changed files
   mvn checkstyle:check -Dcheckstyle.includes=**/*.java
   ```

### Issue: Rate limiting

**Symptoms:**
- API calls failing with 429 errors
- "API rate limit exceeded" messages

**Solutions:**

1. **Reduce API calls in dashboard**
   ```javascript
   // In pr-management-dashboard.yml
   // Reduce per_page or implement caching
   ```

2. **Use GitHub token properly**
   ```yaml
   env:
     GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
   ```

3. **Implement delays**
   ```javascript
   // Add delays between API calls
   await new Promise(resolve => setTimeout(resolve, 1000));
   ```

---

## General Debugging

### Viewing Workflow Logs

```bash
# List all runs
gh run list

# View specific workflow
gh run list --workflow=auto-merge-dependabot.yml

# View run details
gh run view <RUN_ID>

# Download logs
gh run view <RUN_ID> --log

# Watch running workflow
gh run watch <RUN_ID>
```

### Testing Workflows Locally

```bash
# Install act (local GitHub Actions runner)
# https://github.com/nektos/act

# List workflows
act -l

# Run workflow locally
act pull_request -e test-event.json

# Debug workflow
act pull_request --verbose
```

### Workflow Syntax Validation

```bash
# Validate YAML syntax
yamllint .github/workflows/*.yml

# Or use Python
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/auto-merge-dependabot.yml'))"
```

### Manual Workflow Triggers

```bash
# Trigger via CLI
gh workflow run <WORKFLOW_NAME>

# Trigger with inputs
gh workflow run <WORKFLOW_NAME> -f input_name=value

# View triggered run
gh run list --workflow=<WORKFLOW_NAME> --limit 1
```

### Checking PR Status Programmatically

```bash
# Get PR details
gh pr view <PR_NUMBER> --json number,title,state,mergeable,reviewDecision

# Get PR checks
gh pr checks <PR_NUMBER>

# Get PR reviews
gh pr view <PR_NUMBER> --json reviews

# Get PR labels
gh pr view <PR_NUMBER> --json labels
```

### Common GitHub CLI Commands

```bash
# Repository info
gh repo view

# Enable auto-merge
gh repo edit --enable-auto-merge

# List all PRs
gh pr list

# View PR details
gh pr view <PR_NUMBER>

# Check workflow status
gh run list

# View workflow logs
gh run view <RUN_ID> --log

# List labels
gh label list

# Create label
gh label create <NAME> --color <COLOR>

# List issues
gh issue list
```

---

## Emergency Procedures

### Disable All Automation

If automation is causing issues:

1. **Disable specific workflow**
   ```bash
   # Rename workflow file
   mv .github/workflows/auto-merge-dependabot.yml \
      .github/workflows/auto-merge-dependabot.yml.disabled
   ```

2. **Disable all workflows**
   - Go to Settings > Actions > General
   - Select "Disable actions"

3. **Remove auto-merge**
   - Go to Settings > General > Pull Requests
   - Uncheck "Allow auto-merge"

### Rollback Changes

```bash
# Revert to previous commit
git revert <COMMIT_HASH>
git push

# Or reset workflow files
git checkout HEAD^ -- .github/workflows/
git commit -m "Rollback workflow changes"
git push
```

### Emergency Fixes

```bash
# Quick fix workflow
git checkout -b hotfix/workflow-fix
# Edit workflow file
git add .github/workflows/*.yml
git commit -m "fix: Emergency workflow fix"
git push origin hotfix/workflow-fix
# Create PR and merge immediately
```

---

## Getting Help

### Resources

1. **Documentation**
   - [Setup Guide](pr-automation-setup.md)
   - [Full Guide](pr-automation-guide.md)
   - [Quick Reference](pr-automation-quick-reference.md)

2. **GitHub Docs**
   - [Actions](https://docs.github.com/en/actions)
   - [API](https://docs.github.com/en/rest)
   - [CLI](https://cli.github.com/manual/)

3. **Community**
   - GitHub Community Forum
   - Stack Overflow (tag: github-actions)

### Creating Support Issue

When creating an issue:

1. **Gather information**
   ```bash
   # Workflow run ID
   gh run list --workflow=<WORKFLOW> --limit 5
   
   # Workflow logs
   gh run view <RUN_ID> --log > workflow-logs.txt
   
   # PR details
   gh pr view <PR_NUMBER> --json number,title,state,checks > pr-details.json
   ```

2. **Include in issue**
   - What you expected to happen
   - What actually happened
   - Workflow run ID and logs
   - PR number (if applicable)
   - Steps to reproduce
   - Repository settings (if relevant)

3. **Label appropriately**
   - Add `automation` label
   - Add priority label if urgent
   - Add component label (e.g., `ci-cd`)

### Contact

- **Repository Issues**: Open issue with `automation` label
- **Direct Contact**: @cbwinslow
- **Documentation**: Check `docs/` folder

---

## Preventive Measures

### Regular Maintenance

1. **Weekly**
   - Monitor workflow success rates
   - Check for pattern of failures
   - Review workflow logs

2. **Monthly**
   - Update workflow dependencies
   - Review and optimize performance
   - Check GitHub Actions billing

3. **Quarterly**
   - Review entire automation system
   - Update documentation
   - Train team on changes

### Monitoring

Set up monitoring for:
- Workflow failure rate
- Average time to merge
- Auto-merge success rate
- Label application accuracy
- Dashboard generation success

### Testing

Before deploying workflow changes:
1. Test on a fork or branch
2. Use `workflow_dispatch` for manual testing
3. Review logs thoroughly
4. Test with sample PRs
5. Monitor first few runs closely

---

**Last Updated**: 2025-11-04
**Version**: 1.0
**Maintainer**: @cbwinslow
