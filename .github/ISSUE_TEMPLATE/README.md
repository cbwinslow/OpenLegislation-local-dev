# Issue Templates Guide

This directory contains GitHub Issue Forms for creating bug reports and feature requests.

## How to Create an Issue

1. Go to the [Issues page](https://github.com/cbwinslow/OpenLegislation-local-dev/issues)
2. Click **New Issue**
3. Choose either **Bug Report** or **Feature Request**
4. Fill out the form with all required information
5. Click **Submit new issue**

## Issue Templates

### Bug Report
Use this template to report bugs or issues with OpenLegislation.

**Required Information:**
- Clear description of the bug
- Steps to reproduce
- Expected vs. actual behavior
- Environment details (OS, Java version)
- Data source (State/Federal)
- Severity level
- Affected users
- Whether data loss occurred

**Optional Information:**
- Log output
- Congress/Session details
- Bill/Law IDs
- Screenshots
- Possible solutions

### Feature Request
Use this template to propose new features or enhancements.

**Required Information:**
- Feature summary
- Problem it solves
- Proposed solution
- Affected components
- Data sources
- Impact assessments (breaking changes, migration, performance, security)
- Priority (urgency, business value)

**Optional Information:**
- Alternative solutions
- User stories
- Acceptance criteria
- Technical details (database, API, dependencies)
- Effort estimate

## Tips for High-Quality Issues

### For Bug Reports:
1. **Be specific**: Provide exact steps to reproduce
2. **Include details**: Version numbers, environment info, data sources
3. **Show evidence**: Add logs, screenshots, or error messages
4. **Test first**: Verify the bug is reproducible
5. **Search first**: Check if the issue already exists

### For Feature Requests:
1. **Explain the why**: What problem does this solve?
2. **Be realistic**: Consider technical constraints
3. **Think holistically**: Consider impact on all components
4. **Provide context**: User stories help illustrate the need
5. **Estimate impact**: Help prioritize with urgency and business value

## Field Descriptions

### Data Source
- **State**: New York State legislative data
- **Federal**: Congress.gov / govinfo data
- **Both**: Affects both data sources
- **Not applicable**: Not related to data sources

### Severity Levels
- **Critical**: System is unusable, data loss, security issue
- **High**: Major functionality broken, blocking work
- **Medium**: Important functionality impaired, workaround exists
- **Low**: Minor issue, cosmetic, nice to have

### Affected Users
- **All users**: Impacts everyone using the system
- **State users**: Only affects state legislative data users
- **Federal users**: Only affects federal legislative data users
- **Developers**: Only impacts development/deployment
- **Specific users**: Affects certain user groups or scenarios

## Template Configuration

- **Blank issues disabled**: All issues must use a template
- **Required validation**: Core fields must be filled before submission
- **Structured data**: Dropdowns ensure consistent categorization
- **Contact links**: Quick access to documentation and discussions

## Template Maintenance

These templates use GitHub's Issue Forms syntax (YAML format):
- `bug_report.yml` - Bug report form
- `feature_request.yml` - Feature request form
- `config.yml` - Template chooser configuration

To modify templates:
1. Edit the YAML files in this directory
2. Test changes by creating a test issue
3. Ensure YAML syntax is valid
4. Document any significant changes

## Resources

- [GitHub Issue Forms Documentation](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-githubs-form-schema)
- [OpenLegislation Documentation](https://github.com/cbwinslow/OpenLegislation-local-dev/tree/main/docs)
- [Project Discussions](https://github.com/cbwinslow/OpenLegislation-local-dev/discussions)

## Questions?

If you have questions about:
- **Using templates**: Check this guide or create a discussion
- **Template functionality**: Open an issue with the "documentation" label
- **General project questions**: Visit our discussions page
