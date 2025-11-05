"""
Person Metadata Validation Module

Provides validation functions for person metadata files with automatic fixing
capabilities for common issues like missing schema versions.

Author: Jane Smith
Date: November 2025
Version: 0.2.0
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional

from ..io import get_yaml_handler, load_yaml, create_backup
from .models import ValidationIssue

try:
    from ruamel.yaml.error import YAMLError
except ImportError as e:
    raise ImportError(
        "ruamel.yaml is required for validation. "
        "Install with: pip install ruamel.yaml"
    ) from e


# Schema version constants
CURRENT_SCHEMA_VERSION = "1.0.0"
SUPPORTED_SCHEMA_VERSIONS = ["1.0", "1.0.0"]


def validate_person_yaml(
    file_path: Path,
    schema_version: str = CURRENT_SCHEMA_VERSION
) -> Tuple[Optional[Dict], List[ValidationIssue]]:
    """
    Validate a person metadata YAML file.
    
    Checks for:
    - Valid YAML syntax
    - Required fields (person_id, name, name.full_name)
    - Schema version
    - Proper data structure
    
    Args:
        file_path: Path to person YAML file
        schema_version: Expected schema version (default: current)
    
    Returns:
        Tuple of (data_dict, list of validation issues)
        - data_dict: Parsed YAML data (None if critical errors)
        - issues: List of ValidationIssue objects
    
    Example:
        >>> from pathlib import Path
        >>> data, issues = validate_person_yaml(Path("person.yaml"))
        >>> if issues:
        ...     for issue in issues:
        ...         print(issue)
        >>> if data:
        ...     print(f"Person ID: {data['person_id']}")
    """
    issues = []
    data = None
    
    # Check file exists
    if not file_path.exists():
        issues.append(ValidationIssue(
            severity=ValidationIssue.CRITICAL,
            issue=f"File not found: {file_path}",
            fixable=False
        ))
        return None, issues
    
    # Try to load YAML
    try:
        data = load_yaml(file_path)
    except YAMLError as e:
        issues.append(ValidationIssue(
            severity=ValidationIssue.CRITICAL,
            issue=f"Invalid YAML syntax: {e}",
            fixable=False
        ))
        return None, issues
    except Exception as e:
        issues.append(ValidationIssue(
            severity=ValidationIssue.ERROR,
            issue=f"Failed to read file: {e}",
            fixable=False
        ))
        return None, issues
    
    # Check if file is empty
    if not data:
        issues.append(ValidationIssue(
            severity=ValidationIssue.CRITICAL,
            issue="Empty file",
            fixable=False
        ))
        return None, issues
    
    # Validate schema version
    if 'schema_version' not in data:
        issues.append(ValidationIssue(
            severity=ValidationIssue.INFO,
            issue="Missing schema_version",
            fixable=True,
            field_path='schema_version'
        ))
    elif data['schema_version'] == '1.0':
        issues.append(ValidationIssue(
            severity=ValidationIssue.INFO,
            issue=f"Old schema_version format (1.0), should be {schema_version}",
            fixable=True,
            field_path='schema_version'
        ))
    elif data['schema_version'] not in SUPPORTED_SCHEMA_VERSIONS:
        issues.append(ValidationIssue(
            severity=ValidationIssue.WARNING,
            issue=f"Unknown schema_version: {data['schema_version']}",
            fixable=False,
            field_path='schema_version'
        ))
    
    # Validate required fields
    if 'person_id' not in data:
        issues.append(ValidationIssue(
            severity=ValidationIssue.CRITICAL,
            issue="Missing required field: person_id",
            fixable=False,
            field_path='person_id'
        ))
    
    if 'name' not in data:
        issues.append(ValidationIssue(
            severity=ValidationIssue.CRITICAL,
            issue="Missing required field: name",
            fixable=False,
            field_path='name'
        ))
    else:
        # Validate name structure
        if not isinstance(data['name'], dict):
            issues.append(ValidationIssue(
                severity=ValidationIssue.ERROR,
                issue="name must be a dictionary",
                fixable=False,
                field_path='name'
            ))
        elif 'full_name' not in data['name']:
            issues.append(ValidationIssue(
                severity=ValidationIssue.CRITICAL,
                issue="Missing required field: name.full_name",
                fixable=False,
                field_path='name.full_name'
            ))
    
    return data, issues


def validate_person_data(
    data: Dict,
    schema_version: str = CURRENT_SCHEMA_VERSION
) -> List[ValidationIssue]:
    """
    Validate in-memory person data dictionary.
    
    Similar to validate_person_yaml but works on already-loaded data.
    Useful for validating data before writing or after modifications.
    
    Args:
        data: Person data dictionary
        schema_version: Expected schema version
    
    Returns:
        List of validation issues (empty if valid)
    
    Example:
        >>> data = {
        ...     'person_id': 'I123',
        ...     'name': {'full_name': 'John Doe'}
        ... }
        >>> issues = validate_person_data(data)
        >>> if not issues:
        ...     print("Data is valid!")
    """
    issues = []
    
    if not data:
        issues.append(ValidationIssue(
            severity=ValidationIssue.CRITICAL,
            issue="Empty data",
            fixable=False
        ))
        return issues
    
    # Check schema_version
    if 'schema_version' not in data:
        issues.append(ValidationIssue(
            severity=ValidationIssue.INFO,
            issue="Missing schema_version",
            fixable=True,
            field_path='schema_version'
        ))
    
    # Check required fields
    if 'person_id' not in data:
        issues.append(ValidationIssue(
            severity=ValidationIssue.CRITICAL,
            issue="Missing required field: person_id",
            fixable=False,
            field_path='person_id'
        ))
    
    if 'name' not in data:
        issues.append(ValidationIssue(
            severity=ValidationIssue.CRITICAL,
            issue="Missing required field: name",
            fixable=False,
            field_path='name'
        ))
    else:
        if not isinstance(data['name'], dict):
            issues.append(ValidationIssue(
                severity=ValidationIssue.ERROR,
                issue="name must be a dictionary",
                fixable=False,
                field_path='name'
            ))
        elif 'full_name' not in data['name']:
            issues.append(ValidationIssue(
                severity=ValidationIssue.CRITICAL,
                issue="Missing required field: name.full_name",
                fixable=False,
                field_path='name.full_name'
            ))
    
    return issues


def fix_schema_version(
    file_path: Path,
    target_version: str = CURRENT_SCHEMA_VERSION,
    backup_dir: Optional[Path] = None
) -> bool:
    """
    Fix schema version issues in a person YAML file.
    
    Updates or adds schema_version field to the target version.
    Creates a backup before modifying the file.
    
    Args:
        file_path: Path to person YAML file
        target_version: Target schema version to set
        backup_dir: Optional backup directory (defaults to file_path.parent / 'backups')
    
    Returns:
        True if fixed successfully, False otherwise
    
    Example:
        >>> from pathlib import Path
        >>> success = fix_schema_version(Path("person.yaml"))
        >>> if success:
        ...     print("Schema version updated!")
    """
    # Load file
    data, issues = validate_person_yaml(file_path, target_version)
    
    if data is None:
        return False
    
    # Check if there are only fixable schema version issues
    schema_issues = [i for i in issues if 'schema_version' in i.issue]
    other_issues = [i for i in issues if 'schema_version' not in i.issue]
    
    if not schema_issues:
        # No schema version issues to fix
        return True
    
    if any(not i.fixable for i in schema_issues):
        # Has unfixable schema version issues
        return False
    
    # Create backup
    if backup_dir is None:
        backup_dir = file_path.parent / 'backups'
    
    backup_path = create_backup(file_path, backup_dir)
    
    # Fix schema version
    if 'schema_version' in data:
        # Update existing version
        data['schema_version'] = target_version
        new_data = data
    else:
        # Insert schema_version as first key
        new_data = {'schema_version': target_version}
        new_data.update(data)
    
    # Write fixed data
    yaml = get_yaml_handler()
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(new_data, f)
    
    return True


def scan_directory(
    directory: Path,
    pattern: str = "*.yaml",
    limit: Optional[int] = None
) -> List[Path]:
    """
    Scan a directory for YAML files.
    
    Args:
        directory: Directory to scan
        pattern: File pattern to match (default: "*.yaml")
        limit: Optional limit on number of files returned
    
    Returns:
        List of matching file paths
    
    Example:
        >>> from pathlib import Path
        >>> files = scan_directory(Path("data/persons"))
        >>> print(f"Found {len(files)} person files")
    """
    files = list(directory.glob(pattern))
    if limit:
        files = files[:limit]
    return files


def validate_directory(
    directory: Path,
    pattern: str = "*.yaml",
    limit: Optional[int] = None,
    skip_valid: bool = True
) -> Dict[Path, List[ValidationIssue]]:
    """
    Validate all person YAML files in a directory.
    
    Args:
        directory: Directory to scan
        pattern: File pattern to match
        limit: Optional limit on number of files
        skip_valid: If True, only return files with issues
    
    Returns:
        Dictionary mapping file paths to their validation issues
    
    Example:
        >>> from pathlib import Path
        >>> results = validate_directory(Path("data/persons"))
        >>> for file_path, issues in results.items():
        ...     print(f"{file_path.name}: {len(issues)} issues")
    """
    files = scan_directory(directory, pattern, limit)
    results = {}
    
    for file_path in files:
        _, issues = validate_person_yaml(file_path)
        if not skip_valid or issues:
            results[file_path] = issues
    
    return results


def summarize_issues(
    issues: List[ValidationIssue]
) -> Dict[str, int]:
    """
    Summarize validation issues by severity.
    
    Args:
        issues: List of validation issues
    
    Returns:
        Dictionary with counts by severity level
    
    Example:
        >>> issues = [
        ...     ValidationIssue(ValidationIssue.INFO, "Missing schema_version"),
        ...     ValidationIssue(ValidationIssue.CRITICAL, "Missing person_id")
        ... ]
        >>> summary = summarize_issues(issues)
        >>> print(summary)
        {'CRITICAL': 1, 'INFO': 1, 'fixable': 1}
    """
    summary = {
        'CRITICAL': 0,
        'ERROR': 0,
        'WARNING': 0,
        'INFO': 0,
        'fixable': 0
    }
    
    for issue in issues:
        summary[issue.severity] = summary.get(issue.severity, 0) + 1
        if issue.fixable:
            summary['fixable'] += 1
    
    return summary
