# PR Automation System - Visual Overview

This document provides visual representations of how the PR automation system works.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Repository                             │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Pull Request │  │    Issues    │  │   Actions    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
└─────────┼──────────────────┼──────────────────┼───────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Actions Workflows                       │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Auto-Merge Dependabot                                      │ │
│  │  • Detects Dependabot PRs                                   │ │
│  │  • Approves minor/patch updates                             │ │
│  │  • Enables auto-merge                                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Automated Code Review                                       │ │
│  │  • Runs Checkstyle, PMD, SpotBugs                           │ │
│  │  • Adds size labels                                          │ │
│  │  • Posts review checklist                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  PR Auto-Labeler                                             │ │
│  │  • Analyzes changed files                                    │ │
│  │  • Detects PR type from title                                │ │
│  │  • Applies component labels                                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  PR Management Dashboard                                     │ │
│  │  • Scans all open PRs                                        │ │
│  │  • Generates weekly report                                   │ │
│  │  • Manages stale PRs                                         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## Workflow 1: Auto-Merge Dependabot

```
┌──────────────────────────────────────────────────────────────────┐
│                  Dependabot Opens PR                              │
│                 (Dependency Update)                               │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│         Fetch Dependabot Metadata                                 │
│         • Get update type (major/minor/patch)                     │
│         • Get dependency name                                     │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
         ┌─────────┴──────────┐
         │  Update Type?       │
         └─────────┬───────────┘
                   │
         ┌─────────┼─────────┐
         │                   │
         ▼                   ▼
    Major Update      Minor/Patch Update
         │                   │
         ▼                   ▼
┌────────────────┐  ┌──────────────────┐
│ Add Warning    │  │ Auto-Approve PR  │
│ Comment        │  │                  │
│                │  │ Add Label:       │
│ Add Label:     │  │ • auto-merge     │
│ • needs-review │  │ • minor/patch    │
│ • major-update │  │                  │
└────────────────┘  └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Enable Auto-Merge│
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Wait for Checks  │
                    │ • test           │
                    │ • security-scan  │
                    │ • code-quality   │
                    └────────┬─────────┘
                             │
                    ┌────────┴────────┐
                    │ All Checks Pass?│
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │       Yes       │
                    └────────┬────────┘
                             ▼
                    ┌──────────────────┐
                    │   Auto-Merge! ✅ │
                    └──────────────────┘
```

## Workflow 2: Automated Code Review

```
┌──────────────────────────────────────────────────────────────────┐
│              PR Opened/Updated (Not Draft)                        │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  Get Changed Files    │
        └──────────┬────────────┘
                   │
        ┌──────────┴─────────────────────┐
        │                                 │
        ▼                                 ▼
┌──────────────────┐           ┌──────────────────┐
│ Run Code Quality │           │  Calculate Size  │
│ Checks (Parallel)│           │  • Count lines   │
│                  │           │  • Add label     │
│ • Checkstyle     │           │    (XS/S/M/L/XL) │
│ • PMD            │           │                  │
│ • SpotBugs       │           │  Warn if XL      │
└────────┬─────────┘           └────────┬─────────┘
         │                              │
         └──────────┬───────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Aggregate Results    │
         │  • Collect errors     │
         │  • Format output      │
         └──────────┬────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Post Review Comment  │
         │ • Checkstyle results │
         │ • PMD results        │
         │ • SpotBugs results   │
         │ • Complexity report  │
         └──────────┬────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Post Review Checklist│
         │ • Code quality       │
         │ • Functionality      │
         │ • Security           │
         │ • Testing            │
         │ • Documentation      │
         └──────────────────────┘
```

## Workflow 3: PR Auto-Labeler

