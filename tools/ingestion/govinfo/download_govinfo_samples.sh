#!/usr/bin/env bash
set -euo pipefail

# Download GovInfo bulk XML samples for specified collections.
# Usage:
#   ./tools/download_govinfo_samples.sh --out /tmp/govinfo_samples --collections BILLS,BILLSTATUS,BILLSUM --max 365
# The script uses only curl/grep/sed and should work on most Linux/macOS dev machines.

OUT="/tmp/govinfo_samples"
COLS="BILLS,BILLSTATUS,BILLSUM"
MAX=365
UA='OpenLegislationFetcher/1.0 (+https://github.com/nysenate/OpenLegislation)'
BASE='https://www.govinfo.gov/bulkdata'

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT="$2"; shift 2 ;;
    --collections) COLS="$2"; shift 2 ;;
    --max) MAX="$2"; shift 2 ;;
    -h|--help) echo "Usage: $0 [--out DIR] [--collections C1,C2] [--max N]"; exit 0 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

mkdir -p "$OUT"
IFS=',' read -r -a COLLECTION_ARR <<< "$COLS"

download_file() {
  local url="$1" outpath="$2"
  if [[ -f "$outpath" ]]; then
    echo "Skipping existing: $(basename "$outpath")"
    return 0
  fi
  echo "Downloading $url -> $outpath"
  curl -sS -A "$UA" "$url" -o "$outpath" || { echo "Failed: $url"; return 1; }
}

for col in "${COLLECTION_ARR[@]}"; do
  col_dir="$OUT/$col"
  mkdir -p "$col_dir"
  echo "\n=== Collection: $col"
  listing_url="$BASE/$col/"
  listing=$(curl -sS -A "$UA" "$listing_url" || true)
  # collect links to .xml files
  mapfile -t links < <(echo "$listing" | grep -oE 'href="[^"]+\.xml"' | sed -E 's/href="([^\"]+)"/\1/' | while read -r l; do
    if [[ "$l" =~ ^https?:// ]]; then
      echo "$l"
    elif [[ "$l" =~ ^/ ]]; then
      echo "https://www.govinfo.gov${l}"
    else
      # relative path
      echo "$listing_url$l"
    fi
  done)

  echo "  found ${#links[@]} xml links (will download up to $MAX)"
  c=0
  for l in "${links[@]}"; do
    [[ $c -ge $MAX ]] && break
    basename=$(basename "${l%%\?*}")
    outpath="$col_dir/$basename"
    if download_file "$l" "$outpath"; then
      c=$((c+1))
    fi
    sleep 0.4
  done

  # try resources dir for schema/docs
  res_url="$listing_url/resources/"
  res_listing=$(curl -sS -A "$UA" "$res_url" || true)
  if [[ -n "$res_listing" ]]; then
    echo "  found resources for $col"
    mapfile -t resfiles < <(echo "$res_listing" | grep -oE 'href="[^"]+"' | sed -E 's/href="([^\"]+)"/\1/' | grep -iE '\.(xsd|xslt|xsl|md|txt)$' || true)
    for rf in "${resfiles[@]}"; do
      if [[ "$rf" =~ ^https?:// ]]; then
        furl="$rf"
      elif [[ "$rf" =~ ^/ ]]; then
        furl="https://www.govinfo.gov${rf}"
      else
        furl="$res_url$rf"
      fi
      download_file "$furl" "$col_dir/$(basename "$rf")" || true
      sleep 0.2
    done
  fi
done

echo "\nFinished downloading samples to: $OUT"
