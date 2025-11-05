"""
Person Metadata Models

Defines data structures for person metadata files, validation results,
and related metadata. Used across genealogy, media-tagging, and other
person-centric applications.

Author: Jane Smith
Date: November 2025
Version: 0.2.0
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set, Dict, Any


@dataclass
class ValidationIssue:
    """
    Represents a validation issue found in a person metadata file.
    
    Attributes:
        severity: Issue severity level ('CRITICAL', 'ERROR', 'WARNING', 'INFO')
        issue: Description of the validation issue
        fixable: Whether the issue can be automatically fixed
        field_path: Optional dot-notation path to problematic field
    
    Class Constants:
        CRITICAL: Missing required fields, cannot be processed
        ERROR: Invalid structure or values
        WARNING: Missing recommended fields
        INFO: Minor issues (e.g., old schema version)
    
    Example:
        >>> issue = ValidationIssue(
        ...     severity=ValidationIssue.CRITICAL,
        ...     issue="Missing required field: person_id",
        ...     fixable=False
        ... )
        >>> print(issue)
        CRITICAL: Missing required field: person_id
    """
    
    # Severity levels
    CRITICAL = "CRITICAL"  # Missing required fields
    ERROR = "ERROR"        # Invalid structure
    WARNING = "WARNING"    # Missing optional but recommended fields
    INFO = "INFO"          # Schema version missing, etc.
    
    severity: str
    issue: str
    fixable: bool = False
    field_path: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of validation issue."""
        fix_str = " [FIXABLE]" if self.fixable else ""
        field_str = f" (field: {self.field_path})" if self.field_path else ""
        return f"{self.severity}: {self.issue}{field_str}{fix_str}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'severity': self.severity,
            'issue': self.issue,
            'fixable': self.fixable,
            'field_path': self.field_path
        }


@dataclass
class PersonFile:
    """
    Represents a person metadata file with indexed metadata for efficient processing.
    
    This dataclass encapsulates metadata for person files used in genealogy,
    media tagging, and other applications. Includes indexed fields for duplicate
    detection, fuzzy matching, and general person data processing without repeatedly
    parsing files.
    
    Attributes:
        path: Path to the metadata file (YAML, JSON, etc.)
        dataset_type: Type of dataset ('GEDCOM', 'GFR', 'CUSTOM', etc.)
        person_id: Unique person identifier
        name_full: Full name as appears in file
        name_normalized: Normalized name for matching
        name_tokens: Set of name tokens for fast matching
        surname: Family name/surname
        given_names: Given names (first, middle)
        birth_year: Birth year if available
        father_name: Father's name if available
        mother_name: Mother's name if available
        birth_place: Birth place if available
        birth_place_normalized: Normalized birth place for matching
        sources: List of source file paths or URLs
        checksum: SHA-256 checksum of file contents
        raw_data: Original parsed data (dict)
    
    Example:
        >>> person = PersonFile(
        ...     path=Path("I382302780374_Hans_Mueller.yaml"),
        ...     dataset_type="biographical dataset",
        ...     person_id="I382302780374",
        ...     name_full="Hans Mueller",
        ...     name_normalized="hans mueller",
        ...     name_tokens={"hans", "mueller"},
        ...     surname="Mueller",
        ...     given_names="Hans",
        ...     birth_year=1825,
        ...     # ... other fields
        ... )
    """
    
    path: Path
    dataset_type: str
    person_id: str
    name_full: str
    name_normalized: str
    name_tokens: Set[str]
    surname: str
    given_names: str
    birth_year: Optional[int]
    father_name: Optional[str]
    mother_name: Optional[str]
    birth_place: Optional[str]
    birth_place_normalized: Optional[str]
    sources: List[str]
    checksum: str
    raw_data: Dict[str, Any] = field(repr=False)
    
    def has_birth_info(self) -> bool:
        """Check if person has any birth information."""
        return bool(self.birth_year or self.birth_place)
    
    def has_parent_info(self) -> bool:
        """Check if person has any parent information."""
        return bool(self.father_name or self.mother_name)
    
    def is_gedcom(self) -> bool:
        """Check if this is a GEDCOM person."""
        return self.dataset_type == 'GEDCOM'
    
    def is_gfr(self) -> bool:
        """Check if this is a GFR person."""
        return self.dataset_type == 'GFR'
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """
        Convert to summary dictionary (without raw_data).
        
        Useful for logging, debugging, and serialization.
        """
        return {
            'person_id': self.person_id,
            'name_full': self.name_full,
            'dataset_type': self.dataset_type,
            'birth_year': self.birth_year,
            'birth_place': self.birth_place,
            'father_name': self.father_name,
            'mother_name': self.mother_name,
            'file_path': str(self.path),
            'checksum': self.checksum[:16]  # First 16 chars for brevity
        }


@dataclass
class SearchResult:
    """
    Represents a person search result with confidence score.
    
    Used for fuzzy matching and duplicate detection across person metadata.
    
    Attributes:
        person: The matched PersonFile
        confidence: Match confidence score (0-100)
        match_factors: Dictionary of factor scores that contributed to confidence
    
    Example:
        >>> result = SearchResult(
        ...     person=person_file,
        ...     confidence=95.5,
        ...     match_factors={
        ...         'name': 98.0,
        ...         'birth_year': 100.0,
        ...         'parents': 87.0
        ...     }
        ... )
    """
    
    person: PersonFile
    confidence: float
    match_factors: Dict[str, float] = field(default_factory=dict)
    
    def __str__(self) -> str:
        """String representation of search result."""
        return (
            f"SearchResult(person_id={self.person.person_id}, "
            f"name={self.person.name_full}, "
            f"confidence={self.confidence:.1f}%)"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'person': self.person.to_summary_dict(),
            'confidence': self.confidence,
            'match_factors': self.match_factors
        }


@dataclass
class DetectionResult:
    """
    Result of non-person detection scan.
    
    Used to identify entries that aren't actual persons (organizations,
    streets, schools, etc.) in person metadata collections.
    
    Attributes:
        is_non_person: True if detected as non-person
        confidence: Confidence score (0-100)
        matched_patterns: List of pattern names that matched
        recommended_action: Recommended action ('delete', 'review', 'keep')
    
    Example:
        >>> result = DetectionResult(
        ...     is_non_person=True,
        ...     confidence=95,
        ...     matched_patterns=['organization', 'committee'],
        ...     recommended_action='delete'
        ... )
    """
    
    is_non_person: bool
    confidence: int
    matched_patterns: List[str]
    recommended_action: str  # 'delete', 'review', 'keep'
    
    def __str__(self) -> str:
        """String representation of detection result."""
        action_str = f" -> {self.recommended_action.upper()}"
        patterns_str = f" (patterns: {', '.join(self.matched_patterns)})" if self.matched_patterns else ""
        return f"{'NON-PERSON' if self.is_non_person else 'PERSON'} ({self.confidence}%){patterns_str}{action_str}"