```
┌──────────────────────────────────────────────────────────────────┐
│                      PR Opened/Updated                            │
└──────────────────┬───────────────────────────────────────────────┘
                   │
        ┌──────────┴───────────┐
        │                      │
        ▼                      ▼
┌──────────────────┐   ┌──────────────────┐
│ Analyze Files    │   │ Analyze Content  │
│ Changed          │   │ (Title/Desc)     │
└────────┬─────────┘   └────────┬─────────┘
         │                      │
         ▼                      ▼
┌──────────────────┐   ┌──────────────────┐
│ Detect Component │   │ Detect Type      │
│                  │   │                  │
│ • backend        │   │ • bug-fix        │
│ • frontend       │   │ • enhancement    │
│ • database       │   │ • security       │
│ • api            │   │ • performance    │
│ • tests          │   │ • breaking       │
│ • docs           │   │                  │
│ • ci-cd          │   │ Detect Priority  │
│ • infra          │   │ • high-priority  │
│                  │   │ • needs-review   │
└────────┬─────────┘   └────────┬─────────┘
         │                      │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Apply All Labels    │
         │  (Multiple OK)       │
         └──────────┬────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Assign Reviewers     │
         │ (Based on CODEOWNERS)│
         └──────────────────────┘
```

## Workflow 4: PR Management Dashboard

```
┌──────────────────────────────────────────────────────────────────┐
│        Every Monday 9 AM UTC (or Manual Trigger)                  │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
         ┌──────────────────────┐
         │ Fetch All Open PRs   │
         │ (Up to 100)          │
         └──────────┬────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  For Each PR:        │
         │  • Get labels        │
         │  • Get reviews       │
         │  • Get checks        │
         │  • Get age           │
         └──────────┬────────────┘
                    │
                    ▼
         ┌──────────────────────────────────────┐
         │        Categorize PRs                 │
         │                                       │
         │  • High Priority                      │
         │  • Approved (Ready to Merge)          │
         │  • Needs Review                       │
         │  • Dependabot                         │
         │  • Stale (7+ days no activity)        │
         │  • Draft                              │
         └──────────┬────────────────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Generate Report      │
         │ • Formatted markdown │
         │ • Statistics         │
         │ • Links to PRs       │
         └──────────┬────────────┘
                    │
         ┌──────────┴───────────┐
         │                      │
         ▼                      ▼
┌──────────────────┐   ┌──────────────────┐
│ Create/Update    │   │ Mark Stale PRs   │
│ Dashboard Issue  │   │ (30+ days)       │
│                  │   │                  │
│ Add label:       │   │ Close Stale PRs  │
│ • dashboard      │   │ (37+ days)       │
└──────────────────┘   └──────────────────┘
```

## Label Taxonomy

```
┌─────────────────────────────────────────────────────────────────┐
│                         PR Labels                                │
└─────────────────────────────────────────────────────────────────┘

SIZE (Auto)                 TYPE (Auto)              COMPONENT (Auto)
├─ size/XS (< 10)          ├─ bug-fix               ├─ backend
├─ size/S (10-50)          ├─ enhancement           ├─ frontend
├─ size/M (50-200)         ├─ refactoring           ├─ database
├─ size/L (200-500)        ├─ security              ├─ api
└─ size/XL (> 500)         ├─ performance           ├─ tests
                           └─ breaking-change       ├─ documentation
                                                    ├─ ci-cd
STATUS (Auto/Manual)        PRIORITY (Auto/Manual)   ├─ infrastructure
├─ needs-review            ├─ high-priority         ├─ federal-integration
├─ auto-merge              └─ urgent                └─ data-processing
├─ stale
├─ keep-open               SOURCE (Auto)
├─ in-progress             ├─ dependencies
└─ blocked                 ├─ java
                           ├─ python
                           └─ javascript
```

## Data Flow Diagram

