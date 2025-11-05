"""Fuzzy matching utilities for pycommon."""

from .fuzzy import (
    normalize_name,
    normalize_location,
    extract_year_from_date,
    fuzzy_match_name,
    fuzzy_match_location,
    compute_confidence_score,
    compute_match_breakdown,
    FUZZY_MATCHING_AVAILABLE,
)

__all__ = [
    'normalize_name',
    'normalize_location',
    'extract_year_from_date',
    'fuzzy_match_name',
    'fuzzy_match_location',
    'compute_confidence_score',
    'compute_match_breakdown',
    'FUZZY_MATCHING_AVAILABLE',
]
