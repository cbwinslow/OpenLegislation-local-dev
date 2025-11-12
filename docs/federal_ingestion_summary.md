# Federal Data Ingestion Summary Sheet

This document summarises the current state of the federal ingestion code paths
within the OpenLegislation project.  It is intended to act as a living checklist
while we close the gap between the state-level and federal-level models.

## Legend

* **Component** – Logical grouping (model, DAO, processor, etc.).
* **Primary Class** – Entry point in the Java/Python code base.
* **Schema / Migration** – Flyway migration that provisions the SQL surface.
* **Test Coverage** – JUnit/utility tests that currently exercise the component.
* **Notes** – Implementation status, follow-up tasks, or integration details.

## Coverage Matrix

| Component | Primary Class | Schema / Migration | Test Coverage | Notes |
| --- | --- | --- | --- | --- |
| Federal Member domain model | `model/federal/FederalMember` | `V20250929.0001__federal_data_model.sql` | `FederalMemberProcessorTest` | Serialises core biographical data and relationships to committees, terms, and social media. |
| Federal Member committee linkage | `model/federal/FederalMemberCommittee` | `V20250929.0001__federal_data_model.sql` | `FederalMemberProcessorTest` | Committee assignments are mapped via the processor using JSON payloads from the ingestion layer. |
| Federal Member social media | `model/federal/FederalMemberSocialMedia` | `V20250929.0001__federal_data_model.sql` | `FederalMemberProcessorTest` | Social metadata normalised for downstream syndication and analytics. |
| Federal Member term history | `model/federal/FederalMemberTerm` | `V20250929.0001__federal_data_model.sql` | `FederalMemberProcessorTest` | Provides chronological term tracking with chamber and district metadata. |
| Federal Committee aggregate | `model/federal/FederalCommittee` | `V20250929.0001__federal_data_model.sql` | _Pending dedicated tests_ | Members and subcommittees populated from the ingestion mappers. |
| Federal Congressional Record | `processors/federal/CongressionalRecordProcessor` | `V20250929.0001__federal_data_model.sql` | `CongressionalRecordProcessorTest` | Parses floor proceedings, attaches to transcripts, and creates searchable artefacts. |
| Federal Hearing ingestion | `processors/federal/FederalHearingProcessor` | `V20250929.0001__federal_data_model.sql` | _Pending dedicated tests_ | Normalises committee hearings for indexing. |
| Federal Register ingestion | `processors/federal/FederalRegisterProcessor` | `V20250929.0001__federal_data_model.sql` | _Pending dedicated tests_ | Integrates Federal Register notices into the archival store. |
| Federal CFR ingestion | `processors/federal/FederalCFRProcessor` | `V20250929.0001__federal_data_model.sql` | _Pending dedicated tests_ | Handles Code of Federal Regulations updates and cross references. |
| Federal bill ingestion service | `service/ingestion/federal/FederalBillIngestionService` | `V20250929.0001__federal_bills_table.sql` | _Pending dedicated tests_ | Translates congress.gov bill payloads into the legacy `master.bills` schema with federal extensions. |
| Federal ingestion orchestration | `service/federal/FederalIngestionService` | `V20250928.0001__ingestion_optimizations.sql` | `FederalIngestionIntegrationTest` | Coordinates batched imports, processors, and the search notification layer. |
| Congress.gov CLI bridge | `tools/ingest_congress_api.py` | Utilises existing schema; logs runs in `tools/ingestion_log.json` | Covered via dry-run execution and integration smoke tests | Generates deterministic payloads for ingestion and mirrors Java mappers. |

## Outstanding Work

* Add targeted JUnit coverage for the processors without dedicated tests.
* Extend repository DAO coverage to verify SQL mappings against the Flyway
  migrations listed above.
* Enrich the Python ingestion utility with fixtures so that unit tests can
  operate without network access (e.g., via VCR or local JSON samples).

