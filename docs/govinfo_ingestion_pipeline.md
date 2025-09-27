# GovInfo Ingestion Pipeline Design

## Objectives
- Support full and incremental ingestion of federal legislative data from GovInfo bulk datasets and REST API.
- Normalize extracted content into PostgreSQL tables defined under `master.*` (bills, sponsors, actions, documents, ingestion tracking).
- Provide resumable, observable, and idempotent processing executed entirely in Python.

## Data Sources
1. **Bulk Data (`https://www.govinfo.gov/bulkdata`)**
   - Collections: `BILLS`, `PLAW`, `CRPT`, `CREC`, `CHRT`, `CCAL`, `NOM`, `FR`, `CFR` (see `tools/bulk_ingest_govinfo.py`).
   - Directory pattern: `/bulkdata/{COLLECTION}/{CONGRESS}/{SUBPATH}`. For bills, XML is nested by bill type (`hr`, `s`, etc.) and status/stage.
   - Preferred for complete backfills due to zipped packages and consistent directory layout.

2. **REST API (`https://api.govinfo.gov`)**
   - Provides metadata, package manifests, and document download URLs.
   - Requires `api_key` query parameter (register at <https://api.govinfo.gov/docs>). Rate limited (~5000 requests/day by default).
   - Key endpoints:
     - `/collections/{collection}/{congress}/{startDate}/{endDate}` – listing & pagination of new packages.
     - `/packages/{packageId}` – metadata for a package; includes `download` and `files` sections.
     - `/packages/{packageId}/summary` – normalized summary used for incremental updates.
     - `/packages/{packageId}/relationships` – cross-references (e.g., same-as, sponsors).
     - `/packages/{packageId}/ref` – references to ancillary files (PDF, mods XML, uslm XML).

## Architectural Components
1. **Discovery**
   - **Bulk**: enumerate congress/session directories, parse file names (`BILLS-118hr1ih.xml`). Maintain manifest of previously ingested ZIPs in `generic_ingestion_tracker` (`source='govinfo_bulk'`).
   - **API**: poll `/collections` and `/packages` for new package IDs since last run. Store checkpoints per collection/congress.

2. **Download & Staging**
   - Use streaming HTTP GET with retry/backoff (`requests.Session` + `HTTPAdapter`).
   - Stage ZIPs/XML to `staging/federal/{collection}/{congress}/` with content-addressed filenames.
   - Validate checksum / file length from API metadata when available.

3. **Parsing**
   - Use `lxml` to parse USLM (`*_uslm.xml`) and MODS (`*_mods.xml`) files.
   - Map to Python domain models (`Bill`, `BillStatus`, `BillAction`, etc.) using converters (e.g., `GovInfoBillParser`).
   - Handle relationships: same-as, sponsors, actions, versions.

4. **Normalization & Persistence**
   - Translate parsed models into `psycopg2` upsert statements for tables:
     - `master.bill`, `master.bill_amendment`, `master.bill_action`, `master.bill_sponsor`.
     - `master.govinfo_package` for metadata & checksums.
     - `master.source_document` for file references (see migrations `V20250921.*`).
   - Wrap DB operations in `BaseIngestionProcess` transaction helpers with commit per record.

5. **Tracking & Observability**
   - Leverage `GenericIngestionTracker` to record statuses (`pending`, `processing`, `completed`, `failed`) keyed by package ID.
   - Emit structured logs and optional progress bars.
   - Persist metrics (rows inserted, bytes downloaded, elapsed time) to `ingestion_log.json`.

6. **Error Handling & Resume**
   - Automatic retries for transient HTTP/DB failures (configurable per process).
   - Failed records remain in tracker with last error message; next run re-attempts after configurable cool-down.
   - Optional quarantine directory for problematic XML files.

## Module Layout
- `tools/fetch_govinfo_bulk.py`: bulk package downloader (per collection/congress).
- `tools/govinfo_data_connector.py`: REST API wrapper managing sessions, retries, manifests.
- `tools/govinfo_bill_ingestion.py`: orchestrates parsing + DB writes for USLM bill XML (to be expanded).
- `tools/ingest_govinfo_chunks.py`: CLI entry handling concurrency and resume features.
- `models/`: fully ported domain models used during parsing.
- `src/db/`: SQLAlchemy data-access layer (`base.py`, ORM models, Pydantic schemas, CRUD helpers, and service functions for API integrations).
- `tools/govinfo/models.py` / `tools/govinfo/persistence.py`: lightweight dataclasses and persistence utilities shared across bill/agenda/calendar/member/vote/status ingestors.
- `tools/govinfo/agenda_ingestion.py`, `tools/govinfo/calendar_ingestion.py`, `tools/member_data_ingestion.py`, `tools/bill_vote_ingestion.py`, `tools/bill_status_ingestion.py`: CLI wrappers for JSON payload ingestion (run with `--help` for options).
- `tools/govinfo_bill_ingestion.py`: supports multiple directories, glob patterns, explicit file lists, and recursive discovery via CLI flags (`--xml-dir`, `--pattern`, `--file`, `--recursive`).

### ORM Usage

Initial models include `Bill`, `BillAmendment`, `BillAmendmentAction`, and `BillSponsor`. They live under `src/db/models/bill.py` and match the
`master` schema used by the legacy application. The ORM exposes:

- `src/db/session.py`: database engine bootstrap, `session_scope()` context manager, and `init_db()` helper to materialise tables.
- `src/db/schemas/bill.py` / `src/db/schemas/committee.py` / `src/db/schemas/agenda.py`: Pydantic response objects for API serialization.
- `src/db/crud/bill.py`, `src/db/crud/committee.py`, `src/db/crud/agenda.py`: query primitives.
- `src/db/services/bill_service.py`, `src/db/services/committee_service.py`, `src/db/services/agenda_service.py`: high-level helpers returning Pydantic models ready for FastAPI/Flask endpoints.

Example API usage:

```python
from fastapi import APIRouter, HTTPException
from db.services.bill_service import fetch_bill, fetch_bills

router = APIRouter()

@router.get("/bills/{print_no}/{session_year}")
def read_bill(print_no: str, session_year: int):
    bill = fetch_bill(print_no, session_year)
    if bill is None:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill

@router.get("/bills")
def list_bill_endpoint(limit: int = 50, offset: int = 0):
    return fetch_bills(limit=limit, offset=offset)

@router.get("/committees/{chamber}/{name}")
def read_committee(chamber: str, name: str):
    committee = fetch_committee(name=name, chamber=chamber)
    if committee is None:
        raise HTTPException(status_code=404, detail="Committee not found")
    return committee

@router.get("/agendas/{year}/{agenda_no}")
def read_agenda(year: int, agenda_no: int):
    agenda = fetch_agenda(agenda_no=agenda_no, year=year)
    if agenda is None:
        raise HTTPException(status_code=404, detail="Agenda not found")
    return agenda
```

The ingestion workflow now persists via SQLAlchemy (`tools/govinfo_bill_ingestion.py`) ensuring that the same data
layer backs both ETL and the public API.

## Implementation Roadmap
1. Harden `GovInfoDataConnector` with parameterized API key, rate limiting, and pagination helpers.
2. Implement `GovInfoBulkDownloader` that stores manifests and returns file paths for pipeline ingestion.
3. Build `GovInfoBillParser` to convert XML into domain models (bill, sponsor, actions, amendments).
4. Implement `GovInfoBillWriter` to upsert into SQL using `psycopg2` + `ON CONFLICT` patterns from migrations `V20250921.0003__universal_bill_schema.sql` and `V20250921.0005__federal_member_ingestion_tracking.sql`.
5. Integrate parser + writer into `GovInfoBillIngestor`, enabling CLI-driven runs (per congress, optionally incremental via API).
6. Add PyPI dependencies to virtualenv (`requests`, `lxml`, `psycopg2-binary`, `tenacity` for retries) and document install in `README_DEV.md`.
7. Create pytest fixtures under `tools/tests/` covering parsing and DB persistence (use SQLite/PostgreSQL docker for integration as needed).

## CLI Commands

```bash
python tools/govinfo_bill_ingestion.py --xml-dir staging/govinfo/bills --pattern BILLS-*.xml BILLSTATUS-*.xml --recursive
python tools/govinfo/agenda_ingestion.py --json-dir staging/govinfo/agendas
python tools/govinfo/calendar_ingestion.py --json-dir staging/govinfo/calendars
```

All commands accept `--reset`, `--limit`, and `--log-level` switches for fine-grained control.

From the universal manager you can run:

```bash
python tools/manage_all_ingestion.py --run govinfo_agendas --json-dir /path/to/agendas
python tools/manage_all_ingestion.py --run govinfo_calendars --json-dir /path/to/calendars
python tools/manage_all_ingestion.py --run govinfo_bills --xml-dir /path/to/xml --pattern BILLS-*.xml --recursive
```

## Testing Guidance

1. Prepare a temporary PostgreSQL schema and run `python -c "from db.session import init_db; init_db()"`.
2. Drop sample GovInfo payloads (XML for bills, JSON for agendas/calendars) into the staging folders and execute the commands above.
3. Validate results using the service helpers (e.g. `fetch_bill`, `fetch_agenda`).
4. Use the unit tests in `tools/tests/test_govinfo_ingestion.py` as a template for additional persistence assertions.

For a detailed step-by-step walkthrough, see `docs/govinfo_ingestion_runbook.md`.

## Open Items
- Align with DB schema owners on canonical table names/columns (some migrations are placeholders dated 2025+).
- Decide on concurrency model (threaded vs. process). Initial implementation can be serial.
- Determine storage for large files (S3, shared disk) if long-term retention is required beyond staging.
