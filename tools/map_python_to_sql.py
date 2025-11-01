#!/usr/bin/env python3
"""Link generated Python blueprints to extracted SQL schema objects."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

from python_port.blueprints import ClassBlueprint, FieldBlueprint


def _load_classes(path: Path) -> List[ClassBlueprint]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [ClassBlueprint(**item) for item in payload.get("classes", [])]


def _load_schema(path: Path) -> Dict[str, Dict[str, List[str]]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _camel_to_snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def build_mapping(classes: List[ClassBlueprint], schema: Dict[str, Dict[str, List[str]]]) -> Dict[str, Dict[str, str]]:
    mapping: Dict[str, Dict[str, str]] = {}
    tables = schema.get("tables", {})
    for cls in classes:
        table_name = None
        snake_name = _camel_to_snake(cls.name)
        candidate_names = [snake_name, f"{snake_name}s", f"{snake_name}_table"]
        for candidate in candidate_names:
            if candidate in tables:
                table_name = candidate
                break
        if not table_name:
            continue
        column_map = {}
        columns = tables[table_name]["columns"]
        for field in cls.fields:
            field_snake = _camel_to_snake(field.name)
            for column in columns:
                if column == field_snake or column == field.name:
                    column_map[field.name] = column
                    break
        mapping[cls.qualified_name] = {"table": table_name, "fields": column_map}
    return mapping


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blueprints", type=Path, default=Path("python_port/blueprints.json"), help="Path to class blueprint JSON")
    parser.add_argument("--schema", type=Path, default=Path("python_port/sql_schema.json"), help="Path to extracted SQL schema JSON")
    parser.add_argument("--output", type=Path, default=Path("python_port/sql_mapping.json"), help="Destination mapping JSON")
    args = parser.parse_args()

    classes = _load_classes(args.blueprints)
    schema = _load_schema(args.schema)
    mapping = build_mapping(classes, schema)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(mapping, indent=2), encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    main()
