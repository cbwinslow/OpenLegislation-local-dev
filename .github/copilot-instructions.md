# Open Legislation Processing Instructions

This repository is a Java-based legislative data platform (Open Legislation) focused on ingesting, processing, indexing, and serving legislative content.

Keep responses concise and action-oriented. When making code changes, reference the concrete files below and follow existing patterns (DAO -> Processor -> Service -> API controllers). Prioritize minimal, focused edits and include unit tests when touching parsing logic.

Quick architecture notes
- Backend: Java (Maven) under `src/main/java/gov/nysenate/openleg/`.
- Data processing pipeline: `processors/` package. Source file DAOs live in `processors/sourcefile`; per-domain processors in `processors/{bill,law,calendar,agenda,committee}`.
- Source files: incoming XMLs are read from the `staging/xmls` directory via `processors/sourcefile/xml/FsXmlDao.java` and `processors/sourcefile/sobi` for older SOBI formats.
- Domain models and persistence: legislative models live under `legislation/` and search/update layers under `search/` and `updates/`.
- Web/API: controllers under `api/` expose data and admin endpoints (e.g. `ProcessService` endpoints used to trigger processing).

Developer workflows (important commands)
- Build & DB migrate: `mvn compile flyway:migrate` (project uses Java 17 and Flyway migrations in `src/main/resources/sql/migrations`).
- Run in Tomcat (typical dev): import as a Maven project in IntelliJ and run `legislation:war exploded` as described in `docs/backend/index.md`.
- Trigger processing (after placing XML files into `env.staging/xmls`):
  - POST to `http://localhost:8080/api/3/admin/process/run` with admin credentials set in `src/main/resources/app.properties`.

Project-specific patterns and conventions
- File naming & timestamp parsing: XML source filenames follow the pattern parsed by `processors/bill/xml/XmlFile.java` (regex with date/time and type). Use this class for any filename/time parsing.
- Source types: `SourceType` enum drives per-file routing. New ingestion should implement `SourceFileFsDao` for filesystem source access and a `LegDataProcessor` subclass to parse domain objects.
- Encoding edge-cases: files containing `_SENAGEN_` use `CP1252` encoding (see `FsXmlDao.toXmlFile`). Preserve this behavior for any new file ingestion.
- XML mapping libraries: project includes `jackson-dataformat-xml` and `jaxb` dependencies (see `pom.xml`). Follow existing JAXB/Jackson patterns used in `processors/*/xml/*`.
- Archiving: source archiving logic uses `environment.getArchiveDir()` in DAOs; prefer reusing `SourceFileFsDao.archiveSourceFile` behavior to move processed files.

Where to look for parsing examples (copy patterns)
- Bills: `src/main/java/gov/nysenate/openleg/processors/bill/xml/` (many `Xml*Processor` classes).
- Law: `src/main/java/gov/nysenate/openleg/processors/law/` and `legislation/law/` model classes.
- Calendars/Agendas: `processors/calendar/` and `legislation/calendar/`.
- Source file DAOs: `processors/sourcefile/xml/FsXmlDao.java` and `processors/sourcefile/sobi/*`.

Integration guidance for govinfo.gov / congress.gov bulk XML
- Big picture: govinfo and congress.gov provide XML schemas for federal legislative documents (bills, committee reports, CRs). OpenLegislation is structured around per-source file processors that parse XML into domain models and persist/update index. Treat govinfo/congress XML as a new SourceType and implement a processing pipeline that maps their elements to OpenLegislation domain models.
- Steps to integrate (practical, discoverable):
  1. Add a new `SourceType` value (if needed) and implement a `SourceFile` representation analogous to `XmlFile` (filename parsing, published date extraction).
  2. Implement a `SourceFileFsDao` to read govinfo files from a staging dir (reuse `FsXmlDao` logic).
  3. Create `processors/{bill,law,...}/govinfo/` or `processors/federal/` to house parsers that map govinfo/congress fields to existing models. Start by copying structure from `processors/bill/xml/XmlBillTextProcessor` and similar classes.
  4. Map id fields carefully: OpenLegislation uses specific identifiers (e.g. `BaseBillId`, `LawDocId`). Create small adapters that translate govinfo `bill/legislation-id`, `congress-bill-id`, or `report-number` into these models.
  5. Respect archiving & encoding conventions and use existing `LegDataProcessService` to wire new processors into the processing flow.

