# Recommendations (2025-09-26T06:50:09Z)

1. Add automated CI step that runs `tools/generate_table_mapping.py --show-summary` to catch migration/table mismatches early.
2. Extend `tools/bulkdata_pipeline.py` with persistent cursors so interrupted bulk downloads can resume without re-fetching completed files.
3. Integrate the new downloader with existing ingestion orchestration scripts in `tools/manage_all_ingestion.py` to avoid duplicate scheduling logic.
