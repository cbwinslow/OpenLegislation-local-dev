#!/usr/bin/env python3
"""Generate cross references between SqlTable enum entries and Flyway migration files.

This utility inspects the Java enum that enumerates every SQL table referenced by the
application (``SqlTable``) and the Flyway migration scripts under
``src/main/resources/sql/migrations``.  It produces a mapping report that highlights
which migration file defines each table and whether any tables are missing from either
side.

Examples
--------
Generate a JSON report::

    ./tools/generate_table_mapping.py --format json --output table_mapping.json

Emit a markdown summary to stdout::

    ./tools/generate_table_mapping.py --format markdown

The script is intentionally lightweight so that it can be run in automated checks or
manually by developers when adding new tables or migrations.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
SQLTABLE_PATH = REPO_ROOT / "src" / "main" / "java" / "gov" / "nysenate" / "openleg" / "common" / "dao" / "SqlTable.java"
MIGRATIONS_DIR = REPO_ROOT / "src" / "main" / "resources" / "sql" / "migrations"

SQLTABLE_PATTERN = re.compile(r"^\s*([A-Z0-9_]+)\s*\(\"([^\"]+)\"\)")
CREATE_TABLE_PATTERN = re.compile(
    r"CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+(?:[a-z0-9_]+\.)?\"?([a-z0-9_]+)\"?",
    re.IGNORECASE,
)


@dataclass
class SqlTableEntry:
    """Represents a single enum member from ``SqlTable``."""

    enum_name: str
    table_name: str
    source_line: int


@dataclass
class MigrationTable:
    """Represents a table definition found within a migration script."""

    table_name: str
    migration_file: Path
    line_number: int


def parse_sqltable(java_path: Path) -> List[SqlTableEntry]:
    """Extract all enum members from ``SqlTable.java``."""

    entries: List[SqlTableEntry] = []
    with java_path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            match = SQLTABLE_PATTERN.search(line)
            if match:
                enum_name, table_name = match.groups()
                entries.append(SqlTableEntry(enum_name=enum_name, table_name=table_name, source_line=idx))
    return entries


def parse_migrations(migrations_dir: Path) -> List[MigrationTable]:
    """Scan the Flyway migrations for CREATE TABLE statements."""

    tables: List[MigrationTable] = []
    for path in sorted(migrations_dir.glob("*.sql")):
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for idx, line in enumerate(handle, start=1):
                match = CREATE_TABLE_PATTERN.search(line)
                if match:
                    table = match.group(1)
                    tables.append(MigrationTable(table_name=table, migration_file=path.relative_to(REPO_ROOT), line_number=idx))
    return tables


def build_mapping(sqltables: Sequence[SqlTableEntry], migrations: Sequence[MigrationTable]) -> Dict[str, dict]:
    """Cross-reference SqlTable entries with migration definitions."""

    migrations_by_table: Dict[str, List[MigrationTable]] = {}
    for table in migrations:
        migrations_by_table.setdefault(table.table_name, []).append(table)

    mapping: Dict[str, dict] = {}
    for entry in sqltables:
        mapping.setdefault(entry.table_name, {
            "enum_names": [],
            "migrations": migrations_by_table.get(entry.table_name, []),
        })
        mapping[entry.table_name]["enum_names"].append(entry)

    for table_name, mig_entries in migrations_by_table.items():
        mapping.setdefault(table_name, {
            "enum_names": [],
            "migrations": mig_entries,
        })

    return mapping


def serialise_mapping_to_json(mapping: Dict[str, dict]) -> str:
    """Serialise the mapping dictionary into JSON."""

    serialisable = {}
    for table_name, payload in mapping.items():
        serialisable[table_name] = {
            "enum_names": [entry.enum_name for entry in payload["enum_names"]],
            "enum_source_lines": [entry.source_line for entry in payload["enum_names"]],
            "migrations": [
                {
                    "file": str(migration.migration_file),
                    "line": migration.line_number,
                }
                for migration in payload["migrations"]
            ],
        }
    return json.dumps(serialisable, indent=2, sort_keys=True)


def serialise_mapping_to_markdown(mapping: Dict[str, dict]) -> str:
    """Render the mapping information as a markdown table."""

    header = "| Table | SqlTable enums | Migration definitions |\n| --- | --- | --- |"
    rows: List[str] = [header]
    for table_name in sorted(mapping.keys()):
        payload = mapping[table_name]
        enum_repr = "<br>".join(
            f"{entry.enum_name} (line {entry.source_line})" for entry in sorted(payload["enum_names"], key=lambda e: e.enum_name)
        ) or "—"
        migration_repr = "<br>".join(
            f"{migration.migration_file} (line {migration.line_number})" for migration in payload["migrations"]
        ) or "—"
        rows.append(f"| `{table_name}` | {enum_repr} | {migration_repr} |")
    return "\n".join(rows)


def summarise_gaps(mapping: Dict[str, dict]) -> Tuple[Set[str], Set[str]]:
    """Identify tables missing from either the Java enum or the migrations."""

    missing_enum: Set[str] = set()
    missing_migration: Set[str] = set()
    for table_name, payload in mapping.items():
        if not payload["enum_names"]:
            missing_enum.add(table_name)
        if not payload["migrations"]:
            missing_migration.add(table_name)
    return missing_enum, missing_migration


def write_output(content: str, output_path: Optional[Path]) -> None:
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
    else:
        print(content)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate SqlTable to migration mapping report")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format")
    parser.add_argument("--output", type=Path, default=None, help="Optional output file path")
    parser.add_argument("--show-summary", action="store_true", help="Print summary of missing entries to stderr")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    sqltable_entries = parse_sqltable(SQLTABLE_PATH)
    migration_tables = parse_migrations(MIGRATIONS_DIR)
    mapping = build_mapping(sqltable_entries, migration_tables)

    if args.format == "json":
        output = serialise_mapping_to_json(mapping)
    else:
        output = serialise_mapping_to_markdown(mapping)

    write_output(output, args.output)

    if args.show_summary:
        missing_enum, missing_migration = summarise_gaps(mapping)
        if missing_enum:
            print("Tables defined in migrations but missing from SqlTable:", ", ".join(sorted(missing_enum)), file=sys.stderr)
        if missing_migration:
            print("Tables referenced in SqlTable but missing migrations:", ", ".join(sorted(missing_migration)), file=sys.stderr)
        if not missing_enum and not missing_migration:
            print("No discrepancies detected between SqlTable and migrations.", file=sys.stderr)


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
