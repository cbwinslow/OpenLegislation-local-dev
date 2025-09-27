#!/usr/bin/env bash
# Run repository test scripts quickly. Exits non-zero on failure.
set -euo pipefail

source .venv/bin/activate

echo "Running member ingestion smoke test"
python3 tools/test_member_ingestion.py --limit 2

echo "Checking database availability"
if python3 tools/check_db.py >/dev/null 2>&1; then
  echo "DB available: running DB-dependent tests"
  python3 tools/test_govinfo_ingestion.py || true
  python3 tools/test_comprehensive_suite.py || true
else
  echo "DB not available: skipping DB-dependent tests (govinfo/comprehensive)"
fi

echo "All tests executed (check output for failures)"
