# Issue Template Improvements - Visual Comparison

## Problem Addressed

The issue reported was that someone submitted a bug report using only the template placeholders without filling in any actual information. The title was just "[BUG]" and the description contained all the placeholder text from the template.

## Root Cause

The old Markdown-based templates had no validation, allowing users to submit issues with:
- Empty or placeholder content
- Incomplete required information
- Inconsistent data formats

## Solution

Converted to YAML-based GitHub Issue Forms with:
- **Required field validation** - prevents submission without critical info
- **Structured inputs** - dropdowns ensure consistent data
- **Better UX** - form interface vs. markdown editing
- **Disabled blank issues** - all issues must use a template

## Before vs. After

### Old Template (Markdown)
```markdown
---
name: Bug Report
about: Report a bug or issue with OpenLegislation
title: "[BUG] "
labels: bug
assignees: ''
---

## Bug Description
A clear and concise description of the bug.

## Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
A clear and concise description of what you expected to happen.

...
```

**Problems:**
- User could submit without changing any text
- No validation of required fields
- Placeholders like "Go to '...'" could be submitted as-is
- Inconsistent severity/priority inputs

### New Template (YAML Form)
```yaml
name: Bug Report
description: Report a bug or issue with OpenLegislation
title: "[BUG]: "
labels: ["bug"]
body:
  - type: textarea
    id: bug-description
    attributes:
      label: Bug Description
      description: A clear and concise description of the bug.
      placeholder: Describe what went wrong...
    validations:
      required: true

  - type: dropdown
    id: severity
    attributes:
      label: Severity
      description: How severe is this bug?
      options:
        - Critical
        - High
        - Medium
        - Low
    validations:
      required: true
...
```

**Benefits:**
- ✅ **Required fields** must be filled before submission
- ✅ **Dropdowns** for severity, data source, affected users, etc.
- ✅ **Structured data** ensures consistency
- ✅ **Better placeholders** guide users on what to enter
- ✅ **Form validation** prevents incomplete submissions

## Key Improvements

### 1. Required Fields
Both templates now enforce these required fields:

**Bug Report:**
- Bug Description
- Steps to Reproduce
- Expected Behavior
- Actual Behavior
- Operating System
- Java Version
- Data Source
- Severity
- Affected Users
- Data Loss indicator

**Feature Request:**
- Feature Summary
- Problem Statement
- Proposed Solution
- Affected Components
- Data Sources
- Breaking Changes indicator
- Migration Required indicator
- Performance Impact
- Security Implications
- Urgency
- Business Value

### 2. Structured Inputs

**Dropdowns** for consistent data:
- Severity: Critical/High/Medium/Low
- Data Source: State/Federal/Both/Not applicable
- Affected Users: All users/State users/Federal users/Developers/Specific users
- Data Loss: Yes/No/Unknown

**Checkboxes** for multi-select:
- Affected Components: API/Database/Frontend/Processing Pipeline/Documentation/Other

### 3. Configuration

`config.yml` ensures:
- Blank issues are disabled
- Users must choose a template
- Quick links to documentation and discussions

## Testing the Changes

To verify the improvements work on GitHub:

1. Navigate to repository → Issues → New Issue
2. Select "Bug Report" or "Feature Request"
3. Try to submit without filling required fields → Should block submission
4. Fill required fields → Should allow submission
5. Check that dropdowns provide consistent options

## Impact

This change prevents issues like the one reported:
- ❌ **Before**: User could submit "[BUG]" with all placeholder text
- ✅ **After**: User must fill in actual information before submission

The structured approach also makes it easier to:
- Parse and categorize issues automatically
- Generate reports and metrics
- Prioritize issues based on severity
- Route issues to appropriate teams
