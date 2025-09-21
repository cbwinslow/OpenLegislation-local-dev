Fetch govinfo bulk data samples

Usage example:

```bash
# download a few sample files for BILLS 119th congress session 1
python3 tools/fetch_govinfo_bulk.py --collection BILLS --congress 119 --session 1 --out /tmp/govinfo_samples
```

The script will attempt to discover subdirectories (e.g., hr/, s/, hres/) and download a few XML files and any XSDs
found under `resources/` to help with schema discovery.

Place downloaded sample XMLs under `src/test/resources/processor/govinfo/119/` to write unit tests and map XPaths.
