# Recommendations 20251102_033612

- Integrate the new `tools/federal_ingest` CLI entrypoints with existing orchestration scripts (e.g., `manage_all_ingestion.py`) to ensure federal data jobs are scheduled consistently with state-level imports.
- Add unit tests that exercise the normalization helpers against recorded API fixtures to prevent schema regressions as upstream providers evolve.
- Consider caching or checkpointing bulkdata crawl state (e.g., storing last-seen resource keys) to avoid repeatedly traversing large directory trees during scheduled runs.
