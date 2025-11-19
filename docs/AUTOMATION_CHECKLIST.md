# Automation Implementation Checklist

Use this checklist to implement and verify all automation features in the OpenLegislation repository.

## ✅ Phase 1: Basic Setup

- [ ] Run master setup script: `./tools/setup_automation.sh`
- [ ] Install Python dependencies
- [ ] Install pre-commit hooks
- [ ] Verify Git and Python are installed
- [ ] Install GitHub CLI (optional but recommended)

## ✅ Phase 2: GitHub Configuration

- [ ] Generate GitHub personal access token
  - Go to: https://github.com/settings/tokens
  - Scopes: `repo`, `workflow`, `admin:org`, `project`
- [ ] Set environment variable: `export GITHUB_TOKEN=your_token`
- [ ] Configure GitHub Secrets:
  - [ ] `DOCKERHUB_USERNAME` (if using Docker)
  - [ ] `DOCKERHUB_TOKEN` (if using Docker)
  - [ ] `SONAR_TOKEN` (if using SonarCloud)
  - [ ] `FOSSA_API_KEY` (if using FOSSA)
  - [ ] `OPENAI_API_KEY` (if using AI features)

## ✅ Phase 3: Labels and Structure

- [ ] Run GitHub automation script: `python3 tools/github_automation.py`
- [ ] Verify labels created:
  - [ ] Type labels (bug, feature, enhancement, documentation, refactor)
  - [ ] Priority labels (critical, high, medium, low)
  - [ ] Status labels (in-progress, needs-review, blocked, ready)
  - [ ] Domain labels (federal-data, database, api, frontend, ci-cd)
  - [ ] Size labels (xs, s, m, l, xl)
- [ ] Verify milestones created:
  - [ ] Q1 2025 - Federal Data Integration
  - [ ] Q2 2025 - API Enhancements
  - [ ] Q3 2025 - Performance Optimization
  - [ ] Q4 2025 - Documentation & Testing
- [ ] Verify project boards created (if permissions allow)

## ✅ Phase 4: Workflow Configuration

### Core Workflows
- [ ] `ci-cd.yml` - Verify triggers and jobs
- [ ] `security-scan.yml` - Verify security tools configured
- [ ] `code-formatting.yml` - Verify formatters installed

### Automation Workflows
- [ ] `issue-automation.yml` - Test with sample issue
- [ ] `project-automation.yml` - Verify project integration
- [ ] `ai-code-analysis.yml` - Verify AI analysis patterns

### Test Workflows
- [ ] Create a test PR
- [ ] Verify workflows trigger automatically
- [ ] Check workflow logs for errors
- [ ] Verify status checks appear on PR

## ✅ Phase 5: Repository Rulesets

See `docs/github-rulesets-guide.md` for detailed steps.

- [ ] Navigate to Settings → Rules → Rulesets
- [ ] Create "Main Branch Protection" ruleset:
  - [ ] Target: `main` branch
  - [ ] Require PR before merging
  - [ ] Require 1 approval
  - [ ] Require status checks: test, security-scan, code-quality
  - [ ] Block force pushes
  - [ ] Require linear history
- [ ] Create "Develop Branch Protection" ruleset:
  - [ ] Target: `develop` branch
  - [ ] Require PR before merging
  - [ ] Require 1 approval
  - [ ] Require status checks: test, code-quality
- [ ] Create "Release Branch Protection" ruleset:
  - [ ] Target: `release/*` branches
  - [ ] Require 2 approvals
  - [ ] All status checks required
  - [ ] Require signed commits
- [ ] Create "Tag Protection" ruleset:
  - [ ] Target: `v*` tags
  - [ ] Restrict creation and deletion
  - [ ] Require signed tags

## ✅ Phase 6: Pre-commit Hooks

- [ ] Verify `.pre-commit-config.yaml` exists
- [ ] Run `pre-commit install`
- [ ] Test hooks: `pre-commit run --all-files`
- [ ] Fix any issues found
- [ ] Commit a test file to verify hooks run

## ✅ Phase 7: CrewAI Setup (Optional)

- [ ] Install CrewAI: `pip install crewai`
- [ ] Install LangChain: `pip install langchain`
- [ ] Set OpenAI API key (if using OpenAI): `export OPENAI_API_KEY=your_key`
- [ ] Test crews: `python3 tools/crewai_automation.py`
- [ ] Verify all four crews initialize:
  - [ ] Software Development Crew
  - [ ] Legislative Policy Crew
  - [ ] Database Crew
  - [ ] Documentation Crew

## ✅ Phase 8: Wiki Setup (Optional)

- [ ] Clone wiki: `git clone https://github.com/cbwinslow/OpenLegislation-local-dev.wiki.git`
- [ ] Run wiki manager: `python3 tools/wiki_manager.py`
- [ ] Verify pages created:
  - [ ] Home.md
  - [ ] Getting-Started.md
  - [ ] API-Documentation.md
  - [ ] Database-Schema.md
  - [ ] Federal-Data-Integration.md
- [ ] Push changes to wiki
- [ ] Verify pages appear on GitHub

## ✅ Phase 9: Testing and Verification

### Test Issue Automation
- [ ] Create test issue: "Test: Federal data bug"
- [ ] Verify auto-labeling works
- [ ] Verify auto-assignment works (if configured)
- [ ] Verify issue added to project board
- [ ] Close issue and verify status updates

