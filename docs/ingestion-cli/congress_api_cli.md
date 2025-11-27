# Congress API CLI

A lightweight CLI that incrementally ingests Congress.gov API resources while respecting offset-based pagination, rate limits, and concurrency.

## Key Features
- Offset/limit pagination with resumable state tracking
- Configurable rate limiting and worker count for concurrent downloads
- Duplicate protection via stable identifier tracking
- Writes NDJSON output for downstream consumers

## Usage
```bash
python tools/ingestion/congress_api_cli.py \
  --base-url https://api.congress.gov/v3 \
  --endpoint bill \
  --api-key $CONGRESS_API_KEY \
  --page-size 250 \
  --workers 6 \
  --rate-limit 5 \
  --state tools/ingestion/state/congress_state.json \
  --output tools/ingestion/output/congress.ndjson
```

### Helpful Flags
- `--extra chamber=senate` to scope results
- `--max-pages 10` to sample without processing the full catalog
- `--id-field url` to align with existing deduplication behaviour
