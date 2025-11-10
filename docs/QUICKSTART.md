# ⚡ Quick Start: Automation Setup

Get up and running with OpenLegislation automation in 15 minutes!

## Prerequisites Checklist

- [ ] Git installed
- [ ] Python 3.10+ installed
- [ ] GitHub account with repository access
- [ ] GitHub personal access token (PAT)

## 🚀 5-Minute Setup

### Step 1: Run Setup Script (2 minutes)

```bash
# From repository root
./tools/setup_automation.sh
```

This installs dependencies and configures pre-commit hooks.

### Step 2: Configure GitHub Token (1 minute)

```bash
# Generate token at: https://github.com/settings/tokens
# Required scopes: repo, workflow

export GITHUB_TOKEN="your_token_here"
```

### Step 3: Create Labels and Milestones (2 minutes)

```bash
python3 tools/github_automation.py
```

This creates:
- 25 standard labels
- 4 quarterly milestones
- 4 project boards

### Step 4: Test Automation (1 minute)

```bash
# Create a test issue
gh issue create --title "Test: Automation check" --body "Testing automation"

# Check if it was auto-labeled
gh issue list
```

### Step 5: Enable Pre-commit Hooks (30 seconds)

```bash
pre-commit install
pre-commit run --all-files  # Optional: test on all files
```

## ✅ Verification

Your automation is working if:

1. **Test issue was auto-labeled** with appropriate labels
2. **Pre-commit hooks are installed** (check `.git/hooks/pre-commit`)
3. **Workflows are present** in `.github/workflows/` (should be 15 files)
4. **Setup script completed** without errors

## 📖 Next Steps

### Immediate (Next Hour)

1. **Configure Repository Secrets** (Settings → Secrets):
   - Add `DOCKERHUB_USERNAME` (if using Docker)
   - Add `DOCKERHUB_TOKEN` (if using Docker)
   - Add other optional secrets

2. **Create a Test PR**:
   ```bash
   git checkout -b test-automation
   echo "# Test" > TEST.md
   git add TEST.md
   git commit -m "test: automation check"
   git push origin test-automation
   gh pr create --title "Test: Automation" --body "Testing workflows"
   ```

3. **Watch Workflows Run**:
   - Go to Actions tab in GitHub
   - Watch workflows execute
   - Check for any failures

### This Week

4. **Set Up Repository Rulesets** (30 minutes)
   - See: `docs/github-rulesets-guide.md`
   - Protect main branch
   - Configure required reviews

5. **Team Onboarding** (1 hour)
   - Share `AUTOMATION_README.md` with team
   - Explain label system
   - Demonstrate PR workflow

6. **Review Documentation** (1 hour)
   - Read `docs/AUTOMATION_GUIDE.md`
   - Review `.github/copilot-instructions-detailed.md`
   - Bookmark important docs

### This Month

7. **Optional: Set Up CrewAI** (if using AI features)
   ```bash
   pip install crewai langchain
   export OPENAI_API_KEY="your_key"
   python3 tools/crewai_automation.py  # Test
   ```

8. **Optional: Set Up Wiki**
   ```bash
   git clone https://github.com/cbwinslow/OpenLegislation-local-dev.wiki.git
   python3 tools/wiki_manager.py
   ```

9. **Monitor and Optimize**
   - Review workflow performance
   - Adjust automation rules
   - Gather team feedback

## 🎯 Success Criteria

After 15 minutes, you should have:

- ✅ All dependencies installed
- ✅ Pre-commit hooks enabled
- ✅ Labels created
- ✅ Milestones created
- ✅ Test issue auto-labeled
- ✅ Workflows ready to run

## 🆘 Troubleshooting

### Issue: Setup script fails

**Solution**:
```bash
# Install missing dependencies manually
pip install --user pre-commit pyyaml requests

# Try again
./tools/setup_automation.sh
```

### Issue: GitHub automation fails

**Solution**:
```bash
# Check token is set
echo $GITHUB_TOKEN

# Check token permissions at:
# https://github.com/settings/tokens

# Verify repository access
gh repo view cbwinslow/OpenLegislation-local-dev
```

### Issue: Pre-commit hooks not working

**Solution**:
```bash
# Reinstall
pre-commit uninstall
pip install --user pre-commit
pre-commit install

# Test
pre-commit run --all-files
```

### Issue: Workflows not running

**Solution**:
1. Check Actions are enabled (Settings → Actions)
2. Verify workflow files exist: `ls .github/workflows/`
3. Check workflow syntax: `gh workflow list`
4. Review workflow logs: `gh run list`

## 📚 Documentation Quick Links

- **Complete Guide**: `docs/AUTOMATION_GUIDE.md`
- **Quick Reference**: `AUTOMATION_README.md`
- **Checklist**: `AUTOMATION_CHECKLIST.md`
- **Summary**: `AUTOMATION_SUMMARY.md`
- **Rulesets**: `docs/github-rulesets-guide.md`
- **Wiki**: `docs/wiki-automation-guide.md`
- **Copilot**: `.github/copilot-instructions-detailed.md`

## 💡 Pro Tips

1. **Use GitHub CLI**: Install `gh` for easier workflow management
   ```bash
   # Install from: https://cli.github.com/
   gh workflow list
   gh run list
   gh issue list
   ```

2. **Test Locally First**: Test pre-commit hooks before pushing
   ```bash
   pre-commit run --all-files
   ```

3. **Monitor Workflows**: Watch first few workflows closely
   ```bash
   gh run watch
   ```

4. **Use Labels**: Apply labels to issues for auto-assignment
   ```bash
   gh issue create --label "bug,priority: high,domain: federal-data"
   ```

5. **Check Documentation**: When in doubt, check the guides
   ```bash
   cat docs/AUTOMATION_GUIDE.md | less
   ```

## 🎓 Learning Path

1. **Day 1**: Basic setup (this guide)
2. **Week 1**: Workflow understanding
3. **Week 2**: Advanced features (CrewAI, rulesets)
4. **Month 1**: Optimization and team adoption

## 📊 What You Get

After completing this quick start:

### Automated Workflows (15 total)
- ✅ CI/CD pipeline
- ✅ Security scanning
- ✅ Code formatting
- ✅ Issue automation
- ✅ Project management
- ✅ AI code analysis

### Issue Management
- ✅ Auto-labeling
- ✅ Auto-assignment
- ✅ Project boards
- ✅ Stale tracking
- ✅ Related issue linking

### Code Quality
- ✅ Pre-commit hooks
- ✅ Auto-formatting
- ✅ Linting
- ✅ Security checks
- ✅ Test coverage

### AI Features (Optional)
- ✅ 4 specialized agent crews
- ✅ 15 AI agents
- ✅ Code review
- ✅ Documentation generation

## 🎉 You're Done!

Congratulations! You've set up comprehensive automation in 15 minutes.

**Next**: Create your first automated PR and watch the magic happen! 🚀

---

**Questions?** 
- Create an issue with label `automation`
- Review `docs/AUTOMATION_GUIDE.md`
- Check `AUTOMATION_README.md`

**Need Help?**
- Check troubleshooting section above
- Review GitHub Actions docs
- Ask in repository discussions

**Want More?**
- Read full guides in `docs/`
- Explore CrewAI features
- Set up advanced rulesets

Happy automating! 🎊
