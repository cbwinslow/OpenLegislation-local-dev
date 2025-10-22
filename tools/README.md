# Tooling Overview

This directory contains Python utilities that support data ingestion, analysis, and research for the OpenLegislation platform. Scripts are grouped by functional area:

- **Ingestion**: `ingest_*.py`, `*_ingestion.py`, and orchestration helpers used to pull legislative data from source systems.
- **Operations**: provisioning scripts (`install_*.sh`), diagnostics, and scheduling helpers.
- **Research & Analytics**: reusable analysis utilities located under `research/` for building reports that inform policy and social media research initiatives.

## Research Scripts

The `research/` subdirectory provides reproducible analysis pipelines built on top of the PostgreSQL datasets. Each script supports command-line usage and emits JSON summaries in the `reports/` folder by default.

| Script | Purpose |
| ------ | ------- |
| `bill_text_research.py` | Performs TF–IDF keyword extraction, topic modeling, and sentiment analysis across recent federal bill texts. |
| `social_media_research.py` | Aggregates social media engagement, sentiment, topic clusters, and mention networks for legislator accounts. |
| `member_activity_research.py` | Summarizes chamber/party composition, tenure statistics, and recent freshman cohorts for federal members. |

Run any script with `--help` to view available options. Example:

```bash
python -m tools.research.bill_text_research --limit 100 --session-year 2023 --topics 8
```

Reports can be directed to a specific directory by passing `--output /path/to/reports`. When a database is unavailable, social media research supports JSON Lines inputs via `--input sample.jsonl`.
