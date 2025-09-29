# Federal Ingestion Procedures

The purpose of this guide is to provide a reproducible set of instructions for
running the federal ingestion workflow end-to-end.  The workflow is composed of
three phases:

1. **Acquisition** – Fetch raw payloads from congress.gov or OpenStates.
2. **Translation** – Normalise the payloads to match the Java domain model and
   SQL schema defined in the Flyway migrations.
3. **Persistence** – Store the transformed records in PostgreSQL using the
   existing repositories.

This guide assumes the Flyway migrations in
`V20250928.0001__ingestion_optimizations.sql` and
`V20250929.0001__federal_data_model.sql` have been applied and that the
Spring Boot application can reach the target database.

## 1. Acquisition via CLI

The `tools/ingest_congress_api.py` script now exposes a parameterised interface
that mirrors the Java ingestion services.  A typical dry-run for the 119th
Congress members looks like the following:

```bash
./tools/ingest_congress_api.py --source congress --endpoint member \
    --batch 25 --dry-run --output tmp/congress_members.json \
    congress --congress 119
```

Key flags:

* `--dry-run` prevents database writes while still emitting mapped payloads.
* `--output` writes the mapped rows to disk so they can be replayed by tests.
* `--session-year` (for the bill endpoint) allows explicit control over the
  session year that feeds into the Java models.

For OpenStates source data:

```bash
./tools/ingest_congress_api.py --source openstates --endpoint member \
    --batch 50 --dry-run --output tmp/ca_legislators.json \
    openstates --state ca
```

The ingester automatically records offsets and outcomes in
`tools/ingestion_log.json`, allowing resumed execution in later runs.

## 2. Translation inside the Java stack

1. The ingestion controller (`IngestionController`) dispatches to
   `FederalIngestionService`, which determines the appropriate processor.
2. Processors (e.g., `FederalMemberProcessor`,
   `CongressionalRecordProcessor`) translate API-specific JSON into domain
   objects such as `FederalMember` and `FederalHearing`.
3. The DAO layer writes the resulting models into the tables provisioned by the
   migrations listed above.

When introducing new payload fields, ensure the domain model, DAO mapper, and
Flyway migration remain aligned.  The summary sheet in
`docs/federal_ingestion_summary.md` tracks the relationships between the three
layers.

## 3. Persistence & Verification

* The integration test `FederalIngestionIntegrationTest` exercises the full
  ingestion flow against a controlled dataset.
* Repository-level tests can reuse the JSON fixtures produced by the dry-run
  CLI to assert the exact SQL output.
* After running the ingester without `--dry-run`, inspect the counts logged in
  `tools/ingestion_log.json` and verify the deltas against the destination
  tables.

## Appendices

### A. Troubleshooting Checklist

1. Ensure `CONGRESS_API_KEY` or `OPENSTATES_API_KEY` is exported in the shell.
2. Confirm the database credentials in `DB_URL` correspond to the environment
   used by Spring Boot.
3. If API calls fail with throttling errors, adjust the `BATCH_SIZE` environment
   variable or re-run with the persisted offset.

### B. Integration Into the Web UI / CLI

* The existing TUI/CLI entry points can invoke the Python script via `subprocess`
  while passing user-provided filters (congress number, state, batch size).
* Web flows should surface the dry-run payload as a downloadable attachment for
  audit before committing data to the master schema.