Schema analysis hints (where to compare)
- OpenLegislation examples to map fields from:
  - Filename/timestamp parsing: `processors/bill/xml/XmlFile.java`
  - Bill text and actions mapping: `processors/bill/xml/XmlBillTextProcessor.java`, `XmlBillActionAnalyzer.java`
  - Law document ids and tree: `legislation/law/LawDocId.java`, `legislation/law/LawTree.java`
- Govinfo/congress.gov schema locations (agent should fetch these live):
  - govinfo bulk data XML (package schema and sample XML files)
  - congress.gov bulk data (bill XML schema and sample files)
  - When analyzing schemas, produce a short mapping table (source XML path -> OpenLegislation model field) for the most important fields: identifiers, title, sponsors, actions, text, publication dates.

When to ask for human help
- If the source XML contains fields with unclear semantic equivalents (e.g., nested amendment histories, multi-version text deltas), summarize the ambiguity and propose a mapping; ask which OpenLegislation model should own the data.
- If new external dependencies are required for parsing (non-standard encodings, large streaming parsers), propose them and include CI/build impact.

Pull request style
- Keep changes small and testable. Include unit tests under `src/test/java` using existing test fixtures in `src/test/resources` (look at `testing_utils` and `processor` test resources).
- Update `docs/backend/index.md` only when adding new setup steps for federal data ingestion.

If you modify processing behavior, run or add tests that exercise `processors/*` classes. Reference example test utilities in `src/test/java/testing_utils/`.

Ask for feedback on any unclear repository-specific behavior or when you need access to sample govinfo/congress XML documents to produce concrete field mappings.

## Federal Data Integration (Congress.gov / Govinfo.gov) - All Collections

### Overview
Integrate all major federal legislative and regulatory data types from congress.gov bulk data and govinfo.gov bulk repository. Collections include bills/resolutions, laws (public/private), committee reports, congressional records, nominations, treaties, hearings, calendars, federal register, code of federal regulations (CFR), statutes at large, and more. Map to OpenLegislation domain models (extend as needed for regulatory data) and persist to PostgreSQL with Elasticsearch indexing. Follow NY Senate patterns but adapt for federal schemas (XML primarily, some JSON).

### Key Resources
- **Congress.gov Bulk Data**: https://www.congress.gov/bulkdata – XML/JSON for BILLS, RESOLUTIONS, REPORTS, CONGRESSIONAL-RECORD, NOMINATIONS, TREATIES, HEARINGS, CALENDARS. Schemas in MODS/MODS extensions.
- **Govinfo.gov Bulk Data**: https://www.govinfo.gov/bulkdata – XML for BILLSTATUS (113th+), BILLS (2013+ House, 2015+ Senate), BILL-SUMMARIES, CFR (1996+ annual, eCFR current), FEDERAL-REGISTER (2000+), US-GOVERNMENT-MANUAL (2011+), PUBLIC-PAPERS (2009-2011), PRIVACY-ACT (select years), HOUSE-RULES (114th). JSON endpoints available. Schemas/XSDs in GitHub usgpo/uslm for legislative markup.
- **Govinfo Developers**: https://www.govinfo.gov/developers – API (api.data.gov key for search/retrieve), Link Service (query-based links to collections: BILLS, CCAL, CPRT, CDOC, CHRG, CREC, CRPT, FR, PLAW, STATUTE, USCODE), RSS feeds per collection, Sitemaps for crawling.
- **GitHub Repos** (usgpo org, as GovInfo org is new/empty):
  - usgpo/api: GovInfo API services.
  - usgpo/bill-status: Sample Bill Status XML/guide.
  - usgpo/bulk-data: XML bulk user guides.
  - usgpo/collections: Metadata regex.
  - usgpo/link-service: Content/metadata links (OpenAPI/Swagger).
  - usgpo/rss: New content notifications.
  - usgpo/sitemap: Crawling sitemaps.
  - usgpo/uslm: US Legislative Markup XML Schema.
