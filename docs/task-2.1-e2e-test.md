# Task 2.1: End-to-End Test for Bills (High)

## Overview
This task performs an end-to-end test of the federal bills integration: Download a sample ZIP from govinfo.gov, place in staging, trigger processing via API, verify DB persistence and fields. This validates the full pipeline (download → staging → DAO → processor → DB → API query).

## Dependencies
- Task 1.1 (JAXB generated).
- Task 1.2 (JAXB integrated).
- Task 1.3 (BillActionType extended).
- Task 1.4 (Federal fields added).
- Bulk script from Task 2.3 (partial).

## Estimated Effort
2 hours.

## Status
Partial (unit/integration pass; full E2E needs API/DB verify).

## Microgoals
1. **Prepare Sample ZIP**:
   - Download BILLS-119th ZIP from https://www.govinfo.gov/bulkdata/BILLS/119th (or use sample ZIP if available).
   - Unzip to temp dir, verify 1+ XML files (e.g., BILLS-119th-HR1.xml).
   - Copy 1 XML to `staging/federal-xmls/` for testing.

2. **Trigger Processing via API**:
   - Ensure app running (mvn tomcat7:run-war).
   - POST to /api/3/admin/process/run with {"sourceType": "FEDERAL_BILL_XML"} (auth with user/pass).
   - Check logs for "Processed federal bill: BILLS-119th-HR1.xml".

3. **Verify DB Persistence**:
   - Query: SELECT * FROM bills WHERE print_no LIKE 'HR%' AND session_year=2025 LIMIT 1.
   - Assert fields: title="To provide...", federal_congress=119, sponsors=1, actions=1.
   - Check audit_log: INSERT for bills table.

4. **Query via API**:
   - GET /api/3/federal/bills/HR1?congress=119 (assume endpoint from Task 5.2; if not, add simple controller).
   - Assert JSON has title, sponsors, actions.

5. **Error Case Test**:
   - Place invalid XML in staging, trigger API, assert ParseError logged, no DB entry.

6. **Automate in Script**:
   - Extend tools/fetch_govinfo_bulk.py: download_unzip_process(congress=119, collection="BILLS").
   - Run script, verify DB count >0.

## Completion Criteria
- API POST succeeds (200 OK, logs show processing).
- DB has 1+ bills with correct fields (query returns title, federal_congress=119).
- API GET returns JSON with mapped data (title, sponsors array size=1).
- Error test logs ParseError, DB unchanged.
- Script runs end-to-end (download → process → verify count=10+).

After completion, Phase 2 starts with Task 2.2 (Laws).
