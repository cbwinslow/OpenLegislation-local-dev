# Issue Template Migration

## Overview
This document describes the migration from Markdown-based issue templates to YAML-based GitHub Issue Forms.

## What Changed

### Before
- Used Markdown-based templates (`.md` files)
- No validation of required fields
- Users could submit incomplete issue reports
- Title format was `[BUG] ` or `[FEATURE] ` with trailing space

### After
- Uses YAML-based GitHub Issue Forms (`.yml` files)
- Required fields are enforced before submission
- Structured data with dropdowns for consistent input
- Title format is `[BUG]: ` or `[FEATURE]: ` (with colon)
- Blank issues are disabled to ensure all issues use a template
- Added contact links for documentation and discussions

## Benefits

1. **Required Field Validation**: Users must fill in critical information before submitting an issue
2. **Structured Data**: Dropdowns and checkboxes ensure consistent data format
3. **Better User Experience**: Form-based interface is easier to use than editing markdown
4. **Reduced Incomplete Issues**: Validation prevents submission of template placeholders
5. **Improved Issue Quality**: Structured fields guide users to provide all necessary information

## New Issue Templates

### Bug Report (`bug_report.yml`)
Required fields:
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

Optional fields:
- Maven Version
- Database Version
- Browser
- Logs
- Congress/Session
- Bill/Law ID
- Possible Solution
- Additional Context

### Feature Request (`feature_request.yml`)
Required fields:
- Feature Summary
- Problem Statement
- Proposed Solution
- Affected Components (checkboxes)
- Data Sources
- Breaking Changes indicator
- Migration Required indicator
- Performance Impact
- Security Implications
- Urgency
- Business Value

Optional fields:
- Alternative Solutions
- User Stories
- Acceptance Criteria
- Database Changes
- API Changes
- External Dependencies
- Effort Estimate
- Additional Context

## Configuration

The `config.yml` file:
- Disables blank issues to ensure template usage
- Provides links to documentation and discussions
- Helps users find information before creating issues

## Migration Notes

- Old `.md` templates have been removed
- New `.yml` templates provide the same structure with enhanced validation
- Existing issues are not affected
- New issues will use the form-based interface

## Testing

To test the new templates:
1. Go to the repository on GitHub
2. Click "Issues" → "New Issue"
3. You should see the template chooser with the new forms
4. Try to submit without filling required fields - it should prevent submission
5. Fill in all required fields and verify submission works

## References

- [GitHub Issue Forms Documentation](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-githubs-form-schema)
- [Issue Template Configuration](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository)
