# Repository Rules

1. **Configuration-first**: All credentials and tuning parameters must be read from environment variables or configuration files, never hard-coded.
2. **Deterministic data pulls**: Pagination state (offset, page number) must be explicit to ensure resumable ingestion without duplication.
3. **Documentation requirement**: Every new workflow or CLI entry must be described in the docs folder so agents and humans can reuse it.
4. **Safety**: Avoid destructive operations in automation scripts; default to read-only until explicitly enabled by flags.
5. **Compliance**: Honor published API rate limits by adding sleeps or throttling where necessary.