```
┌─────────────┐
│ Contributor │
└──────┬──────┘
       │ Creates PR
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│                        Pull Request                           │
│                                                               │
│  Triggers:                                                    │
│  1. Auto-Merge Workflow (if Dependabot)                      │
│  2. Code Review Workflow                                      │
│  3. Auto-Labeler Workflow                                     │
└──────┬───────────────────────────────────────────────────────┘
       │
       │ Workflows run in parallel
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│                     GitHub Actions                            │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Auto-Merge  │  │ Code Review │  │ Auto-Label  │         │
│  │   (3 min)   │  │  (5 min)    │  │  (1 min)    │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                 │                 │
└─────────┼────────────────┼─────────────────┼─────────────────┘
          │                │                 │
          ▼                ▼                 ▼
┌──────────────────────────────────────────────────────────────┐
│                    Pull Request Updated                       │
│                                                               │
│  • Auto-approval (if Dependabot minor/patch)                 │
│  • Code quality feedback comment                             │
│  • Review checklist                                           │
│  • Labels applied                                             │
│  • Size label                                                 │
│  • Reviewers assigned (CODEOWNERS)                           │
└──────┬───────────────────────────────────────────────────────┘
       │
       │ Human review
       │
       ▼
┌──────────────┐
│   Reviewer   │────► Approves PR
└──────┬───────┘
       │
       │ If Dependabot & auto-merge enabled
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│              All Checks Pass & Approved                       │
└──────┬───────────────────────────────────────────────────────┘
       │
       │ Auto-merge triggers
       │
       ▼
┌──────────────┐
│   Merged! ✅  │
└──────────────┘
```

## Weekly Dashboard Flow

```
Monday 9 AM UTC
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│         PR Management Dashboard Workflow Runs                │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │   Scan Repository   │
         │   • All open PRs    │
         │   • PR metadata     │
         │   • Review status   │
         │   • Check status    │
         │   • Age             │
         └─────────┬───────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │   Categorize PRs    │
         │                     │
         │   High Priority: 3  │
         │   Approved: 5       │
         │   Needs Review: 12  │
         │   Dependabot: 8     │
         │   Stale: 2          │
         │   Draft: 4          │
         └─────────┬───────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │  Generate Report    │
         │  • Markdown format  │
         │  • Tables & lists   │
         │  • Statistics       │
         │  • Links            │
         └─────────┬───────────┘
                   │
         ┌─────────┴──────────┐
         │                    │
         ▼                    ▼
┌─────────────────┐   ┌─────────────────┐
│ Create/Update   │   │  Stale PR       │
│ Dashboard Issue │   │  Management     │
│                 │   │                 │
│ Title:          │   │  Mark stale:    │
│ "PR Management  │   │  • 30+ days     │
│  Dashboard"     │   │                 │
│                 │   │  Close stale:   │
│ Label:          │   │  • 37+ days     │
│ • dashboard     │   │                 │
└─────────────────┘   └─────────────────┘
         │                    │
         │                    │
         ▼                    ▼
┌─────────────────────────────────────┐
│    Team Reviews Dashboard           │
│    • Prioritize PRs for week        │
│    • Address stale PRs               │
│    • Track progress                  │
└─────────────────────────────────────┘
```

## Integration with Existing CI/CD

```
┌──────────────────────────────────────────────────────────────┐
│                   Existing CI/CD Workflows                    │
│                                                               │
│  • ci-cd.yml           (tests, security, build)              │
│  • maven-ci-cd.yml     (Maven build, deploy)                 │
│  • security-scan.yml   (CodeQL, OWASP, Trivy)                │
│  • pre-commit.yml      (pre-commit hooks)                    │
└──────┬───────────────────────────────────────────────────────┘
       │
       │ Required checks
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│                Branch Protection Rules                        │
│                                                               │
│  Required status checks:                                      │
│  • test                                                       │
│  • security-scan                                              │
│  • code-quality                                               │
└──────┬───────────────────────────────────────────────────────┘
       │
       │ All must pass
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│              Auto-Merge (if enabled)                          │
│                                                               │
│  Only triggers when:                                          │
│  1. All required checks pass ✅                               │
│  2. Required approvals received ✅                            │
│  3. No merge conflicts ✅                                     │
│  4. Branch up to date ✅                                      │
└──────────────────────────────────────────────────────────────┘
```

## Success Metrics Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│                  Automation Metrics                          │
└─────────────────────────────────────────────────────────────┘

