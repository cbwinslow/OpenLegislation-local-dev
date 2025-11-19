#!/usr/bin/env python3
"""
linear_import_batches.py

Simple helper to split a commits CSV into incremental batch CSVs suitable for review or import.

Usage:
  python3 tools/linear_import_batches.py --csv tools/linear_commits_since_2024.csv --out-dir tools/batches --batch-size 100 --dry-run

By default this script only performs local file operations. If you supply --api-key it will attempt
to create issues via the Linear API (not implemented here). This keeps the script safe for review.
"""
import argparse
import csv
import math
import os
from pathlib import Path


def read_commits(csv_path):
    commits = []
    with open(csv_path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            commits.append(row)
    return commits


def write_batch(batch, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=["hash", "author", "date", "subject"])
        writer.writeheader()
        for r in batch:
            writer.writerow({k: r.get(k, '') for k in writer.fieldnames})


def split_into_batches(commits, batch_size):
    batches = []
    total = len(commits)
    num = max(1, math.ceil(total / batch_size))
    for i in range(num):
        start = i * batch_size
        end = start + batch_size
        batches.append(commits[start:end])
    return batches


def main():
    p = argparse.ArgumentParser(description='Split commits CSV into incremental batch CSVs')
    p.add_argument('--csv', required=True, help='Path to commits CSV (hash|author|date|subject)')
    p.add_argument('--out-dir', default='tools/batches', help='Directory to write batch CSVs')
    p.add_argument('--batch-size', type=int, default=100, help='Number of items per batch')
    p.add_argument('--dry-run', action='store_true', help='Only write files and show summary')
    args = p.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f'Error: commits CSV not found: {csv_path}')
        return 2

    commits = read_commits(csv_path)
    print(f'Loaded {len(commits)} commits from {csv_path}')
    batches = split_into_batches(commits, args.batch_size)
    print(f'Will write {len(batches)} batch files (batch size {args.batch_size}) to {args.out_dir}')

    for idx, batch in enumerate(batches, start=1):
        out_file = Path(args.out_dir) / f'batch_{idx:03d}.csv'
        write_batch(batch, str(out_file))
        print(f'Wrote {len(batch)} items -> {out_file}')

    print('Done. Review the batch CSVs in the output directory before performing any API imports.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
