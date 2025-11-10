#!/usr/bin/env bash
set -euo pipefail

# govinfo_enumerate.sh
# Enumerate govinfo bulkdata collections, congresses, subdirectories and sample xml counts.
# Uses only curl/grep/sed/awk so it works in restricted environments.
#
# Usage:
#   ./tools/govinfo_enumerate.sh --collections BILLS,BILLSTATUS --max-subdirs 5 --max-files 10 --out /tmp/govinfo_enum.jsonl

BASE='https://www.govinfo.gov/bulkdata'
UA='OpenLegislationEnumerator/1.0 (+https://github.com/nysenate/OpenLegislation)'
#!/usr/bin/env bash
set -euo pipefail

# govinfo_enumerate.sh - a simple govinfo bulkdata enumerator
# Produces JSONL lines: {collection, congress, subdir, sample_count, url}

BASE="https://www.govinfo.gov/bulkdata"
UA="OpenLegislationEnumerator/1.0 (+https://github.com/nysenate/OpenLegislation)"
COLS="BILLS,BILLSTATUS,BILLSUM"
MAX_SUB=10
MAX_FILES=20
OUT="/tmp/govinfo_enum.jsonl"

usage() {
  echo "Usage: $0 [--collections C1,C2] [--max-subdirs N] [--max-files M] [--out FILE]"
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --collections) COLS="$2"; shift 2 ;;
    --max-subdirs) MAX_SUB="$2"; shift 2 ;;
    --max-files) MAX_FILES="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

rm -f "$OUT"
IFS=',' read -r -a C_ARR <<< "$COLS"

jsesc() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e ':a;N;$!ba;s/\n/\\n/g' ; }

echo "Enumerating collections: ${C_ARR[*]} -> output: $OUT"

for col in "${C_ARR[@]}"; do
  echo "{\"collection\": \"$col\", \"status\": \"scanning\"}" >> "$OUT"
  col_url="$BASE/$col/"
  listing=$(curl -sS -A "$UA" "$col_url" || true)

  mapfile -t congs < <(echo "$listing" | grep -oE "/$col/[0-9]{3}/" | sed -E "s|.*/$col/||; s|/||g" | sort -u)
  if [[ ${#congs[@]} -eq 0 ]]; then
    mapfile -t congs < <(echo "$listing" | grep -oE '[0-9]{3}' | sort -u)
  fi
  if [[ ${#congs[@]} -eq 0 ]]; then
    echo "{\"collection\": \"$col\", \"error\": \"no congress dirs found\"}" >> "$OUT"
    continue
  fi

  ccount=0
  for cong in "${congs[@]}"; do
    [[ $ccount -ge $MAX_SUB ]] && break
    ccount=$((ccount+1))
    cong_url="$col_url$cong/"
    sublist=$(curl -sS -A "$UA" "$cong_url" || true)

    mapfile -t subs < <(echo "$sublist" | grep -oE "/bulkdata/$col/$cong/[^/]+/" | sed -E 's|.*/$cong/||; s|/$||' | sort -u)
    if [[ ${#subs[@]} -eq 0 ]]; then
      mapfile -t subs < <(echo "$sublist" | grep -oE 'href="[^"]+/"' | sed -E 's/href="([^"]+)"/\1/' | sed -E 's|/$||' | awk -F'/' '{print $NF}' | sort -u)
      # filter out noisy tokens
      filtered=()
      for s in "${subs[@]}"; do
        case "$s" in
          about|app|browse|resources|search|index.html) continue ;;
          *) filtered+=("$s") ;;
        esac
      done
      subs=("${filtered[@]}")
    fi
    if [[ ${#subs[@]} -eq 0 ]]; then
      subs=(".")
    fi

    scount=0
    for sub in "${subs[@]}"; do
      [[ $scount -ge $MAX_SUB ]] && break
      scount=$((scount+1))
      if [[ "$sub" == "." ]]; then
        sub_url="$cong_url"
        sub_label='root'
      else
        sub_url="$cong_url$sub/"
        sub_label="$sub"
      fi

      page=$(curl -sS -A "$UA" "$sub_url" || true)
      raw_cnt=$(echo "$page" | grep -oE '\.xml' | wc -l | tr -d ' ' || true)
      if [[ -z "$raw_cnt" ]]; then raw_cnt=0; fi
      cnt=$raw_cnt
      if [[ "$cnt" -gt $MAX_FILES ]]; then
        cnt=$MAX_FILES
      fi

      esc_col=$(jsesc "$col")
      esc_cong=$(jsesc "$cong")
      esc_sub=$(jsesc "$sub_label")
      esc_url=$(jsesc "$sub_url")
      echo "{\"collection\": \"$esc_col\", \"congress\": \"$esc_cong\", \"subdir\": \"$esc_sub\", \"sample_count\": $cnt, \"url\": \"$esc_url\"}" >> "$OUT"
    done
  done
  echo "{\"collection\": \"$col\", \"status\": \"done\"}" >> "$OUT"
done

echo "Finished. Summary written to $OUT"
#   ./tools/govinfo_enumerate.sh --collections BILLS,BILLSTATUS --max-subdirs 5 --max-files 10 --out /tmp/govinfo_enum.jsonl
