# Govinfo.gov & Congress.gov Integration Plan - All Collections

## Overview
Comprehensive integration of all bulk data from govinfo.gov (XML/JSON, 2000+) and congress.gov (XML/JSON, recent congresses). Collections: legislative (bills, resolutions, laws, reports, records, hearings, calendars, nominations, treaties), regulatory (FR, CFR, USCODE), historical (statutes, papers, manuals). Use govinfo API/Link Service for access; GitHub usgpo repos for schemas/guides. Map to extended models; persist to PostgreSQL/ES.

## Data Sources & Access
- **Govinfo Bulk**: https://www.govinfo.gov/bulkdata – XML for BILLS (2013+), BILLSTATUS (113th+), BILL-SUMMARIES, CFR (1996+ annual/eCFR), FR (2000+), CREC (1994+), CHRG, CCAL, CRPT, PLAW, STATUTE, US-GOVERNMENT-MANUAL, PUBLIC-PAPERS, PRIVACY-ACT, HOUSE-RULES. JSON via /json endpoint.
- **Congress.gov Bulk**: https://www.congress.gov/bulkdata – BILLS, RESOLUTIONS, REPORTS, CONGRESSIONAL-RECORD, NOMINATIONS, TREATIES, HEARINGS, CALENDARS (XML/JSON, MODS schema).
- **API**: Govinfo API (api.data.gov key): Search/Retrieve services; Related Documents. Link Service: Parameter-based links (e.g., ?collection=FR&congress=119).
- **GitHub usgpo**: bulk-data (guides), uslm (legislative XSD), api (services), link-service (OpenAPI), rss (feeds), sitemap (crawling).
- **Downloads**: Scripts poll RSS/sitemaps; API for deltas. Samples in `test/resources/federal-samples/<collection>/`.

## General Pipeline
1. **Acquire**: `FederalBulkDownloader` – API query (e.g., 'collection:BILLS congress:119'), download/unzip to `staging/federal-<collection>`. Incremental via RSS.
2. **Parse Files**: Per-type `Federal<Type>File` (e.g., FederalFrXmlFile) extracts metadata (congress, date, ID from filename/headers).
3. **Process**: Route by SourceType to `processors/federal/<type>/<Type>Processor`. Unmarshal XML/JSON; map to models.
4. **Map & Validate**: Use adapters (e.g., FederalBillMapper); validate against uslm XSD.
5. **Persist**: DAOs insert/update; trigger ES indexing. Batch for bulk.
6. **Archive/Monitor**: Archive processed; log via ingestion_log.json.
7. **API**: `/api/3/federal/<collection>` endpoints.

## GovInfo API Endpoint Mappings to Java Classes

