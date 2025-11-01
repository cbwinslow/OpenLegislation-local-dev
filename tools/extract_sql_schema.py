#!/usr/bin/env python3
"""Extract table, view, trigger, and index definitions from Flyway migrations."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

CREATE_PATTERN = re.compile(
    r'CREATE\s+(TABLE|VIEW|INDEX|TRIGGER|FUNCTION)\s+(IF\s+NOT\s+EXISTS\s+)?(?P<name>[\w\."]+)',
    re.IGNORECASE,
)
FOREIGN_KEY_PATTERN = re.compile(r"FOREIGN\s+KEY\s*\((?P<columns>[^\)]+)\)\s*REFERENCES\s+(?P<ref>[^\s\(]+)", re.IGNORECASE)


class SchemaCollector:
    def __init__(self) -> None:
        self.tables: Dict[str, Dict[str, List[str]]] = {}
        self.views: Dict[str, str] = {}
        self.indexes: Dict[str, str] = {}
        self.triggers: Dict[str, str] = {}
        self.functions: Dict[str, str] = {}

    def add_statement(self, object_type: str, name: str, statement: str) -> None:
        key = name.strip('"')
        if object_type == "TABLE":
            foreign_keys = [match.group("ref") for match in FOREIGN_KEY_PATTERN.finditer(statement)]
            columns = []
            for line in statement.splitlines():
                line = line.strip()
                if not line or line.upper().startswith("PRIMARY KEY"):
                    continue
                if "(" not in line or line.upper().startswith("FOREIGN KEY"):
                    continue
                column_name = line.split(" ", 1)[0].strip('"')
                columns.append(column_name)
            self.tables[key] = {
                "columns": columns,
                "foreign_keys": foreign_keys,
            }
        elif object_type == "VIEW":
            self.views[key] = statement
        elif object_type == "INDEX":
            self.indexes[key] = statement
        elif object_type == "TRIGGER":
            self.triggers[key] = statement
        elif object_type == "FUNCTION":
            self.functions[key] = statement

    def to_dict(self) -> Dict[str, Dict[str, List[str]]]:
        return {
            "tables": self.tables,
            "views": self.views,
            "indexes": self.indexes,
            "triggers": self.triggers,
            "functions": self.functions,
        }


def extract_schema(sql_root: Path) -> Dict[str, Dict[str, List[str]]]:
    collector = SchemaCollector()
    for sql_file in sql_root.rglob("*.sql"):
        statements = sql_file.read_text(encoding="utf-8", errors="ignore").split(";")
        for statement in statements:
            match = CREATE_PATTERN.search(statement)
            if not match:
                continue
            object_type = match.group(1).upper()
            name = match.group("name")
            collector.add_statement(object_type, name, statement.strip())
    return collector.to_dict()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sql-root", type=Path, default=Path("src/main/resources/sql"), help="Directory with Flyway migrations")
    parser.add_argument("--output", type=Path, default=Path("python_port/sql_schema.json"), help="Destination JSON path")
    args = parser.parse_args()

    schema = extract_schema(args.sql_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(schema, indent=2), encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    main()
