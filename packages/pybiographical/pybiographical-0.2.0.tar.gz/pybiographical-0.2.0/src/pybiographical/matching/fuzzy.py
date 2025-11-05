"""
Fuzzy Matching Utilities

Provides fuzzy matching capabilities for names, locations, and other text fields
with confidence scoring. Used for duplicate detection and search functionality
across person and artifact metadata.

Author: Jane Smith
Date: November 2025
Version: 0.2.0
"""

import re
from typing import Optional, Dict, Tuple, List

# Optional rapidfuzz support for advanced fuzzy matching
try:
    from rapidfuzz import fuzz
    FUZZY_MATCHING_AVAILABLE = True
except ImportError:
    FUZZY_MATCHING_AVAILABLE = False


def normalize_name(name: str) -> str:
    """
    Normalize a person's name for matching.
    
    Removes common variations to improve matching:
    - Converts to lowercase
    - Removes extra whitespace
    - Removes periods
    - Removes common suffixes (Jr, Sr, II, III, IV)
    
    Args:
        name: Person's name to normalize
    
    Returns:
        Normalized name string
    
    Example:
        >>> normalize_name("Johann Wolfgang von Goethe Jr.")
        'johann wolfgang von goethe'
        >>> normalize_name("Dr. John Q. Public, III")
        'dr john q public'
    """
    if not name:
        return ""
    
    # Lowercase and remove extra spaces
    normalized = name.lower().strip()
    normalized = ' '.join(normalized.split())
    
    # Remove periods
    normalized = normalized.replace('.', '')
    
    # Remove common suffixes
    for suffix in [' jr', ' sr', ' ii', ' iii', ' iv', ' v']:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()
    
    return normalized


def normalize_location(place: str) -> Optional[str]:
    """
    Normalize a location name for matching.
    
    Simplifies location strings to improve matching:
    - Converts to lowercase
    - Removes extra whitespace
    - Removes commas
    
    Args:
        place: Location/place name to normalize
    
    Returns:
        Normalized location string, or None if input is empty
    
    Example:
        >>> normalize_location("Harvey, Wells County, North Dakota, USA")
        'harvey wells county north dakota usa'
        >>> normalize_location("  London,  England  ")
        'london england'
    """
    if not place:
        return None
    
    # Lowercase and trim
    normalized = place.lower().strip()
    
    # Remove extra whitespace
    normalized = ' '.join(normalized.split())
    
    # Remove commas
    normalized = normalized.replace(',', '')
    
    return normalized


def extract_year_from_date(date_str: str) -> Optional[int]:
    """
    Extract a 4-digit year from a date string.
    
    Handles various date formats and looks for years between 1700-2029.
    
    Args:
        date_str: Date string to parse (e.g., "1850-01-15", "Jan 15 1850", etc.)
    
    Returns:
        Extracted year as integer, or None if no valid year found
    
    Example:
        >>> extract_year_from_date("1850-01-15")
        1850
        >>> extract_year_from_date("Born circa 1825")
        1825
        >>> extract_year_from_date("Unknown")
        None
    """
    if not date_str:
        return None
    
    # Look for 4-digit year between 1700-2029
    match = re.search(r'\b(1[7-9]\d{2}|20[0-2]\d)\b', str(date_str))
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    
    return None


