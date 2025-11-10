Linear import helper

This folder contains a small helper script and CSV exports to build incremental batches of historical commits for import into Linear.

Files:
- linear_import_batches.py - split a commits CSV into numbered batch CSVs for review and import
- linear_commits_since_2024.csv - exported commits (hash,author,date,subject) since 2024-01-01
- batches/ - output directory for split batches (created by the script)

Workflow:
1. Review tools/linear_commits_since_2024.csv
2. Run the helper to produce batches: python3 tools/linear_import_batches.py --csv tools/linear_commits_since_2024.csv --out-dir tools/batches --batch-size 100
3. Inspect the CSVs in tools/batches/
4. Use the Linear CSV import or the API helper (not included here) to create issues. Ensure you include required fields such as team and project in the import payload.