### Test PR Automation
- [ ] Create test PR
- [ ] Verify auto-labeling
- [ ] Verify code review bot comments
- [ ] Verify formatting bot runs
- [ ] Verify security analysis runs
- [ ] Verify status checks complete

### Test Security Scans
- [ ] View Security → Code scanning alerts
- [ ] View Security → Dependabot alerts
- [ ] Verify weekly scans scheduled
- [ ] Check secret scanning is enabled

### Test Code Formatting
- [ ] Create PR with unformatted code
- [ ] Verify formatter runs
- [ ] Verify auto-commit of formatted code
- [ ] Merge and verify changes

## ✅ Phase 10: Documentation Review

- [ ] Read `docs/AUTOMATION_GUIDE.md`
- [ ] Read `docs/github-rulesets-guide.md`
- [ ] Read `docs/wiki-automation-guide.md`
- [ ] Read `.github/copilot-instructions-detailed.md`
- [ ] Read `AUTOMATION_README.md`
- [ ] Review workflow files in `.github/workflows/`

## ✅ Phase 11: Team Onboarding

- [ ] Share documentation with team
- [ ] Explain label system
- [ ] Demonstrate PR workflow
- [ ] Show how to trigger workflows manually
- [ ] Explain bypass procedures for emergencies
- [ ] Set up team notifications

## ✅ Phase 12: Monitoring Setup

### GitHub Actions Monitoring
- [ ] Install GitHub CLI: `gh`
- [ ] Set up workflow notifications
- [ ] Create monitoring dashboard (optional)
- [ ] Configure failure notifications

### Issue Tracking
- [ ] Set up project board views
- [ ] Configure milestone tracking
- [ ] Set up stale issue notifications

### Security Monitoring
- [ ] Enable Dependabot alerts
- [ ] Enable security advisories
- [ ] Configure code scanning alerts
- [ ] Set up security notification channels

## ✅ Phase 13: Optimization

- [ ] Review workflow execution times
- [ ] Optimize slow workflows
- [ ] Enable workflow caching where appropriate
- [ ] Review and adjust label categories
- [ ] Fine-tune auto-assignment rules
- [ ] Adjust stale issue timeframes

## ✅ Phase 14: Advanced Features (Optional)

- [ ] Set up self-hosted runners (if needed)
- [ ] Configure matrix builds for multiple Java versions
- [ ] Set up deployment pipelines to staging/production
- [ ] Configure automated release notes
- [ ] Set up performance testing workflows
- [ ] Configure automated backups
- [ ] Set up custom GitHub Actions

## ✅ Phase 15: Maintenance Schedule

### Weekly Tasks
- [ ] Review failed workflows
- [ ] Check security scan results
- [ ] Review stale issues
- [ ] Monitor project board status

### Monthly Tasks
- [ ] Update dependencies
- [ ] Review label usage and effectiveness
- [ ] Audit workflow performance
- [ ] Review team assignments
- [ ] Update documentation

### Quarterly Tasks
- [ ] Review and update rulesets
- [ ] Update milestones
- [ ] Review team structure
- [ ] Audit security practices
- [ ] Update automation scripts

## 🎯 Success Criteria

Your automation is successfully implemented when:

- ✅ All workflows run without errors
- ✅ Issues are automatically labeled and assigned
- ✅ PRs go through automated review and checks
- ✅ Code is automatically formatted
- ✅ Security scans run regularly
- ✅ Project boards update automatically
- ✅ Team understands and uses the system
- ✅ Documentation is complete and accessible

## 📊 Metrics to Track

- **Workflow Success Rate**: >95% of workflows should succeed
- **PR Turnaround Time**: Track from creation to merge
- **Issue Resolution Time**: Track from creation to close
- **Security Findings**: Track vulnerabilities found and fixed
- **Code Coverage**: Track test coverage trends
- **Automation Usage**: Track how often automation is used

## 🚨 Emergency Procedures

If automation causes issues:

1. **Disable workflows**: Rename `.github/workflows/` temporarily
2. **Bypass rulesets**: Use bypass token (if configured)
3. **Disable pre-commit**: `pre-commit uninstall`
4. **Manual process**: Fall back to manual reviews and merges
5. **Fix and restore**: Fix the issue, then re-enable automation

## 📞 Support Resources

- **GitHub Actions**: https://docs.github.com/actions
- **GitHub API**: https://docs.github.com/rest
- **CrewAI**: https://docs.crewai.com/
- **Pre-commit**: https://pre-commit.com/
- **Project Issues**: Create issue with `automation` label

## 🎓 Learning Resources

- [GitHub Actions Certification](https://docs.github.com/en/actions/learn-github-actions)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [CI/CD Best Practices](https://docs.github.com/en/actions/guides)
- [CrewAI Examples](https://github.com/joaomdmoura/crewAI-examples)

---

**Note**: This checklist should be completed in order. Each phase builds on the previous one.

**Estimated Time**: 
- Basic Setup (Phases 1-6): 2-3 hours
- Advanced Setup (Phases 7-14): 4-6 hours
- Total: 6-9 hours for complete implementation

**Next Steps After Completion**:
1. Monitor for 1 week
2. Gather team feedback
3. Adjust and optimize
4. Document lessons learned
5. Plan next improvements

Good luck! 🚀
