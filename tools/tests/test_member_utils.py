import pytest

from member_utils import normalize_chamber, derive_chamber_from_terms, derive_state_from_term


def test_normalize_chamber_variants():
    assert normalize_chamber('House of Representatives') == 'house'
    assert normalize_chamber('senator') == 'senate'
    assert normalize_chamber('SENATE') == 'senate'
    assert normalize_chamber(None) == ''


def test_derive_chamber_from_terms():
    terms = [
        {'startYear': '2007', 'chamber': 'Senate'},
        {'startYear': '2019', 'chamber': 'House of Representatives'},
    ]
    # picks term with highest startYear and normalizes
    assert derive_chamber_from_terms(terms) == 'house'


def test_derive_state_from_term():
    assert derive_state_from_term({'stateCode': 'NY'}) == 'NY'
    assert derive_state_from_term({'stateName': 'New York'}) == 'New York'
    assert derive_state_from_term({}) == ''
