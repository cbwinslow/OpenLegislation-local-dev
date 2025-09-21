# Congress.gov Integration Tasks

## Phase 1: Analysis & Planning
- [x] Analyze existing OpenLegislation codebase structure
- [x] Review current SQL schema and data models
- [x] Examine govinfo mapping documentation
- [x] Research congress.gov data sources (bulk XML vs API)
- [x] Identify bulk data extraction methods

### Recent Work Summary (completed)

- [x] Implemented a govinfo enumerator script to discover bulkdata collections and subdirectories (`tools/govinfo_enumerate.sh`).
- [x] Created a pure-stdlib Python fallback parser `tools/govinfo_parse_to_json_fallback.py` to extract title/sponsors/actions from staged BILLS XML fixtures (used when `lxml` is unavailable).
- [x] Staged sample BILLS XML fixtures under `src/test/resources/processor/govinfo/BILLS/119/` for unit tests and parser validation.
- [x] Added Postgres example connection values for Zerotier host `172.28.208.142:5433` to `src/main/resources/app.properties.example`.
- [x] Added a repository `.env` template and a local `app.properties.local` to centralize DB credentials for development.
- [x] Created `.gitconfig.example` containing `user.name = cbwinslow` and `user.email = blaine.winslow@gmail.com`.


## Phase 2: Data Model Design
- [x] Design SQL tables mapped to congress.gov data
- [x] Create Java classes to represent govinfo data structures
- [ ] Map govinfo XML elements to existing Bill model fields
- [ ] Determine staging vs direct master table approach

## Phase 3: Data Extraction
- [x] Implement bulk data extraction logic (Python crawler)
- [ ] Create automated fetching pipeline
- [ ] Handle incremental updates and change detection
- [ ] Implement rate limiting and error handling

### Next Immediate Tasks (high priority)

- [ ] Run the enumerator at scale to produce a full JSONL inventory of available collections and years using `tools/govinfo_enumerate.sh --collections BILLS --out /tmp/govinfo_enum.jsonl` and adjust `--max-subdirs/--max-files` as needed.
- [ ] Use the inventory to download representative samples via `tools/download_govinfo_samples.sh` and store them under `/tmp/govinfo_samples/<collection>/`.
- [ ] Run `tools/govinfo_parse_to_json_fallback.py` against the downloaded samples to validate parsing heuristics and produce coverage stats.
- [ ] Port robust parsing logic to `src/main/java/gov/nysenate/openleg/processors/bill/govinfo/GovInfoBillProcessor.java` and add unit tests under `src/test/resources/processor/govinfo/`.


## Phase 4: Data Processing
- [ ] Implement XML parsing in GovInfoBillProcessor
- [ ] Map parsed data to Bill/BillAction/BillSponsor objects
- [ ] Handle federal vs state data model differences
- [ ] Implement data validation and error handling

## Phase 5: Data Ingestion
- [ ] Create DAO layer for govinfo data insertion
- [ ] Implement transaction management for bulk inserts
- [ ] Add data deduplication logic
- [ ] Create indexing and performance optimizations

## Phase 6: Integration & Testing
- [ ] Integrate with existing processing pipeline
- [ ] Create unit tests for XML parsing
- [ ] Implement end-to-end integration tests
- [ ] Add monitoring and logging

## Phase 7: Production Deployment
- [ ] Set up production data fetching schedule
- [ ] Implement data quality monitoring
- [ ] Create rollback procedures
- [ ] Document operational procedures

### Completed Checklist (repo-level changes)

- [x] Added `.env` template with DB credentials and JDBC URL at project root.
- [x] Added `src/main/resources/app.properties.local` for local Java app properties.
- [x] Added `.gitconfig.example` with requested git identity (`cbwinslow`, `blaine.winslow@gmail.com`).

If you want, I can now run the enumerator at scale and download a year's worth of sample files. This requires network access and may take several minutes depending on rate limits.

## Key Considerations
- **Data Volume**: Congress.gov has ~200k+ bills, regular updates
- **Schema Evolution**: Handle XML schema changes over time
- **Data Quality**: Validate federal data against existing patterns
- **Performance**: Optimize for large bulk inserts
- **Conflict Resolution**: Handle duplicate bills across jurisdictions