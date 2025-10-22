# Legislative Data Methods and Analysis Research

## Overview
This document summarizes ingestion and analysis methods relevant to the OpenLegislation data pipeline. It distills the official documentation that accompanies each source platform and highlights workflow considerations for maintaining accurate, timely legislative data.

## Source Platform Capabilities
### Congress.gov
- **Primary access patterns:** The Congress.gov API provides JSON responses for bills, amendments, congressional records, committee meetings, and member data. Bulk XML and JSON packages are synchronized with the Government Publishing Office (GPO) collections and updated daily when Congress is in session.
- **Authentication & limits:** API keys issued by the Library of Congress are required. The service enforces per-key rate limits (default 5 requests/second and 5000 requests/day) and recommends key rotation for high-volume tasks.
- **Data nuances:** Item-level metadata includes action histories, sponsor/cosponsor details, committee referrals, and summaries. Bulk downloads lag the live site by several hours; monitoring timestamps is necessary to detect late postings.
- **Recommended workflow:** Use incremental API pulls keyed by the `updateDate` field for near-real-time ingestion, while scheduling nightly validation jobs that compare API payloads to the synchronized bulk data for completeness.

### GovInfo
- **Primary access patterns:** GovInfo exposes RESTful endpoints for collections (e.g., BILLS, STATUTE, CREC) with support for pagination, filtering by congress/session, and retrieval of PDF, XML, or JSON renditions. The `search` endpoint powers keyword discovery and accepts query modifiers for date ranges and collection facets.
- **Authentication & limits:** API keys are required, with soft throttling around 1000 requests/hour. Requests without keys are subject to heavier throttling and lower concurrency.
- **Data nuances:** Metadata includes package-level properties (e.g., `packageId`, `publicationDate`, `lastModified`). Some collections (such as STATUTE) provide only PDF/HTML outputs; schema parity varies by collection, so normalization must branch based on `collectionCode`.
- **Recommended workflow:** Mirror the `lastModified` timestamps in a control table and design backfill routines that honor collection-specific date hierarchies. Combine the API with the official Sitemaps for redundancy.

### OpenStates
- **Primary access patterns:** OpenStates v3 API offers REST and GraphQL interfaces covering bills, events, people, committees, and vote events. Snapshots of the full dataset are available via nightly S3 exports for bulk replication.
- **Authentication & limits:** API tokens are mandatory. Standard plans allow ~1 request/second sustained throughput; higher tiers can negotiate increased limits.
- **Data nuances:** Jurisdictions update on heterogeneous cadences. Bill identifiers follow jurisdiction-specific numbering schemes, and vote data may lack roll call breakdowns for some chambers.
- **Recommended workflow:** Favor GraphQL queries for targeted incremental updates (e.g., bills updated since a timestamp). Use nightly S3 snapshots to reconcile missing entities and detect deletions.

### NYS OpenLegislation
- **Primary access patterns:** The New York State Open Legislation API exposes REST endpoints for bills, calendars, agendas, transcripts, and law documents, with optional bulk downloads of nightly data dumps.
- **Authentication & limits:** API keys are required; default rate limits permit roughly 5 requests/second. Elevated access can be requested for large-scale consumers.
- **Data nuances:** Bill data is versioned by `printNo` and `session`. Committee agendas link to attachments stored separately. Some historical transcripts are OCR-derived and require post-processing for accuracy.
- **Recommended workflow:** Implement session-aware crawlers that step through print numbers and check the `publishDate` for incremental updates. Use checksum comparisons when downloading attachments to prevent duplicate storage.

## Cross-Source Harmonization Strategy
1. **Canonical Identifiers:** Map each item to a composite key of jurisdiction, session, chamber, and item identifier. Maintain translation tables for differences in numbering schemes (e.g., OpenStates vs. NYS print numbers).
2. **Schema Normalization:** Create intermediate staging tables shaped around shared entities (Bill, Action, Vote, Member). Use structural metadata from each source to map required fields and flag optional attributes that may be sparse.
3. **Temporal Consistency:** Track ingestion timestamps and source `lastModified` values. Reprocess records when upstream timestamps advance or when reconciliation jobs detect mismatches between API and bulk data.
4. **Text Processing:** Normalize whitespace and encoding for bill texts and transcripts. Apply diff-based checks to detect revisions, and index tokenized versions for downstream search analytics.

## Quality Assurance & Monitoring
- **Validation Rules:** Enforce schema validation (JSON Schema or XSD) at the staging layer. Cross-check sponsor lists and vote totals against authoritative counts published by each platform.
- **Observability:** Emit metrics for request success rates, throttling responses, and per-source latency. Log payload hashes to detect unexpected content shifts.
- **Recovery Procedures:** Maintain replay queues for failed ingestions. For each source, document manual fallback steps (e.g., retrieving static dumps) when APIs are unavailable.

## Analytical Applications
- **Legislative Tracking Dashboards:** Combine normalized data to build cross-jurisdiction bill progression timelines and floor activity heat maps.
- **Stakeholder Reports:** Generate automated summaries for stakeholders highlighting new introductions, committee outcomes, and sponsorship networks.
- **Policy Research Pipelines:** Enable downstream NLP tasks (topic modeling, sentiment) using cleaned transcripts and bill texts to support policy analysis and constituent services.

