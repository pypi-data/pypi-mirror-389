"""
YAML Utilities Module

Provides safe YAML file operations with consistent configuration, backup management,
and atomic writes. Uses ruamel.yaml for better preservation of formatting and comments.

Author: Jane Smith
Date: November 2025
Version: 0.2.0
"""

import hashlib
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from ruamel.yaml import YAML
    from ruamel.yaml.error import YAMLError
except ImportError as e:
    raise ImportError(
        "ruamel.yaml is required for YAML utilities. "
        "Install with: pip install ruamel.yaml"
    ) from e


def get_yaml_handler(
    preserve_quotes: bool = True,
    default_flow_style: bool = False,
    width: int = 4096,
    typ: str = 'rt'
) -> YAML:
    """
    Get a pre-configured YAML handler with sensible defaults.
    
    Args:
        preserve_quotes: Whether to preserve quote styles
        default_flow_style: Whether to use flow style by default
        width: Line width for output formatting
        typ: YAML type ('rt' for round-trip, 'safe' for safe loading)
    
    Returns:
        Configured YAML handler instance
    
    Example:
        >>> yaml = get_yaml_handler()
        >>> data = yaml.load(open('file.yaml'))
    """
    yaml = YAML(typ=typ)
    yaml.preserve_quotes = preserve_quotes
    yaml.default_flow_style = default_flow_style
    yaml.width = width
    return yaml


def load_yaml(file_path: Path, yaml_handler: Optional[YAML] = None) -> Optional[Dict]:
    """
    Safely load a YAML file.
    
    Args:
        file_path: Path to YAML file
        yaml_handler: Optional pre-configured YAML handler
    
    Returns:
        Loaded data as dictionary, or None if file is empty or invalid
    
    Raises:
        FileNotFoundError: If file doesn't exist
        YAMLError: If YAML syntax is invalid
    
    Example:
        >>> data = load_yaml(Path('person.yaml'))
        >>> if data:
        ...     print(data['person_id'])
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if yaml_handler is None:
        yaml_handler = get_yaml_handler()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml_handler.load(f)
    
    # Convert ruamel.yaml omap to dict if needed
    if data is not None and not isinstance(data, dict):
        data = dict(data)
    
    return data


def dump_yaml(
    data: Dict,
    file_path: Path,
    yaml_handler: Optional[YAML] = None,
    create_backup: bool = False,
    backup_dir: Optional[Path] = None
) -> Optional[Path]:
    """
    Safely write data to a YAML file.
    
    Args:
        data: Data to write
        file_path: Target file path
        yaml_handler: Optional pre-configured YAML handler
        create_backup: Whether to create backup before writing
        backup_dir: Directory for backups (defaults to file_path.parent / 'backups')
    
    Returns:
        Path to backup file if created, None otherwise
    
    Example:
        >>> data = {'person_id': 'I123', 'name': {'full_name': 'John Doe'}}
        >>> backup = dump_yaml(data, Path('person.yaml'), create_backup=True)
        >>> print(f"Backup created: {backup}")
    """
    file_path = Path(file_path)
    backup_path = None
    
    # Create backup if requested and file exists
    if create_backup and file_path.exists():
        if backup_dir is None:
            backup_dir = file_path.parent / 'backups'
        backup_path = create_backup_file(file_path, backup_dir)
    
    if yaml_handler is None:
        yaml_handler = get_yaml_handler()
    
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write YAML
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml_handler.dump(data, f)
    
    return backup_path


def create_backup(
    file_path: Path,
    backup_dir: Optional[Path] = None,
    timestamp_format: str = '%Y%m%d_%H%M%S'
) -> Path:
    """
    Create a timestamped backup of a file.
    
    Args:
        file_path: File to backup
        backup_dir: Directory for backup (defaults to file_path.parent / 'backups')
        timestamp_format: Format for timestamp in backup filename
    
    Returns:
        Path to created backup file
    
    Raises:
        FileNotFoundError: If source file doesn't exist
    
    Example:
        >>> backup = create_backup(Path('person.yaml'))
        >>> print(backup.name)
        person_20251103_154500.yaml
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot backup non-existent file: {file_path}")
    
    if backup_dir is None:
        backup_dir = file_path.parent / 'backups'
    
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamped backup filename
    timestamp = datetime.now().strftime(timestamp_format)
    backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
    backup_path = backup_dir / backup_name
    
    # Copy file preserving metadata
    shutil.copy2(file_path, backup_path)
    
    return backup_path


# Alias for backward compatibility
create_backup_file = create_backup


def compute_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute checksum of a file.
    
    Args:
        file_path: File to checksum
        algorithm: Hash algorithm ('sha256', 'md5', etc.)
    
    Returns:
        Hexadecimal checksum string
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If algorithm is not supported
    
    Example:
        >>> checksum = compute_checksum(Path('person.yaml'))
        >>> print(f"SHA-256: {checksum}")
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        hasher = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}") from e
    
    with open(file_path, 'rb') as f:
        # Read in chunks for memory efficiency
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def atomic_write(
    file_path: Path,
    data: Dict,
    yaml_handler: Optional[YAML] = None,
    create_backup: bool = False,
    backup_dir: Optional[Path] = None
) -> Optional[Path]:
    """
    Atomically write data to a YAML file using a temporary file.
    
    This prevents corruption if the write is interrupted. The data is written
    to a temporary file first, then moved to the target location.
    
    Args:
        file_path: Target file path
        data: Data to write
        yaml_handler: Optional pre-configured YAML handler
        create_backup: Whether to create backup before writing
        backup_dir: Directory for backups
    
    Returns:
        Path to backup file if created, None otherwise
    
    Example:
        >>> data = {'person_id': 'I123', 'name': {'full_name': 'John Doe'}}
        >>> atomic_write(Path('person.yaml'), data, create_backup=True)
    """
    file_path = Path(file_path)
    backup_path = None
    
    # Create backup if requested and file exists
    if create_backup and file_path.exists():
        if backup_dir is None:
            backup_dir = file_path.parent / 'backups'
        backup_path = create_backup_file(file_path, backup_dir)
    
    if yaml_handler is None:
        yaml_handler = get_yaml_handler()
    
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to temporary file in same directory (for atomic move)
    with tempfile.NamedTemporaryFile(
        mode='w',
        encoding='utf-8',
        dir=file_path.parent,
        delete=False,
        suffix='.tmp'
    ) as tmp_file:
        yaml_handler.dump(data, tmp_file)
        tmp_path = Path(tmp_file.name)
    
    try:
        # Atomic move (on same filesystem)
        tmp_path.replace(file_path)
    except Exception:
        # Clean up temp file on error
        if tmp_path.exists():
            tmp_path.unlink()
        raise
    
    return backup_path


def validate_yaml_syntax(file_path: Path) -> tuple[bool, Optional[str]]:
    """
    Validate YAML syntax without fully parsing the content.
    
    Args:
        file_path: Path to YAML file to validate
    
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if syntax is valid
        - error_message: Error description if invalid, None if valid
    
    Example:
        >>> is_valid, error = validate_yaml_syntax(Path('person.yaml'))
        >>> if not is_valid:
        ...     print(f"Invalid YAML: {error}")
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    
    try:
        yaml = get_yaml_handler()
        with open(file_path, 'r', encoding='utf-8') as f:
            yaml.load(f)
        return True, None
    except YAMLError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {e}"
