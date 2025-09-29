#!/usr/bin/env python3
"""
linear_api_import.py

Create Linear issues from CSV batches produced by linear_import_batches.py.

Usage:
    python3 tools/linear_api_import.py --token <TOKEN> \
        --batches tools/batches --repo-url <repo_url> \
        --team-key cloudcurio --project-name "OpenLegislation - Data Review"

This script will:
 - discover the Linear team and project by key/name
 - create one issue per commit row in each batch CSV
 - write a run log to tools/linear_import_run_<date>.json

Notes:
 - By default the created issues are left open. Each issue body contains
     "Status: completed" to mark them historically completed.
 - Use with caution: this will perform remote writes. You provided the
     token and the script will send it in the Authorization header.
"""
import argparse
import csv
import datetime
import json
import sys
import time
from pathlib import Path

import urllib.request


GRAPHQL_URL = 'https://api.linear.app/graphql'


def gql_query(token, query, variables=None):
    payload = {'query': query}
    if variables is not None:
        payload['variables'] = variables
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=data,
        headers={
            'Content-Type': 'application/json',
            # Linear expects the raw API key in the Authorization header
            'Authorization': token
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as he:
        # Try to read and decode the response body for GraphQL error details
        try:
            body = he.read().decode('utf-8')
            try:
                return json.loads(body)
            except Exception:
                return {'error': f'HTTP {he.code}: {he.reason}', 'body': body}
        except Exception:
            return {'error': f'HTTP {he.code}: {he.reason}', 'body': None}


def find_team(token, team_key):
    query = (
        'query { teams { nodes { id key name } } }'
    )
    resp = gql_query(token, query)
    nodes = resp.get('data', {}).get('teams', {}).get('nodes', [])
    for n in nodes:
        if n.get('key') == team_key or n.get('name') == team_key:
            return n
    # fallback: return first team with matching substring
    for n in nodes:
        name = n.get('name', '')
        key = n.get('key', '')
        if team_key.lower() in (name.lower() + key.lower()):
            return n
    return None


def find_project(token, project_name):
    query = (
        'query Projects($name: String) '
        '{ projects(filter: {name: $name}) { nodes { id name } } }'
    )
    resp = gql_query(token, query, {'name': project_name})
    nodes = resp.get('data', {}).get('projects', {}).get('nodes', [])
    if nodes:
        return nodes[0]
    # fallback: try searching all projects for substring
    query2 = '''query { projects { nodes { id name } } }'''
    resp2 = gql_query(token, query2)
    for p in resp2.get('data', {}).get('projects', {}).get('nodes', []):
        if project_name.lower() in p.get('name', '').lower():
            return p
    return None


def create_issue(token, team_id, project_id, title, description):
    # The GraphQL schema for issueCreate returns an IssuePayload with
    # { success, issue }. Previously we requested a non-existent `errors`
    # field which caused validation errors. Keep the selection minimal here
    # and handle top-level GraphQL errors where needed.
    mutation = '''mutation IssueCreate($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue {
      id
      identifier
      url
    }
  }
}'''

    variables = {
        'input': {
            'title': title,
            'description': description,
            'teamId': team_id,
            'projectId': project_id
        }
    }

    resp = gql_query(token, mutation, variables)
    return resp


def read_commits_from_csv(path):
    rows = []
    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            rows.append(r)
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--token', required=True, help='Linear API token')
    p.add_argument(
        '--batches', required=True,
        help='Directory containing batch_###.csv files'
    )
    p.add_argument(
        '--repo-url',
        default=(
            'https://github.com/cbwinslow/'
            'OpenLegislation-local-dev'
        ),
        help='Repo URL to link commits'
    )
    p.add_argument(
        '--team-key', default='cloudcurio', help='Linear team key or name'
    )
    p.add_argument(
        '--team-id',
        default=None,
        help='Linear team id (UUID). If provided, discovery is skipped.'
    )
    p.add_argument(
        '--project-name',
        default='OpenLegislation - Data Review',
        help='Linear project name'
    )
    p.add_argument(
        '--project-id',
        default=None,
        help='Linear project id (UUID). If provided, discovery is skipped.'
    )
    p.add_argument(
        '--batch-delay', type=float, default=1.0,
        help='Seconds to wait between issues to avoid bursts'
    )
    args = p.parse_args()

    token = args.token
    batches_dir = Path(args.batches)
    if not batches_dir.exists():
        print('Batches directory not found:', batches_dir)
        return 2

    # If the caller provided explicit team/project ids, use them and
    # skip discovery
    if args.team_id:
        team_id = args.team_id
        print('Using provided team id:', team_id)
    else:
        print('Discovering team...')
        team = find_team(token, args.team_key)
        if not team:
            print('ERROR: team not found for key/name', args.team_key)
            return 3
        team_id = team['id']
        print('Using team:', team.get('name'), team.get('key'), team_id)

    if args.project_id:
        project_id = args.project_id
        print('Using provided project id:', project_id)
    else:
        print('Discovering project...')
        project = find_project(token, args.project_name)
        if not project:
            print('ERROR: project not found:', args.project_name)
            return 4
        project_id = project['id']
        print('Using project:', project.get('name'), project_id)

    run_log = {
        'created': [],
        'failed': [],
        'skipped': []
    }
    timestamp = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    out_path = Path('tools') / f'linear_import_run_{timestamp}.json'

    # load processed hashes from prior run logs and persistent file
    processed_file = Path('tools') / 'linear_import_processed.json'
    processed_hashes = set()
    if processed_file.exists():
        try:
            with open(processed_file, 'r', encoding='utf-8') as phf:
                arr = json.load(phf)
                processed_hashes.update(arr)
        except Exception:
            # ignore parse errors and continue
            pass

    # also scan previous run logs for created entries
    for pf in sorted(Path('tools').glob('linear_import_run_*.json')):
        try:
            with open(pf, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
                for c in data.get('created', []):
                    commit = c.get('commit') or {}
                    h = commit.get('hash')
                    if h:
                        processed_hashes.add(h)
        except Exception:
            continue

    batch_files = sorted(batches_dir.glob('batch_*.csv'))
    if not batch_files:
        print('No batch CSV files found in', batches_dir)
        return 5

    for bf in batch_files:
        print('Processing', bf)
        commits = read_commits_from_csv(bf)
        for c in commits:
            # build title and description
            subj = c.get('subject', '').strip()
            short_hash = c.get('hash', '')[:7]
            full_hash = c.get('hash', '')

            # idempotency: skip if this commit hash was already processed
            if full_hash and full_hash in processed_hashes:
                print('Skipping already-processed commit', full_hash)
                run_log['skipped'].append({'commit': c})
                continue
            title = subj if subj else f'Historical commit {short_hash}'
            commit_url = f"{args.repo_url}/commit/{c.get('hash', '')}"
            description = (
                'Historical import from repo commit\n\n'
                f'Commit: {c.get("hash", "")}\n'
                f'Author: {c.get("author", "")}\n'
                f'Date: {c.get("date", "")}\n'
                f'Subject: {subj}\n\n'
                f'Repo commit: {commit_url}\n\n'
                'Status: completed\n\n'
                f'Imported by automation on '
                f'{datetime.datetime.utcnow().isoformat()}Z\n'
            )

            try:
                resp = create_issue(
                    token, team_id, project_id, title[:250], description
                )
            except Exception as ex:
                print(
                    'Network/API error creating issue for',
                    c.get('hash'), '->', ex
                )
                run_log['failed'].append({'commit': c, 'error': str(ex)})
                time.sleep(args.batch_delay)
                continue

            # inspect response and handle GraphQL top-level errors
            if resp.get('errors'):
                # GraphQL validation / top-level errors
                print('GraphQL errors:', resp.get('errors'))
                run_log['failed'].append({'commit': c, 'response': resp})
            else:
                data = resp.get('data', {})
                ic = data.get('issueCreate') if data else None
                if ic and ic.get('success') and ic.get('issue'):
                    issue = ic['issue']
                    print('Created', issue.get('identifier'), issue.get('url'))
                    run_log['created'].append({'commit': c, 'issue': issue})
                    # mark as processed and persist
                    if full_hash:
                        processed_hashes.add(full_hash)
                        try:
                            with open(
                                processed_file, 'w', encoding='utf-8'
                            ) as phf:
                                json.dump(
                                    sorted(list(processed_hashes)), phf, indent=2
                                )
                        except Exception:
                            pass
                else:
                    print('Create failed for', c.get('hash'), 'response:')
                    print(resp)
                    run_log['failed'].append({'commit': c, 'response': resp})

            time.sleep(args.batch_delay)

        # write intermediate run log after each batch
        with open(out_path, 'w', encoding='utf-8') as fh:
            json.dump(run_log, fh, indent=2)

        # also persist processed hashes after each batch
        try:
            with open(
                processed_file, 'w', encoding='utf-8'
            ) as phf:
                json.dump(
                    sorted(list(processed_hashes)), phf, indent=2
                )
        except Exception:
            pass

    print('Import finished. Run log written to', out_path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
