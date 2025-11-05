"""Person metadata management utilities."""

from .models import PersonFile, ValidationIssue, SearchResult, DetectionResult
from .validation import (
    validate_person_yaml,
    validate_person_data,
    fix_schema_version,
    scan_directory,
    validate_directory,
    summarize_issues,
    CURRENT_SCHEMA_VERSION,
)
from .crud import (
    PersonCRUD,
    generate_person_id,
    sanitize_filename
)

__all__ = [
    # Models
    'PersonFile',
    'ValidationIssue',
    'SearchResult',
    'DetectionResult',
    # Validation
    'validate_person_yaml',
    'validate_person_data',
    'fix_schema_version',
    'scan_directory',
    'validate_directory',
    'summarize_issues',
    'CURRENT_SCHEMA_VERSION',
    # CRUD
    'PersonCRUD',
    'generate_person_id',
    'sanitize_filename',
]
