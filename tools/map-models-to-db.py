#!/usr/bin/env python3
# Scans Java models for JPA annotations and compares to Flyway migrations.

import os
import re
from pathlib import Path


def find_java_models(root_dir):
    models = []
    for file in Path(root_dir).rglob("*.java"):
        if "legislation" in str(file.parent) and (
            "Entity" in file.read_text() or "@Entity" in file.read_text()
        ):
            models.append(str(file))
    return models


def extract_table_name(java_file):
    with open(java_file, "r") as f:
        content = f.read()
    match = re.search(r'@Table\(name\s*=\s*"(\w+)"\)', content)
    return match.group(1) if match else None


def find_migrations(root_dir):
    migrations = []
    for file in Path(root_dir).rglob("V*.sql"):
        migrations.append(str(file))
    return migrations


models_dir = "src/main/java/gov/nysenate/openleg/legislation"
migrations_dir = "src/main/resources/sql/migrations"

models = find_java_models(models_dir)
tables = {m: extract_table_name(m) for m in models if extract_table_name(m)}
migs = find_migrations(migrations_dir)

print("Mapped Tables from Java Models:")
for model, table in tables.items():
    print(f"- {model} → {table}")

print("\nExisting Migrations:")
for mig in migs:
    print(f"- {mig}")

unmapped = [
    table
    for table in tables.values()
    if not any(table.lower() in Path(m).stem.lower() for m in migs)
]
if unmapped:
    print(f"\nUnmapped Tables (Need New Migrations): {unmapped}")
    print(
        "Run: mvn flyway:migrate -Dflyway.locations=filesystem:src/main/resources/sql/migrations"
    )
else:
    print("\nAll models mapped! Ready for ingestion.")
