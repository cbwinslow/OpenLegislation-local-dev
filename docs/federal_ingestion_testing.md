# Federal Ingestion Test Strategy

The following matrix documents the recommended automated and manual checks for
the federal ingestion feature set.  Where tests already exist they are
referenced explicitly; gaps are highlighted for future implementation.

## Automated Tests

| Layer | Existing Coverage | Recommended Additions |
| --- | --- | --- |
| Domain model serialisation | `FederalMemberProcessorTest` validates mapping of member, committee, term, and social media payloads. | Add parameterised tests for `FederalBill`, `FederalCommittee`, and related aggregates using fixtures exported from dry-run CLI executions. |
| Processor workflows | `CongressionalRecordProcessorTest` ensures transcripts and record parsing remain stable. | Create focused tests for `FederalRegisterProcessor`, `FederalHearingProcessor`, and `FederalCFRProcessor` using sample JSON from the associated federal APIs. |
| Integration / orchestration | `FederalIngestionIntegrationTest` spans ingestion through persistence and search notification queues. | Extend the integration harness to run against Flyway-managed test databases seeded with the new federal migrations. |
| Python ingestion utility | _New_ | Add unit tests that exercise `map_congress_member`, `map_congress_bill`, and the OpenStates counterparts using static payloads.  Mock the HTTP session to validate pagination and logging behaviour without hitting the network. |

## Manual & Exploratory Testing

1. **Dry-run verification** – Execute the CLI with `--dry-run --output` and
   confirm the JSON mirrors the expected schema before allowing database writes.
2. **Database sanity checks** – After a production ingestion, validate row counts
   and spot-check a handful of records for correct key relationships (e.g.,
   committees referencing existing members).
3. **Search integration** – Trigger a re-indexing pass to ensure that newly
   ingested federal data appears in the Elastic-backed search endpoints.

## Fixture Management

* Capture representative payloads from the 118th and 119th Congress to cover
  edge cases (special elections, joint committees, hearings with multiple
  witnesses).
* Store fixtures under `src/test/resources/federal/` with descriptive filenames
  (e.g., `member_119_senate.json`).
* Reference these fixtures from both the Java tests and the Python unit tests to
  guarantee consistent expectations across the stack.

