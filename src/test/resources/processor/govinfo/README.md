GovInfo test fixtures

This directory contains sample GovInfo bulk XML files used for unit testing and XPath mapping.

To regenerate samples locally, run the downloader script from the project root:

```bash
# download samples for selected collections
./tools/download_govinfo_samples.sh --out /tmp/govinfo_samples --collections BILLS,BILLSTATUS,BILLSUM --max 365

# copy desired samples into this test directory
mkdir -p src/test/resources/processor/govinfo/BILLS/119
cp /tmp/govinfo_samples/BILLS/*.xml src/test/resources/processor/govinfo/BILLS/119/
```

To parse samples into JSONL for inspection:

```bash
python3 tools/govinfo_parse_to_json.py /tmp/govinfo_samples/BILLS > /tmp/govinfo_samples.bills.jsonl
head -n 5 /tmp/govinfo_samples.bills.jsonl
```

Use these fixtures when writing unit tests under `src/test/java/.../processor/govinfo`.
