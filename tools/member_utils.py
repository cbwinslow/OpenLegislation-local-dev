"""Utility helpers for member ingestion parsing and normalization."""
from typing import Dict, Optional, List


def normalize_chamber(chamber: Optional[str]) -> str:
    """Normalize various chamber strings to 'house' or 'senate'."""
    if not chamber:
        return ''
    ch = chamber.lower().strip()
    if 'house' in ch:
        return 'house'
    if 'senate' in ch:
        return 'senate'
    return ch


def derive_chamber_from_terms(terms: Optional[List[Dict]]) -> str:
    """Derive chamber from the most recent term (by startYear) if available."""
    if not terms:
        return ''
    chosen = None
    try:
        chosen = max((t for t in terms if t), key=lambda t: int(t.get('startYear') or 0))
    except Exception:
        chosen = terms[-1] if terms else None

    if chosen:
        return normalize_chamber(chosen.get('chamber', ''))
    return ''


def derive_state_from_term(term: Dict) -> str:
    """Return a state string from common term keys.

    Supports `state`, `stateCode`, and `stateName`.
    """
    return term.get('state') or term.get('stateCode') or term.get('stateName') or ''