- **Samples**: Download via govinfo bulk links; store in `src/test/resources/federal-samples/<collection>/`. Use tools/fetch_govinfo_bulk.py for automation.

### General Integration Process
1. **SourceType Extensions**: Add enums in `legislation/SourceType.java`: `FEDERAL_BILL`, `FEDERAL_LAW`, `FEDERAL_REPORT`, `FEDERAL_RECORD`, `FEDERAL_HEARING`, `FEDERAL_CALENDAR`, `FEDERAL_NOMINATION`, `FEDERAL_TREATY`, `FEDERAL_REGISTER`, `FEDERAL_CFR`, `FEDERAL_STATUTE`.
2. **File Handling**: Extend `XmlFile`/`JsonFile` for each (e.g., `FederalBillXmlFile`, `CfrXmlFile`). Implement DAOs like `FsFederalBillDao` reading from `env.staging/federal-<collection>/`.
3. **Processors**: Create `processors/federal/<type>/` packages. Use JAXB/Jackson for XML/JSON unmarshalling. Map to models (Bill, LawDocument, new for regulatory like `FederalRegisterDoc`).
4. **Mapping Principles**: Federal IDs (congress number → session year, e.g., 119th=2025-2026). Chambers: HOUSE/SENATE. Handle amendments/versions. For non-legislative (FR/CFR), extend models or create new (e.g., `RegulatoryDoc`).
5. **Persistence**: Use/extend DAOs (BillDao, LawDao); add federal-specific fields via Flyway (e.g., congress_number, federal_chamber). Batch inserts for bulk.
6. **API Exposure**: Add controllers `/api/3/federal/<type>` querying by congress/session.
7. **Testing**: Unit/integration tests per collection; spotchecks comparing source vs. ingested.
8. **Bulk Ingestion**: Scripts to download/unzip/process via API/bulk links; use RSS/sitemaps for updates.

### Collection-Specific Guidance

#### 1. Bills/Resolutions (BILLS, BILLSTATUS, BILL-SUMMARIES)
- **Sources**: Congress.gov BILLS XML/JSON; Govinfo BILLSTATUS (XML 113th+), BILLS (XML 2013+), SUMMARIES.
- **Mapping**: As before – `<legislation-id>` → BaseBillId; `<sponsor>` → BillSponsor; `<action>` → BillAction; summaries to BillSummary.
- **Processor**: `FederalBillXmlProcessor` (extend XmlBillProcessor); handle resolutions similarly (SourceType.FEDERAL_RESOLUTION).
- **SQL**: Extend bills table with federal_congress, resolution_type.
- **Edge Cases**: Multi-version bills; status updates via BILLSTATUS.

#### 2. Laws (PLAW, STATUTE)
- **Sources**: Govinfo PLAW (Public/Private Laws XML); STATUTE (Statutes at Large XML).
- **Mapping**: `<public-law>` → LawDocId; sections to LawSection; effective dates.
- **Processor**: `FederalLawXmlProcessor` (extend LawProcessor); map to LawDocument/LawTree.
- **SQL**: Extend laws with federal_congress, law_type (public/private).
- **Edge Cases**: Vetoed laws; historical statutes.

#### 3. Committee Reports (CRPT, CPRT)
- **Sources**: Congress.gov REPORTS XML; Govinfo CRPT (Reports XML).
- **Mapping**: Report number → new ReportId; committee, title, text to ReportDoc.
- **Processor**: `FederalReportXmlProcessor`; create Report model if needed.
- **SQL**: New table reports (report_id, congress, committee, text); link to bills via reference.
- **Edge Cases**: Multi-volume reports; amendments.

