# Known Issues

This document tracks known issues and work-in-progress features in the OpenLegislation repository.

## Incomplete Federal Processors (Excluded from Build)

**Status**: Work in Progress  
**Last Updated**: 2025-11-09

### Description
The federal processors and services located in:
- `src/main/java/gov/nysenate/openleg/processors/federal/`
- `src/main/java/gov/nysenate/openleg/service/federal/`

These files are incomplete implementations that reference packages and classes that don't exist in the current codebase:
- `gov.nysenate.openleg.dao.bill.data.BillDao`
- `gov.nysenate.openleg.model.process.ProcessUnit`
- `gov.nysenate.openleg.service.process.LegDataProcessor`
- `gov.nysenate.openleg.processors.bill.XmlFile`

### Impact
These files are currently excluded from Maven compilation via the compiler plugin configuration in `pom.xml`.

### Resolution Path
To complete these processors:
1. Implement or locate the missing base classes and interfaces
2. Update import statements to match actual package structure
3. Complete method implementations
4. Add comprehensive tests
5. Remove exclusions from pom.xml once complete

### Affected Files
- `CongressionalRecordProcessor.java`
- `FederalCFRProcessor.java`
- `FederalHearingProcessor.java`
- `FederalMemberProcessor.java`
- `FederalRegisterProcessor.java`
- `GovInfoApiProcessor.java`
- `FederalBillXmlFile.java`
- `FederalBillXmlProcessor.java`
- `FsFederalBillXmlDao.java`
- `FederalLawXmlFile.java`
- `FederalReportXmlFile.java`
- `FederalIngestionService.java`
- `CongressApiIngestionService.java`

### Scripts Affected
The following scripts reference these incomplete processors and may not work:
- `AllMembersIngester.java` (references `FederalIngestionService.getMembers()` which doesn't exist)

## NPM Security Vulnerabilities

**Status**: ✅ RESOLVED  
**Severity**: Moderate (6 vulnerabilities) - NOW FIXED  
**Last Updated**: 2025-11-09

### Description
The PostCSS and related Tailwind CSS dependencies had known security vulnerabilities:
- PostCSS: CVE-2023-44270 (Regular Expression Denial of Service)
- PostCSS: GHSA-7fh5-64p2-3v2j (line return parsing error)

### Resolution Applied
Upgraded vulnerable dependencies in `src/main/webapp/package.json`:
- `tailwindcss`: Upgraded from `@tailwindcss/postcss7-compat@^2.2.17` to `^3.4.15`
- `postcss`: Upgraded from `^8.4.6` to `^8.4.47`
- `postcss-nested`: Upgraded from `^5.0.6` to `^6.2.0`

All npm vulnerabilities are now resolved (verified with `npm audit`).

### Note
The upgrade to Tailwind CSS 3.x may introduce breaking changes in CSS class names or configuration.
If styling issues are observed, consult the [Tailwind CSS v3 upgrade guide](https://tailwindcss.com/docs/upgrade-guide).

### Remaining Directories
The following directories were not checked/updated as they were not part of the main build:
- `frontend/` (separate Next.js app)
- `tests/frontend/` (frontend tests)
