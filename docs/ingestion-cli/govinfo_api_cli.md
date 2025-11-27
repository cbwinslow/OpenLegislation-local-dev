# GovInfo API CLI

Ingests paginated GovInfo collections while persisting progress so downloads can be resumed and deduplicated safely.

## Key Features
- Offset/page-size pagination with resumable state
- Rate limiting and concurrent fetch controls
- NDJSON output for downstream parsers
- Stable ID tracking to prevent duplicate writes

## Usage
```bash
python tools/ingestion/govinfo_api_cli.py \
  --base-url https://api.govinfo.gov \
  --endpoint collections/BILLS \
  --api-key $GOVINFO_API_KEY \
  --page-size 100 \
  --workers 6 \
  --rate-limit 4 \
  --state tools/ingestion/state/govinfo_state.json \
  --output tools/ingestion/output/govinfo.ndjson
```

### Helpful Flags
- `--extra startDate=2020-01-01` to window results
- `--max-pages 5` to validate settings without a full run
- `--id-field packageId` to align with the GovInfo package schema
