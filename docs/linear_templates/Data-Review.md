# Data Review Issue Template

Summary
- Short summary of the data review task (one-liner)

Context
- Repository path(s): e.g., src/, data/, src/test/resources/
- Relevant docs: docs/data-ingestion-guidance.md, docs/govinfo_ingestion_runbook.md

Checklist
- [ ] Confirm ingestion run id / log attached
- [ ] Sample fixture(s) included and parsed
- [ ] Schema mappings documented (table, field, type)
- [ ] Edge cases noted (nulls, dates, encoding)

Steps
1. Describe what to inspect (collections, fixtures, DB tables)
2. Outline commands or SQL to run to reproduce the issue locally

Artifacts
- Attach ingestion_log.json and up to two sample fixture XMLs
- Attach sample SQL queries or DDL

Acceptance Criteria
- All failing records explained or reproduced
- PR or migration created if schema changes required
- Test case added to src/test/ for the failing fixture

Labels
- crew:data-review, type:review, priority:medium
