## 2025-09-29 12:56:11 UTC
- Add pytest-based regression coverage for `tools/ingest_congress_api.py` that mocks HTTP responses and exercises pagination, logging, and error handling code paths.
- Capture canonical congress.gov JSON fixtures (members, bills, hearings) to unblock dedicated processor tests called out in `docs/federal_ingestion_testing.md`.
- Wire the dry-run JSON export into the TUI/CLI so analysts can trigger ingestions directly from approved UI flows without shell access.
