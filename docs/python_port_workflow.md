# Python Port and Data Ingestion Workflow

This document describes a pragmatic path toward generating Python equivalents
for the existing Java domain model, aligning them with the Flyway-maintained SQL
schema, and ingesting XML data from Congress.gov and GovInfo API surfaces.

## Overview

1. **Blueprint extraction** – `tools/generate_python_blueprints.py` parses every
   Java source file and records the discovered classes, enums, fields, and
   method signatures.  The result is persisted to
   `python_port/blueprints.json`.
2. **Schema extraction** – `tools/extract_sql_schema.py` aggregates the DDL from
   the Flyway migrations into a structured summary that includes table columns,
   foreign keys, views, triggers, and indexes.  The summary is written to
   `python_port/sql_schema.json`.
3. **Mapping** – `tools/map_python_to_sql.py` performs a heuristic join between
   blueprint names and SQL objects to generate an initial field-to-column map in
   `python_port/sql_mapping.json`.
4. **Runtime materialisation** – `python_port.builders` exposes helpers that can
   convert a blueprint into a concrete `dataclass` or `Enum` instance at runtime
   so downstream ETL steps can instantiate Python-native models without checking
   in thousands of generated files.
5. **Ingestion** – `tools/bulkdata_pipeline.py` and the new
   `tools/govinfo_ingest.py` module orchestrate bulk and parameterised pulls from
   Congress.gov and GovInfo respectively, emitting XML payloads that can be
   deserialised into the generated Python dataclasses before being written into
   PostgreSQL tables via the SQL mapping metadata.

## Usage

```bash
# 1) Create Python blueprints for the Java domain model
python tools/generate_python_blueprints.py

# 2) Extract SQL schema metadata
python tools/extract_sql_schema.py

# 3) Join the two worlds together
python tools/map_python_to_sql.py

# 4) Materialise a dataclass for a specific Java type
python - <<'PY'
from pathlib import Path
import json
from python_port import build_class, ClassBlueprint

payload = json.loads(Path('python_port/blueprints.json').read_text())
blueprint_data = next(cls for cls in payload['classes'] if cls['qualified_name'] == 'gov.nysenate.openleg.legislation.bill.Bill')
cls = build_class(ClassBlueprint(**blueprint_data))
print(cls)
PY
```

## Extending the Mapping

The heuristic snake_case matching in `tools/map_python_to_sql.py` is meant to
seed the port.  For complex objects you can edit the generated JSON files or
extend the script with project-specific naming rules (for example reading the
`SqlTable` enum or DAO metadata).

## Database Creation

The Flyway migrations in `src/main/resources/sql` remain the source of truth for
schema creation.  The extracted metadata intentionally retains the original SQL
statements so they can be replayed or transformed into dialect-specific DDL as
needed.

## GovInfo API Ingestion

`tools/govinfo_ingest.py` accepts collection identifiers and date filters to
stream XML payloads either by calling the REST API or by downloading bulk ZIP
archives.  The ingested files can be parsed into the Python dataclasses to build
SQL insert batches that align with the generated mapping metadata.
