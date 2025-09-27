# Open Legislation Processing Instructions

## Overview
OpenLegislation is a Java-based legislative data platform focused on ingesting, processing, indexing, and serving legislative content from New York State and federal sources (govinfo/congress.gov).

- **Tech Stack**: Java 17, Spring 5, PostgreSQL, Elasticsearch 8, React, Tomcat 9.
- **License**: Dual BSD/GPL.
- **API**: JSON API at legislation.nysenate.gov (docs: http://legislation.nysenate.gov/static/docs/html/).

## Architecture
- **Backend**: Java (Maven) under `src/main/java/gov/nysenate/openleg/`.
- **Data Processing Pipeline**: `processors/` package. Source file DAOs in `processors/sourcefile`; per-domain processors in `processors/{bill,law,calendar,agenda,committee}`.
- **Source Files**: Incoming XMLs from `staging/xmls` via `processors/sourcefile/xml/FsXmlDao.java` and `processors/sourcefile/sobi` for SOBI.
- **Domain Models & Persistence**: `legislation/` for models; `search/` and `updates/` for indexing/updates.
- **Web/API**: Controllers in `api/`; admin endpoints like `ProcessService` for triggering processing.

Data flow: Ingest raw files (XML/SOBI) → Parse via processors → Persist to PostgreSQL → Index in Elasticsearch → Expose via REST API.

## Developer Workflows
- **Build & Migrate DB**: `mvn compile flyway:migrate` (Flyway in `src/main/resources/sql/migrations`).
- **Run in Tomcat**: Import as Maven project in IntelliJ; run `legislation:war exploded` (see `docs/backend/index.md`).
- **Trigger Processing**: Place XMLs in `env.staging/xmls`; POST to `http://localhost:8080/api/3/admin/process/run` with admin creds from `src/main/resources/app.properties`.
- **Tests**: `mvn test`; unit tests in `src/test/java` using fixtures in `src/test/resources`.
- **Bulk Federal Ingestion**: Use `tools/fetch_govinfo_bulk.py` or `tools/bulk_ingest_congress_gov.sh` for downloads.

## Conventions & Patterns
- **File Naming/Timestamp Parsing**: Use `processors/bill/xml/XmlFile.java` regex for XML filenames (date/time/type).
- **Source Types**: `SourceType` enum routes files; implement `SourceFileFsDao` for FS access, `LegDataProcessor` subclass for parsing.
- **Encoding**: `_SENAGEN_` files use CP1252 (see `FsXmlDao.toXmlFile`).
- **XML Mapping**: Jackson-dataformat-xml & JAXB (pom.xml); follow patterns in `processors/*/xml/*`.
- **Archiving**: Reuse `SourceFileFsDao.archiveSourceFile` with `environment.getArchiveDir()`.

Examples:
- Bill processing: `processors/bill/xml/XmlBillTextProcessor.java`, `XmlBillActionAnalyzer.java`.
- Law: `processors/law/`, `legislation/law/` models.

## Federal Integration (Congress.gov / Govinfo.gov)
- **Sources**: Bulk XML/JSON from congress.gov (BILLS, REPORTS, etc.) & govinfo (BILLSTATUS, FR, CFR).
- **Steps**:
  1. New `SourceType` (e.g., `FEDERAL_BILL`).
  2. Extend `XmlFile`/`JsonFile`; DAO like `FsFederalBillDao` for `env.staging/federal-<collection>/`.
  3. Processors in `processors/federal/<type>/`; map to models (Bill, LawDocument; new for regulatory).
  4. IDs: Translate govinfo `bill/legislation-id` to `BaseBillId`.
  5. Persistence: Extend DAOs; Flyway for federal fields (congress_number).
  6. API: `/api/3/federal/<type>`.
- **Mapping Examples**: See `docs/govinfo-119-mapping.md`; use USLM schema (`src/main/resources/schema/uslm/`).
- **Tools**: `tools/fetch_govinfo_bulk.py`, `tools/govinfo_bill_ingestion.py`.
- **Testing**: Samples in `src/test/resources/federal-samples/`; extend `IngestionIntegrationIT`.

## Troubleshooting
- Validate XML with USLM XSD (`uslm-bill.xsd`).
- For large files, use streaming parsers.
- If unclear mappings, reference `docs/{congress_gov_integration.md, govinfo-integration.md}`.

Keep changes small, testable; update docs/backend/index.md for new setups.
