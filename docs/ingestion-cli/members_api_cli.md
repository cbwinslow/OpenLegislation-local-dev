# Members API CLI

Fetches member data incrementally with resumable pagination, deduplication, and concurrent downloads.

## Key Features
- Offset-based pagination with persisted state files
- Configurable concurrency and rate limiting
- Duplicate protection using configurable identifier fields
- Emits NDJSON output for downstream pipelines

## Usage
```bash
python tools/ingestion/members_api_cli.py \
  --base-url https://api.congress.gov/v3 \
  --endpoint member \
  --api-key $CONGRESS_API_KEY \
  --page-size 200 \
  --workers 6 \
  --rate-limit 5 \
  --state tools/ingestion/state/members_state.json \
  --output tools/ingestion/output/members.ndjson
```

### Helpful Flags
- `--extra congress=118` to scope to a single congress
- `--max-pages 3` for smoke tests
- `--id-field bioguideId` to align with the existing member data model
