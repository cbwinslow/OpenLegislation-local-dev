"""
Pytest unit and integration tests for federal members fetch/mapping scripts.

Requirements:
    pip install pytest pytest-mock

Run:
    pytest tools/test_fetch_members.py -v

Tests cover:
- Mapping functions with sample data
- Fetch functions with mocked responses (no real API calls)
- XML parsing for GovInfo
"""

import json
import os
import pytest
import xml.etree.ElementTree as ET
from unittest.mock import patch, MagicMock
from tools.fetch_congress_members import fetch_all_members, fetch_member_details, map_to_entity as map_congress_entity
from tools.fetch_govinfo_members import download_bulk_zip, parse_members_xml, map_to_entity as map_govinfo_entity

# Sample data for testing
SAMPLE_CONGRESS_MEMBER_LIST = {
    "members": [
        {
            "bioguideId": "P000197",
            "name": "Charles E. Schumer",
            "chamber": "Senate",
            "party": "Democrat",
            "state": "New York"
        }
    ]
}

SAMPLE_CONGRESS_MEMBER_DETAILS = {
    "member": {
        "basic": {
            "bioguideId": "P000197",
            "name": "Charles E. Schumer",
            "chamber": "Senate",
            "party": "Democrat",
            "state": "New York",
            "contactWebsite": "https://www.schumer.senate.gov"
        },
        "biography": {
            "dateOfBirth": "1950-11-23",
            "placeOfBirth": "Brooklyn, NY"
        },
        "terms": [{"congress": 118, "startDate": "2023-01-03"}],
        "committees": [{"name": "Judiciary", "role": "Chair"}]
    }
}

SAMPLE_GOVINFO_XML = """
<congressionalDirectory>
    <member id="M000123">
        <name>John Doe</name>
        <title>Senator</title>
        <party>Republican</party>
        <state>CA</state>
        <chamber>Senate</chamber>
        <district>N/A</district>
        <address>Washington, DC</address>
        <phone>202-224-3121</phone>
        <committee>
            <name>Appropriations</name>
            <role>Member</role>
        </committee>
        <biography>Born in 1960, lawyer.</biography>
    </member>
</congressionalDirectory>
"""

def test_map_congress_entity_basic():
    """Test mapping from congress.gov basic data."""
    mapped = map_congress_entity(SAMPLE_CONGRESS_MEMBER_DETAILS['member'])
    assert mapped['guid'] == 'P000197'
    assert mapped['fullName'] == 'Charles E. Schumer'
    assert mapped['chamber'] == 'Senate'
    assert mapped['party'] == 'Democrat'
    assert mapped['state'] == 'New York'
    assert 'source' in mapped and mapped['source'] == 'congress.gov'
    assert len(mapped['terms']) == 1
    assert len(mapped['committees']) == 1

def test_map_congress_entity_list_basic():
    """Test mapping from list item (no details)."""
    basic_data = {'basic': SAMPLE_CONGRESS_MEMBER_LIST['members'][0]}
    mapped = map_congress_entity(basic_data)
    assert mapped['guid'] == 'P000197'
    assert 'biography' not in mapped  # Not present

def test_map_govinfo_entity():
    """Test mapping from GovInfo parsed data."""
    parsed_member = {
        'name': 'John Doe',
        'title': 'Senator',
        'party': 'Republican',
        'state': 'CA',
        'chamber': 'Senate',
        'district': 'N/A',
        'office': {'address': 'Washington, DC', 'phone': '202-224-3121'},
        'committees': [{'name': 'Appropriations', 'role': 'Member'}],
        'biography': 'Born in 1960, lawyer.',
        'guid': 'M000123'
    }
    mapped = map_govinfo_entity(parsed_member)
    assert mapped['guid'] == 'M000123'
    assert mapped['fullName'] == 'Senator John Doe'
    assert mapped['chamber'] == 'Senate'
    assert mapped['party'] == 'Republican'
    assert mapped['state'] == 'CA'
    assert 'district' not in mapped  # Filtered N/A
    assert len(mapped['committees']) == 1
    assert 'source' in mapped and mapped['source'] == 'govinfo.gov'

@patch('requests.get')
def test_fetch_all_members_mock(mock_get):
    """Mock API call for congress.gov members list."""
    mock_response = MagicMock()
    mock_response.json.return_value = SAMPLE_CONGRESS_MEMBER_LIST
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    members = fetch_all_members(congress=118, api_key='test_key')
    assert len(members) == 1
    assert members[0]['bioguideId'] == 'P000197'
    mock_get.assert_called_once()

@patch('requests.get')
def test_fetch_member_details_mock(mock_get):
    """Mock API call for single member details."""
    mock_response = MagicMock()
    mock_response.json.return_value = SAMPLE_CONGRESS_MEMBER_DETAILS
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    details = fetch_member_details('P000197', api_key='test_key')
    assert details['basic']['bioguideId'] == 'P000197'
    mock_get.assert_called_once()

def test_parse_members_xml():
    """Test GovInfo XML parsing."""
    # Create temp XML file
    xml_path = '/tmp/test_govinfo.xml'
    with open(xml_path, 'w') as f:
        f.write(SAMPLE_GOVINFO_XML)

    try:
        raw_members = parse_members_xml(xml_path)
        assert len(raw_members) == 1
        assert raw_members[0]['name'] == 'John Doe'
        assert raw_members[0]['guid'] == 'M000123'
        assert len(raw_members[0]['committees']) == 1
        assert raw_members[0]['office']['phone'] == '202-224-3121'
    finally:
        os.remove(xml_path)

@patch('requests.get')
@patch('tools.fetch_govinfo_members.zipfile.ZipFile')
def test_download_bulk_zip_mock(mock_zip, mock_get):
    """Mock download and extract for GovInfo ZIP."""
    mock_response = MagicMock()
    mock_get.return_value = mock_response

    mock_zipfile = MagicMock()
    mock_zip.return_value = mock_zipfile
    mock_zipfile.namelist.return_value = ['CD-118.xml']
    mock_zipfile.read.return_value = b'<xml>mock</xml>'

    xml_path = download_bulk_zip(118)
    assert os.path.exists(xml_path)
    mock_get.assert_called_once()
    os.remove(xml_path)  # Cleanup

# Integration test: Full flow with mocks
@patch('tools.fetch_congress_members.requests.get')
def test_full_congress_flow_mock(mock_get):
    """Mock full fetch and map for congress.gov."""
    mock_list = MagicMock()
    mock_list.json.return_value = SAMPLE_CONGRESS_MEMBER_LIST
    mock_list.raise_for_status.return_value = None

    mock_details = MagicMock()
    mock_details.json.return_value = SAMPLE_CONGRESS_MEMBER_DETAILS
    mock_details.raise_for_status.return_value = None

    mock_get.side_effect = [mock_list, mock_details]

    # Simulate main logic (not directly testable, but test components)
    members = fetch_all_members(118)
    assert len(members) == 1
    details = fetch_member_details('P000197')
    mapped = map_congress_entity(details['member'])
    assert 'guid' in mapped

# Run with pytest -k test_map to select