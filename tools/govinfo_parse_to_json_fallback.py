#!/usr/bin/env python3
"""Lightweight fallback parser for govinfo XML files.

This script requires only Python stdlib and extracts a minimal set of fields
usable for demonstrating ingestion: title, sponsors, actions, and raw XML.

Usage: python3 tools/govinfo_parse_to_json_fallback.py /path/to/samplesdir > out.jsonl
"""
import sys
import os
import re
import json
import base64


def strip_tags(s):
    return re.sub(r'<[^>]+>', '', s).strip()


def first_match(text, patterns):
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE | re.DOTALL)
        if m:
            return strip_tags(m.group(1))
    return None


def extract_sponsors(text):
    sponsors = []
    # try common sponsor containers
    for p in [r'<sponsor[^>]*>(.*?)</sponsor>', r'<sponsor-name[^>]*>(.*?)</sponsor-name>', r'<sponsors[^>]*>(.*?)</sponsors>']:
        for m in re.finditer(p, text, flags=re.IGNORECASE | re.DOTALL):
            inner = m.group(1)
            # try to find <name> inside
            name = None
            mm = re.search(r'<name[^>]*>(.*?)</name>', inner, flags=re.IGNORECASE | re.DOTALL)
            if mm:
                name = strip_tags(mm.group(1))
            else:
                # fallback to inner text
                name = strip_tags(inner)
            if name:
                if name not in [s['name'] for s in sponsors]:
                    sponsors.append({'name': name})
    return sponsors


def extract_actions(text):
    acts = []
    for m in re.finditer(r'<action([^>]*)>(.*?)</action>', text, flags=re.IGNORECASE | re.DOTALL):
        attr = m.group(1)
        inner = m.group(2)
        # date attribute
        date_m = re.search(r'date\s*=\s*"([^"]+)"', attr)
        date = date_m.group(1) if date_m else None
        # look for <type> or <text>
        summary = first_match(inner, [r'<type[^>]*>(.*?)</type>', r'<text[^>]*>(.*?)</text>'])
        if not summary:
            summary = strip_tags(inner)
        if summary and len(summary) > 300:
            summary = summary[:300].rsplit(' ', 1)[0] + '...'
        acts.append({'date': date, 'description': summary})
    return acts


def parse_file(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    try:
        text = raw.decode('utf-8')
    except Exception:
        try:
            text = raw.decode('latin-1')
        except Exception:
            text = raw.decode('utf-8', errors='ignore')

    basename = os.path.basename(path)
    name_noext = basename[:-4]

    title = first_match(text, [r'<official-title[^>]*>(.*?)</official-title>', r'<officialTitle[^>]*>(.*?)</officialTitle>', r'<title[^>]*>(.*?)</title>'])
    short_title = first_match(text, [r'<short-title[^>]*>(.*?)</short-title>', r'<shortTitle[^>]*>(.*?)</shortTitle>'])
    introduced = first_match(text, [r'<introduced-date[^>]*>(.*?)</introduced-date>', r'<introducedDate[^>]*>(.*?)</introducedDate>', r'<introduced[^>]*>(.*?)</introduced>'])

    sponsors = extract_sponsors(text)
    actions = extract_actions(text)

    record = {
        'source_domain': 'govinfo.gov',
        'source_collection': 'BILLS',
        'source_congress': None,
        'source_session': None,
        'source_filename': basename,
        'source_url': f'https://www.govinfo.gov/content/pkg/{name_noext}/xml/{basename}',
        'doc_type': None,
        'published_at': introduced,
        'received_at': None,
        'canonical_id': name_noext,
        'title': title or short_title,
        'sponsors': sponsors or None,
        'actions': actions or None,
        'text_versions': None,
        'raw_xml_base64': base64.b64encode(raw).decode('ascii'),
    }
    record['parsed_json'] = {'title': record['title'], 'sponsors': record['sponsors'], 'actions': record['actions']}
    return record


def main():
    if len(sys.argv) < 2:
        print('Usage: govinfo_parse_to_json_fallback.py /path/to/samplesdir', file=sys.stderr)
        sys.exit(2)
    in_dir = sys.argv[1]
    files = sorted([f for f in os.listdir(in_dir) if f.lower().endswith('.xml')])
    for fn in files:
        path = os.path.join(in_dir, fn)
        try:
            rec = parse_file(path)
            print(json.dumps(rec, ensure_ascii=False))
        except BrokenPipeError:
            try:
                sys.stdout.close()
            except Exception:
                pass
            sys.exit(0)


if __name__ == '__main__':
    main()
