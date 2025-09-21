#!/usr/bin/env bash
set -euo pipefail

# Helper to demonstrate how to gather multi-year GovInfo samples using
# `tools/download_govinfo_samples.sh` and to summarize locally-staged fixtures.
#
# Usage:
#   ./tools/prove_govinfo_gather.sh --congresses 116,117,118,119 --max 50 --out /tmp/govinfo_samples --dry-run

OUT=/tmp/govinfo_samples
CONGRESSES="116,117,118,119"
COLLECTIONS="BILLS,BILLSTATUS,BILLSUM"
MAX=200
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT="$2"; shift 2 ;;
    --congresses) CONGRESSES="$2"; shift 2 ;;
    --collections) COLLECTIONS="$2"; shift 2 ;;
    --max) MAX="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift 1 ;;
    -h|--help) echo "Usage: $0 [--out DIR] [--congresses 116,117] [--collections BILLS] [--max N] [--dry-run]"; exit 0 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

echo "Proving GovInfo gatherability"
echo "  out: $OUT"
echo "  congresses: $CONGRESSES"
echo "  collections: $COLLECTIONS"
echo "  max per collection: $MAX"
echo "  dry-run: $DRY_RUN"

IFS=',' read -r -a CONG_ARR <<< "$CONGRESSES"
IFS=',' read -r -a COL_ARR <<< "$COLLECTIONS"

echo
echo "Local fixtures summary (repo test fixtures under src/test/resources/processor/govinfo):"
find src/test/resources/processor/govinfo -type f -name "*.xml" -print | sed -n '1,200p' || true

echo
for col in "${COL_ARR[@]}"; do
  for cong in "${CONG_ARR[@]}"; do
    echo "Collection=$col Congress=$cong -> target: $OUT/$col/$cong/"
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "  DRY RUN: would run: tools/download_govinfo_samples.sh --out $OUT --collections $col --max $MAX"
    else
      echo "  Running downloader for $col $cong (may take time)"
      tools/download_govinfo_samples.sh --out "$OUT" --collections "$col" --max "$MAX"
    fi
  done
done

echo
echo "After downloads, summarize counts per collection/congress:";
for col in "${COL_ARR[@]}"; do
  for cong in "${CONG_ARR[@]}"; do
    dir="$OUT/$col/$cong"
    if [[ -d "$dir" ]]; then
      cnt=$(find "$dir" -maxdepth 1 -type f -name "*.xml" | wc -l)
      echo "  $col/$cong: $cnt files in $dir"
    else
      echo "  $col/$cong: no directory found"
    fi
  done
done

echo
echo "Done. To actually fetch files, re-run without --dry-run on a machine with network access."
