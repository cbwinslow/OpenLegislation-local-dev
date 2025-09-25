# Federal Data Ingestion Prompts for Copilot - All Collections

Use these in VS Code Copilot Chat. Grouped by collection; reference GitHub usgpo repos (bulk-data guides, uslm schema) and govinfo API/Link Service.

## Setup (All)
"Add SourceType enums for all federal collections: FEDERAL_BILL, FEDERAL_LAW, FEDERAL_REPORT, FEDERAL_RECORD, FEDERAL_HEARING, FEDERAL_CALENDAR, FEDERAL_NOMINATION, FEDERAL_TREATY, FEDERAL_REGISTER, FEDERAL_CFR, FEDERAL_STATUTE to legislation/SourceType.java."

"Create base FederalXmlFile extending XmlFile for congress.gov/govinfo XML: parse filename for congress/date/type using regex from usgpo/collections repo."

"Implement FsFederalBulkDao: download ZIP via govinfo API (api.data.gov key), unzip to staging/federal-<collection>, process recursively."

## Bills/Resolutions (BILLS, BILLSTATUS, SUMMARIES)
"Implement FederalBillXmlProcessor.java in processors/federal/bill/: Parse govinfo BILLS XML <billset><bill>: legislation-id congress/type/number → BaseBillId('H.R. 1', 2025); official-title → title; sponsor → BillSponsor (state, party); actions → BillAction. Use JAXB with uslm schema."

"Create FederalBillStatusProcessor for BILLSTATUS XML: Update bill statuses/actions from 113th+; map to BillUpdateService."

"Write BillSummaryMapper: govinfo summaries XML <summary> to BillSummary model, link to existing bills."

"Generate unit test FederalBillProcessorTest: Load sample BILLS-119th-HR1.xml, assert BaseBillId, sponsors list size=1."

## Laws (PLAW, STATUTE)
"FederalLawXmlProcessor in processors/federal/law/: Parse PLAW XML <public-law>: number/date → LawDocId; sections → LawSection; map to LawDocument/LawTree. Handle private laws separately."

"Extend LawDao for federal: Batch insert PLAW, add federal_congress column via migration."

"Test: FederalLawTest with sample PLAW-118-1.xml, verify LawDocId and section count."

## Committee Reports (CRPT, CPRT)
"Create Report model and FederalReportXmlProcessor: congress.gov REPORTS XML <report>: report-number → ReportId; committee/title/text → ReportDoc fields. Link to bills via <related-bill>."

"SQL: Propose migration add reports table (report_id, congress, committee, text); foreign key to bills."

"Prompt for parser: Map CRPT XML <report-body> to full-text search index."

"Unit test: Assert report linked to bill HR1."

## Congressional Record (CREC)
"FederalRecordXmlProcessor: Parse CREC XML <congressional-record>: date/volume → RecordId; <page>/<speech> → RecordEntry (speaker, text). Handle daily editions."

"New model RecordEntry; SQL table congressional_records (date, volume, entries JSONB or normalized)."

"Test: Ingest sample CREC-2025-01-03.xml, search for 'speech' keyword."

## Hearings (CHRG)
"FederalHearingXmlProcessor extending TranscriptProcessor: CHRG XML <hearing>: id/date/committee → HearingId; <witness>/<statement> → HearingWitness/Testimony."

"SQL: hearings table (hearing_id, congress, committee, witnesses array)."

"Parser prompt: Extract hearing location/address from <location>."

"Integration test: Verify testimony searchable via Elasticsearch."

## Calendars (CCAL)
"FederalCalendarXmlProcessor extend CalendarProcessor: CCAL XML <calendar>: date/type → CalendarId; bills → CalendarBillEntry."

"Extend calendars table with federal_congress, calendar_type (Union/House)."

"Test: Map sample calendar to existing Calendar model."

## Nominations/Treaties
"FederalNominationXmlProcessor: NOMINATIONS XML <nomination>: id/nominee/status → NominationDoc; committee actions."

"New Nomination model; table nominations (id, congress, nominee, status)."

"Similar for TREATIES: Treaty number/ratification → TreatyDoc."

"Test: Assert nomination status 'Confirmed'."

## Federal Register (FR)
"FederalRegisterXmlProcessor: FR XML <FR> <DOCUMENT>: doc-number/date/agency → FrDocId; <BODY> → text. Classify as rule/notice."

"New FrDoc model; table federal_register (doc_id, date, agency, type, text). GIN index on text."

"Use Link Service for retrieval: /link?collection=FR&congress=119."

"Test: Parse sample FR-2025-01-01.xml, assert agency='EPA'."

## CFR/USCODE
"FederalCfrXmlProcessor: CFR XML <CFR> <TITLE>/<PART>/<SECTION> → CfrSectionId; amendments to version history."

"Models: CfrTitle, CfrPart, CfrSection; tables cfr_titles/parts/sections (title_num, part_num, section_num, text, effective_date)."

"USCODE similar: <USC> <TITLE> to UsCodeSection."

"Migration: Add cfr tables with full-text search."

"Test: Ingest eCFR Title 40 Part 1, verify section hierarchy."

## Other (Manuals, Papers, Privacy Act, Rules)
"FederalManualProcessor for US-GOVERNMENT-MANUAL XML: Parse agency descriptions to ManualEntry."

"PublicPapersProcessor: PUBLIC-PAPERS XML speeches to PaperDoc (president, date, text)."

"HouseRulesProcessor: One-off for HOUSE-RULES XML to RulesDoc."

"Extend for PRIVACY-ACT: Agency systems to PrivacyEntry."

## Bulk/API Integration
"Create FederalBulkDownloader: Use govinfo API (Search Service) to query 'congress:119 collection:BILLS', download via retrieve endpoint. Handle pagination."

"RSS Poller: Parse usgpo/rss feeds for new CREC/FR, trigger incremental ingestion."

"Sitemap Crawler: Use usgpo/sitemap to discover updates, process deltas."

"Link Service Util: Generate links for collections via OpenAPI spec from usgpo/link-service."

## General Testing/SQL
"Extend IngestionIntegrationIT with federal multi-collection test: Ingest bill+report+record, verify links."

"Flyway migrations: V20250924.0003__federal_tables.sql – Add reports, hearings, fr, cfr schemas."

"Spotcheck: FederalSpotcheck comparing XML extract vs. DB query for each collection."

Copy-paste into Copilot. Review against usgpo/bulk-data guides and uslm schema.