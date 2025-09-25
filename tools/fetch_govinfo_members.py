#!/usr/bin/env python3

"""
Script to fetch and map bulk U.S. Congress members data from GovInfo.gov
Congressional Directory XML package.

Usage:
    python3 fetch_govinfo_members.py --congress 118 --output members_govinfo_118.json

Requirements:
    pip install requests

Bulk Data Docs: https://www.govinfo.gov/bulkdata/LIV/118/CONGRESSIONAL-DIRECTORY
Assumes latest XML ZIP; parses <member> tags.
"""

import argparse
import json
import os
import requests
import zipfile
import io
import xml.etree.ElementTree as ET
from typing import List, Dict

BASE_URL = "https://www.govinfo.gov/bulkdata"
OUTPUT_DIR = "output"

def download_bulk_zip(congress: int) -> str:
    """
    Download the Congressional Directory ZIP for the given congress.
    Returns path to extracted XML file.
    """
    # Construct URL for 1st session (adjust for 2nd if needed)
    session = "1stSession"
    filename = f"CD-{congress}thCongress-{session}.xml.zip"
    url = f"{BASE_URL}/LIV/{congress}/CONGRESSIONAL-DIRECTORY/{filename}"

    print(f"Downloading {url}...")
    response = requests.get(url)
    response.raise_for_status()

    # Extract in memory
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        xml_filename = z.namelist()[0]  # Assume single XML file
        xml_content = z.read(xml_filename).decode('utf-8')

    # Save extracted XML temporarily
    xml_path = f"/tmp/{xml_filename.replace('.zip', '')}"
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)

    print(f"Extracted to {xml_path}")
    return xml_path

def parse_members_xml(xml_path: str) -> List[Dict]:
    """
    Parse the XML file for <member> elements.
    GovInfo structure: <congressionalDirectory><member>...</member></congressionalDirectory>
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    members = []
    for member_elem in root.findall('.//member'):
        member_data = {
            'name': member_elem.find('name').text if member_elem.find('name') is not None else None,
            'title': member_elem.find('title').text if member_elem.find('title') is not None else None,
            'party': member_elem.find('party').text if member_elem.find('party') is not None else None,
            'state': member_elem.find('state').text if member_elem.find('state') is not None else None,
            'district': member_elem.find('district').text if member_elem.find('district') is not None else None,
            'chamber': member_elem.find('chamber').text if member_elem.find('chamber') is not None else None,
            'office': {
                'address': member_elem.find('.//address').text if member_elem.find('.//address') is not None else None,
                'phone': member_elem.find('.//phone').text if member_elem.find('.//phone') is not None else None,
                'fax': member_elem.find('.//fax').text if member_elem.find('.//fax') is not None else None,
                'email': member_elem.find('.//email').text if member_elem.find('.//email') is not None else None
            },
            'committees': [
                {
                    'name': comm.find('name').text if comm.find('name') is not None else None,
                    'role': comm.find('role').text if comm.find('role') is not None else None
                }
                for comm in member_elem.findall('.//committee')
            ],
            'biography': member_elem.find('biography').text if member_elem.find('biography') is not None else None
        }
        # Assign GUID: Use name + state as fallback if no id
        member_data['guid'] = member_elem.get('id') or f"{member_data['name']}_{member_data['state']}"
        members.append(member_data)

    return members

def map_to_entity(member_data: Dict) -> Dict:
    """
    Map parsed GovInfo data to project-like entity model (Member).
    Similar structure to congress.gov mapping.
    """
    entity = {
        'guid': member_data.get('guid'),
        'fullName': f"{member_data.get('title', '')} {member_data.get('name', '')}".strip(),
        'chamber': member_data.get('chamber'),
        'party': member_data.get('party'),
        'state': member_data.get('state'),
        'district': member_data.get('district', 'N/A'),
        'office': member_data.get('office', {}),
        'committees': member_data.get('committees', []),
        'biography': member_data.get('biography'),
        'source': 'govinfo.gov',
        'lastUpdated': 'From bulk download'  # No timestamp in XML
    }

    # Clean up None values
    return {k: v for k, v in entity.items() if v is not None and v != 'N/A'}

def main():
    parser = argparse.ArgumentParser(description="Fetch and map GovInfo bulk members data")
    parser.add_argument('--congress', type=int, default=118, help='Congress number (default: 118)')
    parser.add_argument('--output', default=None, help='Output JSON file (default: members_govinfo_{congress}.json)')

    args = parser.parse_args()

    # Download and extract
    xml_path = download_bulk_zip(args.congress)

    try:
        # Parse
        raw_members = parse_members_xml(xml_path)
        print(f"Parsed {len(raw_members)} raw members from XML")

        # Map
        entities = [map_to_entity(m) for m in raw_members]

        # Output
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        if not args.output:
            args.output = f"{OUTPUT_DIR}/members_govinfo_{args.congress}.json"

        with open(args.output, 'w') as f:
            json.dump(entities, f, indent=2)

        print(f"Mapped {len(entities)} members to {args.output}")
        print("Sample:")
        print(json.dumps(entities[0], indent=2) if entities else "No data")

    finally:
        # Cleanup temp XML
        if os.path.exists(xml_path):
            os.remove(xml_path)
            print(f"Cleaned up {xml_path}")

if __name__ == "__main__":
    main()