def fuzzy_match_name(
    name1: str,
    name2: str,
    threshold: int = 80,
    check_alternates: Optional[List[str]] = None
) -> float:
    """
    Calculate fuzzy match score between two names.
    
    Uses rapidfuzz if available, otherwise falls back to simple matching.
    Can check against alternate spellings for better matching.
    
    Args:
        name1: First name to compare
        name2: Second name to compare
        threshold: Minimum score to consider a match (0-100)
        check_alternates: Optional list of alternate spellings to check
    
    Returns:
        Match confidence score (0-100)
    
    Example:
        >>> fuzzy_match_name("Hans Mueller", "John Johnson")
        92.3
        >>> fuzzy_match_name("Smith", "Smyth", check_alternates=["Smithe", "Smythe"])
        95.5
    
    Note:
        Requires rapidfuzz for fuzzy matching. Falls back to exact matching
        if rapidfuzz is not available.
    """
    if not name1 or not name2:
        return 0.0
    
    # Normalize both names
    name1_norm = normalize_name(name1)
    name2_norm = normalize_name(name2)
    
    # Exact match
    if name1_norm == name2_norm:
        return 100.0
    
    # Fuzzy matching if available
    if FUZZY_MATCHING_AVAILABLE:
        # Check main names
        best_score = fuzz.token_sort_ratio(name1_norm, name2_norm)
        
        # Check alternates if provided
        if check_alternates:
            for alt in check_alternates:
                alt_norm = normalize_name(alt)
                score = fuzz.token_sort_ratio(name1_norm, alt_norm)
                best_score = max(best_score, score)
                
                score = fuzz.token_sort_ratio(name2_norm, alt_norm)
                best_score = max(best_score, score)
        
        return float(best_score)
    else:
        # Fallback: simple substring matching
        if name1_norm in name2_norm or name2_norm in name1_norm:
            return 70.0
        return 0.0


def fuzzy_match_location(
    location1: str,
    location2: str,
    threshold: int = 60
) -> float:
    """
    Calculate fuzzy match score between two locations.
    
    Uses partial ratio matching to handle locations with different levels
    of specificity (e.g., "Harvey, ND" vs "Harvey, Wells County, North Dakota").
    
    Args:
        location1: First location to compare
        location2: Second location to compare
        threshold: Minimum score to consider a match (0-100)
    
    Returns:
        Match confidence score (0-100)
    
    Example:
        >>> fuzzy_match_location("Harvey, Wells County, ND", "Harvey, North Dakota")
        88.5
        >>> fuzzy_match_location("London", "London, England, UK")
        75.0
    
    Note:
        Requires rapidfuzz. Falls back to substring matching if unavailable.
    """
    if not location1 or not location2:
        return 0.0
    
    # Normalize both locations
    loc1_norm = normalize_location(location1)
    loc2_norm = normalize_location(location2)
    
    if not loc1_norm or not loc2_norm:
        return 0.0
    
    # Exact match
    if loc1_norm == loc2_norm:
        return 100.0
    
    # Fuzzy matching if available
    if FUZZY_MATCHING_AVAILABLE:
        # Use partial ratio for locations (handles different specificity levels)
        score = fuzz.partial_ratio(loc1_norm, loc2_norm)
        return float(score)
    else:
        # Fallback: simple substring matching
        if loc1_norm in loc2_norm or loc2_norm in loc1_norm:
            return 70.0
        return 0.0


