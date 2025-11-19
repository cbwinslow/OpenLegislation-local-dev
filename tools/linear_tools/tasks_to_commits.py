#!/usr/bin/env python3
"""
tasks_to_commits.py

Convert `docs/tasks.md` into a CSV suitable for the batch importer.

Output: tools/tasks_as_commits.csv (columns: hash,author,date,subject)

This script extracts bullet/list items and headings as task subjects. Each
row uses a synthetic UUID as `hash`, author `tasks.md import`, and ISO date.
"""
import csv
import datetime
import re
import sys
import uuid
from pathlib import Path


def parse_tasks(md_path):
    tasks = []
    cur_section = None
    bullet_re = re.compile(r"^\s*[-*+]\s+(.*)")
    numbered_re = re.compile(r"^\s*\d+[.)]\s+(.*)")
    header_re = re.compile(r"^#{1,6}\s+(.*)")

    with open(md_path, 'r', encoding='utf-8') as fh:
        for line in fh:
            line = line.rstrip('\n')
            if not line.strip():
                continue
            m = header_re.match(line)
            if m:
                cur_section = m.group(1).strip()
                continue
            m = bullet_re.match(line) or numbered_re.match(line)
            if m:
                text = m.group(1).strip()
                if cur_section:
                    subject = f"{cur_section}: {text}"
                else:
                    subject = text
                tasks.append(subject)
            else:
                # detect plausible short lines (titles) as tasks
                if len(line.strip()) < 120 and not line.startswith('>'):
                    # ignore code blocks and long paragraphs
                    # treat as potential task if it looks like a title
                    if any(ch.isalnum() for ch in line):
                        tasks.append(line.strip())
    return tasks


def write_csv(tasks, out_path):
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    out_dir = Path(out_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=["hash", "author", "date", "subject"])
        writer.writeheader()
        for t in tasks:
            row = {
                'hash': uuid.uuid4().hex,
                'author': 'tasks.md import',
                'date': now,
                'subject': t
            }
            writer.writerow(row)


def main():
    md = Path('docs/tasks.md')
    if not md.exists():
        print('docs/tasks.md not found; aborting')
        return 2
    tasks = parse_tasks(md)
    if not tasks:
        print('No tasks extracted from docs/tasks.md')
        return 3
    out_csv = Path('tools') / 'tasks_as_commits.csv'
    write_csv(tasks, out_csv)
    print(f'Wrote {len(tasks)} tasks -> {out_csv}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