The following table maps GovInfo API search/retrieve endpoints (base: https://api.govinfo.gov/v1) to existing or planned Java models and processors in the OpenLegislation codebase. This ensures a generalized approach for ingestion scripts. Each collection uses /v1/search?collection={COLLECTION}&congress={CONGRESS}&api_key={KEY}&offset={OFFSET}&limit={LIMIT} for querying, with /v1/package/{COLLECTION}/{CONGRESS}/{PACKAGE_ID} for bulk retrieval.

| API Collection | Endpoint Example | Java Model | Processor Class | Notes |
|----------------|------------------|------------|-----------------|-------|
| BILLS | /v1/search?collection=BILLS&congress=119 | [`Bill`](src/main/java/gov/nysenate/openleg/legislation/bill/Bill.java) | [`GovInfoApiProcessor`](src/main/java/gov/nysenate/openleg/processors/federal/GovInfoApiProcessor.java) (extend for JSON parsing) | Map JSON 'search.results' to Bill fields (title, sponsors, actions). Use ObjectMapper for JSON. Persist via BillDao. |
| BILLSTATUS | /v1/search?collection=BILLSTATUS&congress=119 | [`Bill`](src/main/java/gov/nysenate/openleg/legislation/bill/Bill.java) | [`GovInfoApiProcessor`](src/main/java/gov/nysenate/openleg/processors/federal/GovInfoApiProcessor.java) | Update existing bills with status/actions. |
| PLAW | /v1/search?collection=PLAW&congress=119 | [`LawDocument`](src/main/java/gov/nysenate/openleg/legislation/law/LawDocument.java) (extend if needed) | FederalLawXmlProcessor (adapt for API JSON/XML) | Map to LawDocId, sections. Use JAXB for XML if retrieved. |
| CRPT | /v1/search?collection=CRPT&congress=119 | ReportDoc (new: src/main/java/gov/nysenate/openleg/legislation/federal/ReportDoc.java) | FederalReportXmlProcessor (adapt for API) | Map report-number, committee, text. |
| CREC | /v1/search?collection=CREC&from=2025-01-01 | RecordEntry (new: src/main/java/gov/nysenate/openleg/legislation/transcript/RecordEntry.java) | FederalRecordXmlProcessor (adapt) | Parse speeches; extend Transcript model. |
| CHRG | /v1/search?collection=CHRG&congress=119 | Hearing (extend Transcript) | FederalHearingXmlProcessor (adapt) | Map witnesses, statements. |
| CCAL | /v1/search?collection=CCAL&congress=119 | Calendar (extend existing) | FederalCalendarXmlProcessor (adapt) | Map bill references to entries. |
| NOM | /v1/search?collection=NOMINATIONS&congress=119 | NominationDoc (new) | FederalNominationXmlProcessor (adapt) | Map nominee, status. |
| TRTY | /v1/search?collection=TREATIES&congress=119 | TreatyDoc (new) | FederalTreatyXmlProcessor (adapt) | Map ratification details. |
| FR | /v1/search?collection=FR&from=2025-01-01 | FrDoc (new: src/main/java/gov/nysenate/openleg/legislation/federal/FrDoc.java) | FederalRegisterXmlProcessor (adapt via Link Service) | Map agency, body text. |
| CFR | /v1/search?collection=CFR&title=40 | CfrSection (new) | FederalCfrXmlProcessor (adapt) | Hierarchical: titles/parts/sections. |
| STATUTE | /v1/search?collection=STATUTE&congress=119 | StatuteDoc (new, extend LawDocument) | FederalStatuteXmlProcessor (adapt) | Historical statutes. |
| Other (e.g., SUMMARIES, MANUALS) | /v1/search?collection=BILL-SUMMARIES | SummaryDoc/ManualEntry (new) | Custom processors (simple DOM/JSON) | One-off mappings. |

**Generalization Notes**:
- Use a config-driven approach: Enum for collections, Map<Collection, Class<? extends LegContent>> for models.
- API Response: Always parse 'search.results' array; each hit has 'title', 'metadata' (sponsors, actions), 'link' for full doc.
- For XML retrieval: Use /v1/document/{COLLECTION}/{PACKAGE_ID}?format=XML.
- Error Handling: Check 'status' in response; retry on 429 (rate limit).
- Persistence: Route to specific DAOs (e.g., BillDao.insert(bill, NoticeNoOp)).

## Ingestion Script Usage

The ingestion is handled by [`GovInfoApiProcessor`](src/main/java/gov/nysenate/openleg/processors/federal/GovInfoApiProcessor.java), which implements Spring's CommandLineRunner for CLI execution.

### Configuration
- Edit `src/main/resources/govinfo-api.properties`:
  ```
  govinfo.api.key=your_api_key_here  # From api.data.gov
  govinfo.api.base-url=https://api.govinfo.gov/v1
  govinfo.api.limit=50
  govinfo.api.retry-max=3
  govinfo.api.retry-delay-ms=1000
  ```
- Logging: Configured in `src/main/resources/log4j2.xml` with rolling file `logs/ingestion-govinfo.log` (daily, 50MB max, 30 days retention). Includes timestamps, endpoint, processed count, errors.

### Running the Script
Build the project: `mvn clean compile`

Run for bills (default):
```
java -jar target/legislation-3.10.2.war GovInfoApiProcessor --congress=119
```

For other collections:
```
java -jar target/legislation-3.10.2.war GovInfoApiProcessor --congress=119 --collection=PLAW
```

- **Args**:
  - `--congress=119`: Required, congress number.
  - `--collection=BILLS`: Optional, default BILLS. Supported: BILLS, PLAW, CRPT, CREC (stubs for others).

- **Output**:
  - Console: Verbose INFO/DEBUG logs (progress, fetched URL, processed count).
  - File: Detailed logs in `logs/ingestion-govinfo.log` (e.g., "2025-09-27 03:45:00 INFO GovInfoApiProcessor: Processed 25 bills for congress 119").
  - Errors: Logged with stack traces; retries on transient failures (e.g., rate limit).

### Repeatability & Generalization
- **Config-Driven**: Properties for API params; CLI for runtime (congress, collection).
- **Extensibility**: Add cases in `processCollection()` for new collections; map JSON to specific models/DAOs.
- **Robustness**: Retry logic (3 attempts, backoff), JSON validation, exception trapping.
- **Monitoring**: Check logs for "Ingestion completed: X items"; query DB (e.g., SELECT COUNT(*) FROM bills WHERE federal_congress=119).

For bulk/full congress, paginate with offset/limit in future enhancements (API supports &offset=0&limit=1000 max).

Update `federal-integration-tasklist.md` with completions as implemented.

## Collection-Specific Mappings & Extensions

### Bills/Resolutions
| XML Path (Govinfo/Congress) | Model Field | SQL Column | Notes |
|-----------------------------|-------------|------------|-------|
| `<billNum congress/type>` | BaseBillId | bills.print_no, session_year | 'H.R. 1', map congress 119→2025 |
| `<officialTitle>` | Bill.title | bills.title | - |
| `<sponsor state/party/name>` | BillSponsor | bill_sponsors | district=null |
| `<action date/type/text>` | BillAction | bill_actions | Standardize types |
| BILLSTATUS `<status>` | Bill.status | bills.status | Updates |
| SUMMARIES `<summary>` | BillSummary | bill_summaries.text | New table |

- Processor: FederalBillXmlProcessor (JAXB uslm).
- Migration: ADD federal_congress TO bills.

### Laws (PLAW, STATUTE)
| XML Path | Model Field | SQL Column | Notes |
|----------|-------------|------------|-------|
| `<public-law number/date>` | LawDocId | laws.doc_id | PLAW-118-1 |
| `<section id/content>` | LawSection | law_sections | Hierarchical |
| STATUTE `<statute>` | StatuteDoc | statutes.text | Historical |

- Processor: FederalLawXmlProcessor.
- New: statutes table.

### Reports (CRPT, CPRT)
| XML Path | Model Field | SQL Column | Notes |
|----------|-------------|------------|-------|
| `<report-number congress>` | ReportId | reports.report_id | CRPT-118hrpt1 |
| `<committee/title>` | Report.committee, title | reports.committee, title | - |
| `<report-body>` | Report.text | reports.text | Full-text |

- Model: ReportDoc; Processor: FederalReportXmlProcessor.
- New table: reports (link to bills).

### Congressional Record (CREC)
| XML Path | Model Field | SQL Column | Notes |
|----------|-------------|------------|-------|
| `<congressional-record date/volume>` | RecordId | records.record_id | CREC-2025-01-03 |
| `<speech speaker/text>` | RecordEntry | record_entries (speaker, text) | Normalized or JSONB |

- Processor: FederalRecordXmlProcessor (parse pages/speeches).
- New table: congressional_records.

### Hearings (CHRG)
| XML Path | Model Field | SQL Column | Notes |
|----------|-------------|------------|-------|
| `<hearing id/date/committee>` | HearingId | hearings.hearing_id | CHRG-118hhrg12345 |
| `<witness name/statement>` | HearingWitness | hearing_witnesses | - |

- Extend Transcript; Processor: FederalHearingXmlProcessor.
- New table: hearings.

### Calendars (CCAL)
| XML Path | Model Field | SQL Column | Notes |
|----------|-------------|------------|-------|
| `<calendar date/type>` | CalendarId | calendars.calendar_id | Union/House |
| `<bill-reference>` | CalendarEntry | calendar_entries | Link to bills |

- Processor: FederalCalendarXmlProcessor.
- Extend calendars.

### Nominations/Treaties
| XML Path | Model Field | SQL Column | Notes |
|----------|-------------|------------|-------|
| `<nomination id/nominee/status>` | NominationId | nominations.nom_id | Nom-118-1 |
| `<treaty number/ratification>` | TreatyId | treaties.treaty_id | Treaty-118-1 |

- Processors: FederalNominationXmlProcessor, FederalTreatyXmlProcessor.
- New tables: nominations, treaties.

### Federal Register (FR)
| XML Path | Model Field | SQL Column | Notes |
|----------|-------------|------------|-------|
| `<DOCUMENT doc-number/date>` | FrDocId | fr_docs.doc_id | 2025-01-01;R1 |
| `<AGENCY>`, `<BODY>` | FrDoc.agency, text | fr_docs.agency, text | Rule/Notice |

- Processor: FederalRegisterXmlProcessor (via Link Service).
- New table: federal_register (full-text).

### CFR/USCODE
| XML Path | Model Field | SQL Column | Notes |
|----------|-------------|------------|-------|
| `<CFR TITLE/PART/SECTION>` | CfrSectionId | cfr_sections.id | 40 CFR 1.1 |
| `<amendments>` | CfrVersion | cfr_versions | Effective date |

- Processor: FederalCfrXmlProcessor (hierarchical parse).
- New tables: cfr_titles/parts/sections.
- USCODE: Similar, table uscode_sections.

### Other Collections
- **Summaries/Manuals/Papers**: Map to SummaryDoc/ManualEntry/PaperDoc; one-off processors.
- **Privacy Act/House Rules**: Static XML → new entries in privacy_act/rules tables.

## Challenges/Solutions
- **Formats/Schemas**: XML dominant; validate with uslm XSD (usgpo/uslm). JSON via API.
- **Volume/Updates**: Bulk ZIPs large; use API pagination, RSS for deltas (usgpo/rss).
- **Mapping Gaps**: Regulatory (FR/CFR) need new models; use Link Service for metadata.
- **Performance**: Streaming JAXB; async processing; ES for search.
- **Validation**: Spotchecks per collection; compare via usgpo/bill-status samples.

## Next Steps
1. Implement core (bills/laws) using API/Link Service.
2. Add regulatory (FR/CFR) with new models.
3. Bulk scripts integrating RSS/sitemaps (usgpo repos).
4. Full tests/migrations for all.

See federal-ingestion-prompts.md for Copilot assistance; usgpo/bulk-data for guides.