Week 1                  Week 4                  Week 12
├─────────────────────┼─────────────────────┼────────────────┐
│                     │                     │                │
│ Manual Reviews: 100%│ Manual Reviews: 40% │ Manual: 30%    │
│ Auto-Merge: 0%      │ Auto-Merge: 60%     │ Auto: 70% ✅   │
│                     │                     │                │
│ Avg Time to         │ Avg Time to         │ Avg Time to    │
│ Merge: 48 hrs       │ Merge: 32 hrs       │ Merge: 24 hrs✅│
│                     │                     │                │
│ Stale PRs: 15       │ Stale PRs: 8        │ Stale PRs: 3✅ │
│                     │                     │                │
│ Labeled PRs: 20%    │ Labeled PRs: 90%    │ Labeled: 100%✅│
└─────────────────────┴─────────────────────┴────────────────┘

Target Achievement:
├─ Auto-merge rate: ████████████████░░░░ 70% (Target: 60%)
├─ Time reduction:  ████████████████████ 100% (Target: 30%)
├─ Stale PR count:  ████████████████████ 100% (Target: <5)
└─ Label coverage:  ████████████████████ 100% (Target: 95%)
```

## Decision Tree: When Does Auto-Merge Trigger?

```
                    ┌─────────────────┐
                    │   PR Created    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ From Dependabot?│
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │      Yes        │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Update Type?   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
         ┌────────┐     ┌────────┐     ┌────────┐
         │ Major  │     │ Minor  │     │ Patch  │
         └───┬────┘     └───┬────┘     └───┬────┘
             │              │              │
             │              └──────┬───────┘
             │                     │
             │                     ▼
             │            ┌─────────────────┐
             │            │ Auto-Approve ✅ │
             │            └────────┬────────┘
             │                     │
             │                     ▼
             │            ┌─────────────────┐
             │            │ Enable Auto-    │
             │            │ Merge ✅        │
             │            └────────┬────────┘
             │                     │
             │                     ▼
             │            ┌─────────────────┐
             │            │ All CI Checks   │
             │            │ Pass?           │
             │            └────────┬────────┘
             │                     │
             │            ┌────────┴────────┐
             │            │      Yes        │
             │            └────────┬────────┘
             │                     │
             │                     ▼
             │            ┌─────────────────┐
             │            │ PR Approved?    │
             │            └────────┬────────┘
             │                     │
             │            ┌────────┴────────┐
             │            │      Yes        │
             │            └────────┬────────┘
             │                     │
             │                     ▼
             │            ┌─────────────────┐
             │            │  AUTO-MERGE! ✅ │
             │            └─────────────────┘
             │
             ▼
    ┌─────────────────┐
    │ Flag for Manual │
    │ Review ⚠️       │
    └─────────────────┘
```

## Time Savings Estimation

```
┌─────────────────────────────────────────────────────────────┐
│              Before Automation                               │
└─────────────────────────────────────────────────────────────┘

Per Week:
├─ Dependabot PRs: 20 PRs × 10 min each = 200 min (3.3 hrs)
├─ Manual labeling: 30 PRs × 2 min each = 60 min (1 hr)
├─ Code review setup: 30 PRs × 5 min each = 150 min (2.5 hrs)
├─ PR tracking: 1 hr manual dashboard creation
└─ Total: ~8 hours/week

┌─────────────────────────────────────────────────────────────┐
│              After Automation                                │
└─────────────────────────────────────────────────────────────┘

Per Week:
├─ Dependabot PRs: 6 PRs (major only) × 10 min = 60 min (1 hr)
├─ Manual labeling: 0 min (automated)
├─ Code review setup: 0 min (automated)
├─ PR tracking: 10 min (review dashboard)
└─ Total: ~1.2 hours/week

┌─────────────────────────────────────────────────────────────┐
│              Time Savings                                    │
└─────────────────────────────────────────────────────────────┘

Per Week: 6.8 hours saved (85% reduction)
Per Month: 27.2 hours saved
Per Year: 326.4 hours saved (8.2 work weeks!)
```

---

**Visual Guide Version**: 1.0  
**Last Updated**: November 4, 2025  
**Created for**: OpenLegislation PR Automation System
