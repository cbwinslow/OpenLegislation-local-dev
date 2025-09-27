# Ingestion Procedures for OpenLegislation

## Overview
This document provides repeatable procedures for ingesting data from GovInfo API into the OpenLegislation database. The process is hybrid: Python for fetching/parsing (flexible for API/XML), Java for mapping/persistence (leverages JPA to SQL tables). It's generalized for all collections (BILLS, FR, CFR, CREC, etc.) with parameters (congress range, limit). Robust features: Chunked batches (50/item to respect rate limits), resume from log.json (if interrupted), error handling (skip dups, log failures), progress logging.

**Key Components**:
- **Scripts**: Python (tools/ingest_govinfo_chunks.py for core ingestion, tools/run_ingestion.sh for wrapper).
- **Java Classes/Entities**: IngestionService (orchestrates), GovInfoApiProcessor (maps JSON → models), Document/Bill (entities), DocumentRepository (JPA repo for SQL).
- **Tables**: bill (BILLS), law_document (FR/CFR), transcript (CREC), etc. (JPA maps @Entity to tables).
- **Websites/Endpoints**: GovInfo API (https://api.govinfo.gov/v1/search?collection=BILLS&congress=119&api_key=yourkey).
- **UI**: Web page at /ingest-ui.html (text boxes for params, real-time progress via WebSocket).

**Prerequisites**:
- API key: Register at api.govinfo.gov, add to .env (GOVINFO_API_KEY=yourkey).
- DB: PostgreSQL (openlegdb), tables via Flyway (run `mvn flyway:migrate`).
- Java: Compiled project (`mvn clean compile`).
- Python: Venv activated (`source tools/venv/bin/activate`), deps installed (`pip install -r tools/requirements.txt`).
- Server: Tomcat running (`mvn tomcat7:run`) for UI/API.

## Setup Procedure (One-Time)
1. **Install Deps**:
   - Java: `mvn clean compile` (builds processors).
   - Python: `cd tools && source venv/bin/activate && pip install -r requirements.txt` (requests, psycopg2, etc.).
   - DB: `mvn flyway:migrate` (creates bill, transcript tables).

2. **Configure .env**:
   ```
   GOVINFO_API_KEY=yourkey
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=openlegdb
   DB_USER=postgres
   DB_PASS=yourpass
   ```

3. **Test Setup**:
   - API: `curl "https://api.govinfo.gov/v1/collections?api_key=$GOVINFO_API_KEY"` (lists collections).
   - DB: `psql openlegdb -c "\dt"` (shows tables like bill).
   - UI: `mvn tomcat7:run`, visit http://localhost:8080/ingest-ui.html.

## General Ingestion Procedure (Repeatable)
For any collection (e.g., BILLS, FR):
1. **Choose Params**: Site= GovInfo, Collection=BILLS, Congress=113-119 (range), Limit=50 (batch size).
2. **Run Script**: `./tools/run_ingestion.sh --site govinfo --collection BILLS --congress 113-119 --limit 50`.
   - Fetches JSON from API (chunked by congress).
   - Parses/maps to Java models (e.g., title → Bill.setTitle()).
   - Persists via JPA (e.g., Bill → bill table INSERT/UPDATE).
   - Logs to ingestion_log.json (resume offset/total).
3. **Monitor**: Check log.json for progress (e.g., "Congress 113: 82 items"). UI shows real-time bar/logs.
4. **Verify**: `psql openlegdb -c "SELECT count(*) FROM bill WHERE congress_number BETWEEN 113 AND 119;"` (e.g., 487 rows).

**Resume**: If interrupted, rerun with same params—script loads from log.json (skips completed congress).

## Procedures by Collection
### BILLS (Bill Text/Status)
- **Website/Endpoint**: https://api.govinfo.gov/v1/search?collection=BILLS&congress=119&api_key=yourkey (JSON with title, sponsors, actions).
- **Classes/Entities**: GovInfoApiProcessor.processBILLS() (Jackson unmarshal → Bill entity), Bill.java (@Entity, fields: title, sponsors List<BillSponsor>).
- **Tables**: bill (title VARCHAR, congress_number INT, data_source='GOVINFO'), bill_sponsor (member_name VARCHAR).
- **Mapping**: JSON {"title": "HR 1"} → Bill.setTitle("HR 1"); sponsors array → BillSponsor.setMemberName().
- **Procedure**:
  1. Run: `./tools/run_ingestion.sh --collection BILLS --congress 113-119`.
  2. Output: ~487 bills (113-119 congress), logged as "Ingested HR1 (pkgid: GOVDOC-2025-1)".
  3. Verify: `psql -c "SELECT title FROM bill WHERE congress_number=119 LIMIT 1;"` → "H.R.1 - For the People Act".

### FR (Federal Register)
- **Website/Endpoint**: https://api.govinfo.gov/v1/search?collection=FR&api_key=yourkey (JSON with title, agency, sections).
- **Classes/Entities**: GovInfoApiProcessor.processFR() → LawDocument (@Entity, fields: lawId, metadata JSONB).
- **Tables**: law_document (title VARCHAR, metadata JSONB for agency/sections).
- **Mapping**: JSON {"notice": {"title": "Rule", "agency": "DOE"}} → LawDocument.setTitle("Rule"), metadata={"agency": "DOE"}.
- **Procedure**:
  1. Run: `./tools/run_ingestion.sh --collection FR --congress 119` (use year for FR).
  2. Output: Notices/rules ingested, e.g., "Ingested FR-2025-123 (agency: DOE)".
  3. Verify: `psql -c "SELECT title FROM law_document WHERE metadata->>'agency' = 'DOE' LIMIT 1;"`.

### CFR (Code of Federal Regulations)
- **Website/Endpoint**: https://api.govinfo.gov/v1/search?collection=CFR&api_key=yourkey (JSON with title/part/section).
- **Classes/Entities**: GovInfoApiProcessor.processCFR() → Law (@Entity, fields: title, sections List<LawSection>).
- **Tables**: law (title VARCHAR, sections JSONB for hierarchy).
- **Mapping**: JSON {"title": {"parts": [{"sections": [{"text": "Reg"}] } ]}} → Law.setTitle("Title"), sections JSONB.
- **Procedure**:
  1. Run: `./tools/run_ingestion.sh --collection CFR --limit 100`.
  2. Output: Regulations ingested, e.g., "Ingested CFR Title 1 Part 1".
  3. Verify: `psql -c "SELECT title FROM law WHERE sections ? 'part' LIMIT 1;"`.

### CREC (Congressional Record)
- **Website/Endpoint**: https://api.govinfo.gov/v1/search?collection=CREC&api_key=yourkey (JSON with date, debates).
- **Classes/Entities**: GovInfoApiProcessor.processCREC() → Transcript (@Entity, fields: date, content TEXT).
- **Tables**: transcript (date DATE, content TEXT, source='CREC').
- **Mapping**: JSON {"record": {"date": "2025-09-25", "debates": "Text"}} → Transcript.setDate("2025-09-25"), setContent("Text").
- **Procedure**:
  1. Run: `./tools/run_ingestion.sh --collection CREC --limit 50`.
  2. Output: Records ingested, e.g., "Ingested CREC 2025-09-25".
  3. Verify: `psql -c "SELECT date FROM transcript WHERE source='CREC' ORDER BY date DESC LIMIT 1;"`.

### Other Collections (PLAW, HEARINGS, etc.)
- Similar: Extend script/UI with --collection PLAW (public laws → LawDocument), HEARINGS (hearings → Hearing model/table).
- Procedure: Same as above; add to GovInfoApiProcessor.processPLAW().

## Scripts
- **run_ingestion.sh** (Bash wrapper): `./tools/run_ingestion.sh --site govinfo --collection BILLS --congress 113-119 --limit 50`.
  - Calls ingest_govinfo_chunks.py with params.
  - Resume: Loads from ingestion_log.json.
- **ingest_govinfo_chunks.py** (Python core): Fetches API (requests), chunks by congress (50/batch), maps to Java (subprocess mvn exec), persists (psycopg2 upsert).
  - Log: ingestion_log.json (congress/total/offset).
- **fetch_govinfo_bulk.py** (Python): Bulk download for XML (alternative to API).

## Important Objects
- **Entities/Models (Java)**:
  - Bill.java (@Entity @Table(name="bill"), fields: title, congress_number, sponsors List<BillSponsor>).
  - LawDocument.java (@Entity @Table(name="law_document"), fields: lawId, metadata JSONB).
  - Transcript.java (@Entity @Table(name="transcript"), fields: date, content).
  - BillSponsor.java (member_name, party).
- **Repositories (Java JPA)**:
  - DocumentRepository (extends JpaRepository<Document, Long>, methods: saveAll, existsByUrl, findBySource).
  - BillDao (save Bill → bill table).
- **Services (Java)**:
  - IngestionService (ingestFromRSS, broadcast progress via SimpMessagingTemplate to /topic/progress).
  - GovInfoApiProcessor (processBILLS: JSON → Bill, processFR: → LawDocument).
- **Tables (SQL/Postgres)**:
  - bill: title VARCHAR, congress_number INT, data_source VARCHAR, govinfo_pkg_id UNIQUE.
  - law_document: title VARCHAR, metadata JSONB.
  - transcript: date DATE, content TEXT, source VARCHAR.
  - JPA Mapping: @Column(name="title") private String title; → bill.title VARCHAR.

## Websites/Endpoints
- **GovInfo API**: https://api.govinfo.gov (base).
  - /v1/collections (list).
  - /v1/search?collection=BILLS&congress=119 (data).
  - /v1/package/GOVDOC-2025-1 (full bill).
- **Local UI**: http://localhost:8080/ingest-ui.html (text boxes: congress "113-119", limit "50", dropdown site/collection, start button, progress bar/logs).

## Troubleshooting
- API Error (500/401): Check .env key (register if dummy).
- DB "relation does not exist": Run `mvn flyway:migrate`.
- Script Fail: Check log.json, resume with same params.
- UI No Progress: Ensure Tomcat running, WebSocket connected (/ws endpoint).

For repetition: Bookmark UI or alias `alias ingest='./tools/run_ingestion.sh'`. Extend for new sites (add to UI dropdown, script flag).
