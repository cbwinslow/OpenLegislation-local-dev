#!/usr/bin/env python3

"""
Script to fetch U.S. Congress members data from congress.gov API
and map to OpenLegislation entity model structure (JSON output).

Usage:
    python3 fetch_congress_members.py --congress 118 --chamber senate --api_key YOUR_KEY --output members_senate_118.json

Requirements:
    pip install requests

API Docs: https://api.congress.gov/v3/member
"""

import argparse
import json
import os
import requests
from typing import List, Dict

BASE_URL = "https://api.congress.gov/v3"
LIMIT = 100  # Max per page
OUTPUT_DIR = "output"


def fetch_all_members(
    congress: int, chamber: str = None, api_key: str = None
) -> List[Dict]:
    """
    Fetch all members for a congress, optionally filtered by chamber.
    Paginate through results.
    """
    members = []
    offset = 0
    while True:
        params = {
            "congress": congress,
            "format": "json",
            "limit": LIMIT,
            "offset": offset,
        }
        if chamber:
            params["chamber"] = chamber
        if api_key:
            params["api_key"] = api_key

        response = requests.get(f"{BASE_URL}/member", params=params)
        response.raise_for_status()
        data = response.json()

        if "members" not in data or not data["members"]:
            break

        members.extend(data["members"])
        offset += LIMIT

        if len(data["members"]) < LIMIT:
            break

    return members


def fetch_member_details(bioguide_id: str, api_key: str = None) -> Dict:
    """
    Fetch full details for a single member.
    """
    params = {"format": "json"}
    if api_key:
        params["api_key"] = api_key

    response = requests.get(f"{BASE_URL}/member/{bioguide_id}", params=params)
    response.raise_for_status()
    return response.json().get("member", {})


def map_to_entity(member_data: Dict) -> Dict:
    """
    Map API response to project-like entity model (Member).
    Simplified: Focus on key fields; extend for terms, committees.
    """
    basic = member_data.get("basic", {})
    biography = member_data.get("biography", {})

    entity = {
        "guid": basic.get("bioguideId"),  # Unique ID
        "fullName": basic.get("name"),
        "chamber": basic.get("chamber"),
        "party": basic.get("party"),
        "state": basic.get("state"),
        "district": basic.get("district", "N/A"),  # For House
        "dateOfBirth": biography.get("dateOfBirth"),
        "placeOfBirth": biography.get("placeOfBirth"),
        "education": biography.get("education", []),
        "profession": biography.get("profession", []),
        "family": biography.get("family", {}),
        "contactWebsite": basic.get("contactWebsite"),
        "office": basic.get("office", {}),  # Address, phone
        "terms": member_data.get("terms", []),  # List of term dicts
        "committees": member_data.get("committees", []),  # List of committee dicts
        "source": "congress.gov",
        "lastUpdated": basic.get("lastUpdated"),
    }

    # Clean up None values
    return {k: v for k, v in entity.items() if v is not None}


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and map Congress members from API"
    )
    parser.add_argument(
        "--congress", type=int, default=118, help="Congress number (default: 118)"
    )
    parser.add_argument(
        "--chamber", choices=["senate", "house", "joint"], help="Filter by chamber"
    )
    parser.add_argument(
        "--api_key",
        default=os.getenv("CONGRESS_API_KEY"),
        help="API key (or set CONGRESS_API_KEY env)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON file (default: members_{congress}_{chamber}.json)",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Fetch full details for each member (slower)",
    )

    args = parser.parse_args()

    if not args.api_key:
        args.api_key = input("Enter Congress.gov API key: ").strip()
        if not args.api_key:
            print("API key required for production use. Using demo mode (limited).")
            args.api_key = "DEMO_KEY"  # Limited to basic queries

    print(
        f"Fetching members for Congress {args.congress}, chamber: {args.chamber or 'all'}"
    )

    # Fetch list
    member_list = fetch_all_members(args.congress, args.chamber, args.api_key)

    entities = []
    for member in member_list:
        if args.details:
            # Fetch full details
            bioguide_id = member.get("bioguideId")
            if bioguide_id:
                full_data = fetch_member_details(bioguide_id, args.api_key)
                mapped = map_to_entity(full_data)
            else:
                mapped = map_to_entity({"basic": member})
        else:
            # Basic mapping from list
            mapped = {
                "guid": member.get("bioguideId"),
                "fullName": member.get("name"),
                "chamber": member.get("chamber"),
                "party": member.get("party"),
                "state": member.get("state"),
                "source": "congress.gov",
            }

        entities.append(mapped)

    # Output
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if not args.output:
        chamber_str = args.chamber or "all"
        args.output = f"{OUTPUT_DIR}/members_{args.congress}_{chamber_str}.json"

    with open(args.output, "w") as f:
        json.dump(entities, f, indent=2)

    print(f"Mapped {len(entities)} members to {args.output}")
    print("Sample:")
    print(json.dumps(entities[0], indent=2) if entities else "No data")


if __name__ == "__main__":
    main()