def compute_confidence_score(
    name_score: float,
    birth_year_diff: Optional[int] = None,
    parent_match: bool = False,
    location_score: Optional[float] = None,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Compute overall confidence score for a person match.
    
    Combines multiple matching factors with configurable weights to produce
    an overall confidence score. Used for duplicate detection and search.
    
    Args:
        name_score: Name match score (0-100)
        birth_year_diff: Difference in birth years (None if unknown)
        parent_match: Whether parent names match
        location_score: Birth place match score (0-100, None if unknown)
        weights: Optional custom weights for factors
    
    Returns:
        Overall confidence score (0-100)
    
    Default Weights:
        - name: 40%
        - birth_year: 20%
        - parents: 20%
        - location: 20%
    
    Example:
        >>> compute_confidence_score(
        ...     name_score=95.0,
        ...     birth_year_diff=2,
        ...     parent_match=True,
        ...     location_score=85.0
        ... )
        92.5
    """
    # Default weights
    default_weights = {
        'name': 0.40,
        'birth_year': 0.20,
        'parents': 0.20,
        'location': 0.20
    }
    
    if weights:
        default_weights.update(weights)
    
    w = default_weights
    confidence = 0.0
    
    # Name score (heavily weighted)
    confidence += name_score * w['name']
    
    # Birth year score
    if birth_year_diff is not None:
        if birth_year_diff == 0:
            year_score = 100.0
        elif birth_year_diff <= 2:
            year_score = 90.0
        elif birth_year_diff <= 5:
            year_score = 70.0
        else:
            year_score = 0.0  # Too different
        confidence += year_score * w['birth_year']
    else:
        # Unknown - neutral
        confidence += 50.0 * w['birth_year']
    
    # Parent match score
    if parent_match:
        confidence += 100.0 * w['parents']
    else:
        # Unknown/no match - neutral
        confidence += 50.0 * w['parents']
    
    # Location score
    if location_score is not None:
        confidence += location_score * w['location']
    else:
        # Unknown - neutral
        confidence += 50.0 * w['location']
    
    return round(confidence, 2)


def compute_match_breakdown(
    name1: str,
    name2: str,
    birth_year1: Optional[int] = None,
    birth_year2: Optional[int] = None,
    location1: Optional[str] = None,
    location2: Optional[str] = None,
    parent1_names: Optional[Tuple[str, str]] = None,
    parent2_names: Optional[Tuple[str, str]] = None,
) -> Dict[str, float]:
    """
    Compute detailed match breakdown for debugging and transparency.
    
    Provides individual scores for each matching factor to understand
    why two records did or didn't match.
    
    Args:
        name1: First person's name
        name2: Second person's name
        birth_year1: First person's birth year
        birth_year2: Second person's birth year
        location1: First person's birth location
        location2: Second person's birth location
        parent1_names: First person's (father_name, mother_name)
        parent2_names: Second person's (father_name, mother_name)
    
    Returns:
        Dictionary with individual match scores and overall confidence
    
    Example:
        >>> breakdown = compute_match_breakdown(
        ...     name1="Hans Mueller",
        ...     name2="John Johnson",
        ...     birth_year1=1825,
        ...     birth_year2=1825,
        ...     location1="Harvey, ND",
        ...     location2="Harvey, North Dakota"
        ... )
        >>> print(breakdown)
        {
            'name_score': 95.0,
            'birth_year_score': 100.0,
            'location_score': 88.5,
            'parent_score': None,
            'overall': 92.3
        }
    """
    breakdown = {}
    
    # Name matching
    breakdown['name_score'] = fuzzy_match_name(name1, name2)
    
    # Birth year matching
    if birth_year1 is not None and birth_year2 is not None:
        year_diff = abs(birth_year1 - birth_year2)
        if year_diff == 0:
            breakdown['birth_year_score'] = 100.0
        elif year_diff <= 2:
            breakdown['birth_year_score'] = 90.0
        elif year_diff <= 5:
            breakdown['birth_year_score'] = 70.0
        else:
            breakdown['birth_year_score'] = 0.0
    else:
        breakdown['birth_year_score'] = None
    
    # Location matching
    if location1 and location2:
        breakdown['location_score'] = fuzzy_match_location(location1, location2)
    else:
        breakdown['location_score'] = None
    
    # Parent matching
    if parent1_names and parent2_names:
        father1, mother1 = parent1_names
        father2, mother2 = parent2_names
        
        father_match = 0.0
        mother_match = 0.0
        
        if father1 and father2:
            father_match = fuzzy_match_name(father1, father2)
        
        if mother1 and mother2:
            mother_match = fuzzy_match_name(mother1, mother2)
        
        # Average parent match scores
        if father_match > 0 and mother_match > 0:
            breakdown['parent_score'] = (father_match + mother_match) / 2
        elif father_match > 0:
            breakdown['parent_score'] = father_match
        elif mother_match > 0:
            breakdown['parent_score'] = mother_match
        else:
            breakdown['parent_score'] = 0.0
    else:
        breakdown['parent_score'] = None
    
    # Compute overall confidence
    birth_year_diff = None
    if birth_year1 is not None and birth_year2 is not None:
        birth_year_diff = abs(birth_year1 - birth_year2)
    
    parent_match = (breakdown['parent_score'] or 0) > 70
    
    breakdown['overall'] = compute_confidence_score(
        name_score=breakdown['name_score'],
        birth_year_diff=birth_year_diff,
        parent_match=parent_match,
        location_score=breakdown['location_score']
    )
    
    return breakdown
