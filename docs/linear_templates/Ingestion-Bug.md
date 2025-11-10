# Ingestion Bug Report Template

Title
- Short reproducible title (e.g., 'Federal BILLS ingestion: Postgres transaction abort')

Description
- Describe the bug and include the exact error message.

Reproduction Steps
1. Command(s) to run
2. Sample fixture(s) path(s)
3. Database state or seed data used

Observed Behavior
- Copy/paste of logs and stack traces

Expected Behavior
- Clear statement of intended behavior or success criteria

Quick Diagnostic SQL
- Example: SELECT count(*) FROM staging.federal_bill WHERE collection = 'BILLS' AND congress = 119;

Suggested Immediate Fixes
- Look for transaction failures, ensure inserts are batched properly, add retry logic or transaction boundaries.

Labels
- crew:ingestion, type:bug, severity:high