#### 4. Congressional Record (CREC)
- **Sources**: Congress.gov CONGRESSIONAL-RECORD XML; Govinfo CREC (Daily XML 1994+).
- **Mapping**: Date/edition → RecordId; debates/actions to RecordEntry (speaker, text).
- **Processor**: `FederalRecordXmlProcessor`; parse <page>, <speech>.
- **SQL**: New table congressional_records (date, volume, pages, text); index for search.
- **Edge Cases**: Daily vs. bound editions; OCR errors in older.

#### 5. Hearings (CHRG)
- **Sources**: Congress.gov HEARINGS XML; Govinfo CHRG (Hearings XML).
- **Mapping**: Hearing ID/date → HearingId; committee, witnesses, testimony to HearingDoc.
- **Processor**: `FederalHearingXmlProcessor`; extend TranscriptProcessor patterns.
- **SQL**: New table hearings (hearing_id, congress, committee, date, transcript).
- **Edge Cases**: Audio/video links; classified sessions.

#### 6. Calendars (CCAL)
- **Sources**: Congress.gov CALENDARS XML; Govinfo CCAL (Calendars XML).
- **Mapping**: Calendar date/type → CalendarId; bills/agendas to CalendarEntry.
- **Processor**: `FederalCalendarXmlProcessor` (extend CalendarProcessor).
- **SQL**: Extend calendars with federal_congress, chamber.
- **Edge Cases**: Union Calendar vs. House Calendar.

#### 7. Nominations/Treaties (NOMINATIONS, TREATIES)
- **Sources**: Congress.gov NOMINATIONS/TREATIES XML.
- **Mapping**: Nominee ID → NominationId; status, committee to NominationDoc; similar for treaties.
- **Processor**: `FederalNominationXmlProcessor`, `FederalTreatyXmlProcessor`.
- **SQL**: New tables nominations (id, congress, nominee_name, status), treaties (treaty_number, status).
- **Edge Cases**: Confirmation votes; ratification.

#### 8. Federal Register (FR)
- **Sources**: Govinfo FR (XML 2000+).
- **Mapping**: Document number/date → FrDocId; agency, rules/notices to FrEntry.
- **Processor**: `FederalRegisterXmlProcessor`; parse <FRFILING-DATE>, <AGENCY>.
- **SQL**: New table federal_register (doc_number, date, agency, text); full-text search.
- **Edge Cases**: Proposed vs. final rules; comments.

#### 9. Code of Federal Regulations (CFR, USCODE)
- **Sources**: Govinfo CFR (Annual XML 1996+, eCFR current); USCODE XML.
- **Mapping**: Title/part/section → CfrSectionId; amendments to CfrDoc.
- **Processor**: `FederalCfrXmlProcessor` (extend LawProcessor for structure); USCODE similar.
- **SQL**: New tables cfr_titles, cfr_parts, cfr_sections (title, part, section, text, effective_date).
- **Edge Cases**: Annual updates; cross-references.

#### 10. Other (Summaries, Manuals, Papers)
- **Summaries**: Map to BillSummary model.
- **Government Manual**: Static docs → new ManualDoc.
- **Public Papers**: Speeches → new PaperEntry.
- **Privacy Act/House Rules**: One-off processors for select years.

### Bulk Download/Ingestion
- Use Govinfo API/Link Service for programmatic access (e.g., retrieve by congress/collection).
- Scripts: Extend `tools/fetch_govinfo_bulk.py` for all collections; unzip/process via `FederalBulkIngester`.
- Updates: Poll RSS/sitemaps; delta ingestion via modified dates.

### Testing/Validation
- Samples per collection in `test/resources/federal-samples/<collection>/`.
- Integration: Extend `IngestionIntegrationIT` with multi-collection tests.
- Spotchecks: `spotchecks/federal/<type>/` comparing XML vs. DB.

### Copilot Prompts
(Existing + new for each collection, e.g., "Create FederalReportXmlProcessor for CRPT XML: map report-number to ReportId, committee to ReportCommittee...")

### Troubleshooting
- Schemas: Use usgpo/uslm XSD; validate XML.
- Volume: Streaming parsers for large FR/CFR.
- Compatibility: Java 21; no new deps needed.

Follow per-collection for targeted tasks. Start with bills, then expand.
