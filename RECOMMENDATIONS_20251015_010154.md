## 2025-10-15 01:01:54 UTC
- Automate creation of lightweight sample datasets (bill text excerpts, mock social media posts, member term snapshots) so analysts can exercise the research scripts without requiring a live database connection.
- Introduce pytest coverage for the research package by stubbing psycopg2 cursors and verifying JSON report structure for representative CLI invocations.
- Wire the new research scripts into a top-level CLI launcher (e.g., `tools/research/run_research.py`) that can execute multiple analyses in a single run with shared configuration flags.
