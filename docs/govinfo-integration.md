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
