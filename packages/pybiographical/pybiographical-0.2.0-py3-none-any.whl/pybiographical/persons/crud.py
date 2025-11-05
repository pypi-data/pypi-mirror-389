"""
Person Metadata CRUD Operations

Provides comprehensive Create, Read, Update, Delete operations for person metadata files
with duplicate detection, fuzzy search, and automatic backup management.

Author: Jane Smith
Date: November 2025
Version: 0.2.0
"""

import logging
import random
import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from ..io import get_yaml_handler, load_yaml, dump_yaml, create_backup
from ..matching import (
    fuzzy_match_name,
    fuzzy_match_location,
    normalize_name,
    FUZZY_MATCHING_AVAILABLE
)
from .validation import validate_person_data, CURRENT_SCHEMA_VERSION

# Setup module logger
logger = logging.getLogger(__name__)


# ============================================================================
# Utility Functions
# ============================================================================

def generate_person_id(dataset_type: str = 'GEDCOM') -> str:
    """
    Generate a unique person identifier.
    
    Args:
        dataset_type: Type of dataset ('GEDCOM', 'GFR', 'CUSTOM')
    
    Returns:
        Generated person ID string
    
    Example:
        >>> generate_person_id('GEDCOM')
        'I382145678901'
        >>> generate_person_id('GFR')
        'GFR-a1b2c3d4'
    """
    if dataset_type == 'GEDCOM':
        # Generate GEDCOM-style ID
        return f"I382{random.randint(100000000, 999999999)}"
    elif dataset_type == 'GFR':
        # Generate GFR-style ID
        return f"GFR-{uuid.uuid4().hex[:8]}"
    else:
        # Generate generic ID
        return f"PERSON-{uuid.uuid4().hex[:8]}"


def sanitize_filename(name: str) -> str:
    """
    Sanitize a name for use in filenames.
    
    Removes or replaces invalid filesystem characters.
    
    Args:
        name: Name string to sanitize
    
    Returns:
        Sanitized name safe for filenames
    
    Example:
        >>> sanitize_filename("John Q. Public, Jr.")
        'John_Q_Public_Jr'
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    
    # Remove extra spaces
    name = '_'.join(name.split())
    
    return name


# ============================================================================
# PersonCRUD Class
# ============================================================================

class PersonCRUD:
    """
    Handles CRUD operations for person metadata files.
    
    Provides create, read, update, delete operations with:
    - Automatic duplicate detection
    - Fuzzy search capabilities  
    - Idempotent operations
    - Automatic backup management
    - Archive/restore functionality
    
    Example:
        >>> crud = PersonCRUD(
        ...     persons_dir=Path("data/persons"),
        ...     backup_dir=Path("data/backups"),
        ...     archive_dir=Path("data/archive")
        ... )
        >>> person = crud.create("John", "Doe", birth_year=1850)
        >>> print(person['person_id'])
    """
    
    def __init__(
        self,
        persons_dir: Path,
        backup_dir: Path,
        archive_dir: Path,
        location_resolver: Optional[Any] = None
    ):
        """
        Initialize PersonCRUD handler.
        
        Args:
            persons_dir: Directory containing person YAML files
            backup_dir: Directory for backups
            archive_dir: Directory for archived/deleted persons
            location_resolver: Optional location resolver for place names
        """
        self.persons_dir = Path(persons_dir)
        self.backup_dir = Path(backup_dir)
        self.archive_dir = Path(archive_dir)
        self.location_resolver = location_resolver
        
        # Ensure directories exist
        self.persons_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize YAML handler
        self.yaml = get_yaml_handler()
        
        logger.debug(f"PersonCRUD initialized: {self.persons_dir}")
    
    # ========================================================================
    # CREATE
    # ========================================================================
    
    def create(
        self,
        given_names: str,
        surname: str,
        check_duplicates: bool = True,
        **kwargs
    ) -> Dict:
        """
        Create a new person record (idempotent with duplicate checking).
        
        Args:
            given_names: Given names (first, middle)
            surname: Family name/surname
            check_duplicates: Check for duplicates before creating
            **kwargs: Additional fields:
                - person_id: Custom ID (auto-generated if not provided)
                - dataset_type: 'GEDCOM', 'GFR', or 'CUSTOM'
                - gender: 'Male', 'Female', or 'Unknown'
                - birth_year: Birth year (int)
                - birth_date: Birth date (str)
                - birth_place: Birth place (str)
                - sources: List of sources
                - notes: Notes (str)
                - tags: List of tags
        
        Returns:
            Created person data dictionary
        
        Raises:
            FileExistsError: If person file already exists
            ValueError: If validation fails
        
        Example:
            >>> person = crud.create(
            ...     "Johann",
            ...     "Johnson",
            ...     birth_year=1825,
            ...     birth_place="Harvey, ND"
            ... )
        """
        # Check for duplicates (if enabled)
        if check_duplicates:
            existing = self._find_duplicate(
                given_names=given_names,
                surname=surname,
                birth_year=kwargs.get('birth_year'),
                gender=kwargs.get('gender')
            )
            
            if existing:
                person_data, confidence = existing
                logger.info(
                    f"Found existing person: {person_data['person_id']} "
                    f"({confidence:.1f}% match)"
                )
                
                if confidence >= 95:
                    # Very high confidence - return existing (idempotent)
                    logger.info("Returning existing record (idempotent)")
                    return person_data
                elif confidence >= 85:
                    # High confidence - warn but continue
                    logger.warning(
                        f"Potential duplicate: {person_data['person_id']} "
                        f"({confidence:.1f}% match)"
                    )
        
        # Generate person ID if not provided
        person_id = kwargs.get('person_id')
        if not person_id:
            dataset_type = kwargs.get('dataset_type', 'GEDCOM')
            person_id = generate_person_id(dataset_type)
        
        # Build full name
        full_name = f"{given_names} {surname}"
        
        # Create person data structure
        person_data = {
            'schema_version': CURRENT_SCHEMA_VERSION,
            'person_id': person_id,
            'name': {
                'full_name': full_name,
                'given_names': given_names,
                'surname': surname
            }
        }
        
        # Add optional fields
        if 'gender' in kwargs:
            person_data['gender'] = kwargs['gender']
        
        if any(k in kwargs for k in ['birth_year', 'birth_date', 'birth_place']):
            person_data['vital_events'] = {'birth': {}}
            birth = person_data['vital_events']['birth']
            
            if 'birth_date' in kwargs:
                birth['date'] = kwargs['birth_date']
            if 'birth_year' in kwargs:
                birth['year'] = kwargs['birth_year']
            if 'birth_place' in kwargs:
                birth['place'] = kwargs['birth_place']
        
        if 'sources' in kwargs:
            person_data['sources'] = kwargs['sources']
        if 'notes' in kwargs:
            person_data['notes'] = kwargs['notes']
        if 'tags' in kwargs:
            person_data['tags'] = kwargs['tags']
        
        # Validate
        issues = validate_person_data(person_data)
        critical_issues = [i for i in issues if i.severity == 'CRITICAL']
        if critical_issues:
            errors = [str(i) for i in critical_issues]
            raise ValueError(f"Invalid person data: {'; '.join(errors)}")
        
        # Generate filename
        safe_given = sanitize_filename(given_names)
        safe_surname = sanitize_filename(surname)
        filename = f"{person_id}_{safe_given}_{safe_surname}.yaml"
        file_path = self.persons_dir / filename
        
        # Check if file already exists
        if file_path.exists():
            raise FileExistsError(f"Person file already exists: {file_path}")
        
        # Write YAML file
        dump_yaml(person_data, file_path)
        
        logger.info(f"Created person: {person_id} ({full_name})")
        logger.debug(f"  File: {file_path}")
        
        return person_data
    
    def _find_duplicate(
        self,
        given_names: str,
        surname: str,
        birth_year: Optional[int] = None,
        gender: Optional[str] = None
    ) -> Optional[Tuple[Dict, float]]:
        """Find potential duplicate person."""
        search_criteria = {
            'surname': surname,
            'given_names': given_names,
            'fuzzy': True,
            'threshold': 80
        }
        
        if birth_year:
            search_criteria['birth_year'] = birth_year
        if gender:
            search_criteria['gender'] = gender
        
        results = self.search(**search_criteria)
        
        if results:
            return results[0]  # Highest confidence match
        
        return None
    
    # ========================================================================
    # READ
    # ========================================================================
    
    def read(self, person_id: str) -> Optional[Dict]:
        """
        Read a person record by ID.
        
        Args:
            person_id: Person identifier
        
        Returns:
            Person data dictionary or None if not found
        
        Example:
            >>> person = crud.read("I382302780374")
            >>> if person:
            ...     print(person['name']['full_name'])
        """
        # Find file matching person_id
        matches = list(self.persons_dir.glob(f"{person_id}_*.yaml"))
        
        if not matches:
            logger.warning(f"Person not found: {person_id}")
            return None
        
        if len(matches) > 1:
            logger.warning(
                f"Multiple files found for {person_id}, using first match"
            )
        
        file_path = matches[0]
        data = load_yaml(file_path)
        
        logger.debug(f"Read person: {person_id} from {file_path}")
        
        return data
    
    def search(self, **criteria) -> List[Tuple[Dict, float]]:
        """
        Search for persons with fuzzy matching and confidence scoring.
        
        Args:
            **criteria: Search criteria:
                - surname: Surname to match
                - given_names: Given names to match
                - birth_year: Birth year (with ±5 year tolerance)
                - gender: Gender to match
                - birth_place: Birth place to match
                - fuzzy: Enable fuzzy matching (default: True)
                - threshold: Minimum confidence score (default: 60)
        
        Returns:
            List of (person_data, confidence_score) tuples sorted by confidence
        
        Example:
            >>> results = crud.search(surname="Johnson", birth_year=1825, fuzzy=True)
            >>> for person, confidence in results:
            ...     print(f"{person['name']['full_name']}: {confidence}%")
        """
        use_fuzzy = criteria.pop('fuzzy', True) and FUZZY_MATCHING_AVAILABLE
        threshold = criteria.pop('threshold', 60)
        
        if not FUZZY_MATCHING_AVAILABLE and use_fuzzy:
            logger.warning("rapidfuzz not available, using exact matching only")
            use_fuzzy = False
        
        matches = []
        
        for yaml_file in self.persons_dir.glob("*.yaml"):
            try:
                data = load_yaml(yaml_file)
                confidence = 100.0  # Start with perfect score
                
                # Exact match filter for person_id
                if 'person_id' in criteria:
                    if criteria['person_id'] != data.get('person_id'):
                        continue
                
                # Surname matching
                if 'surname' in criteria:
                    surname = data.get('name', {}).get('surname', '')
                    if not surname:
                        continue
                    
                    if use_fuzzy:
                        alt_spellings = data.get('name', {}).get('alternate_spellings', [])
                        score = fuzzy_match_name(
                            criteria['surname'],
                            surname,
                            check_alternates=alt_spellings
                        )
                        
                        if score < threshold:
                            continue
                        
                        # Weight surname heavily (40%)
                        confidence = confidence * 0.6 + (score * 0.4)
                    else:
                        if criteria['surname'].lower() not in surname.lower():
                            continue
                
                # Given names matching
                if 'given_names' in criteria:
                    given = data.get('name', {}).get('given_names', '')
                    if not given:
                        nicknames = data.get('name', {}).get('nicknames', [])
                        if nicknames:
                            given = ' '.join(nicknames)
                        else:
                            continue
                    
                    if use_fuzzy:
                        nicknames = data.get('name', {}).get('nicknames', [])
                        score = fuzzy_match_name(
                            criteria['given_names'],
                            given,
                            check_alternates=nicknames
                        )
                        
                        if score < threshold:
                            continue
                        
                        # Weight given names (30%)
                        confidence = confidence * 0.7 + (score * 0.3)
                    else:
                        if criteria['given_names'].lower() not in given.lower():
                            continue
                
                # Birth year matching (with tolerance)
                if 'birth_year' in criteria:
                    birth_year = data.get('vital_events', {}).get('birth', {}).get('year')
                    if birth_year:
                        year_diff = abs(birth_year - criteria['birth_year'])
                        if year_diff == 0:
                            confidence = min(100, confidence * 1.1)
                        elif year_diff <= 2:
                            confidence *= 0.95
                        elif year_diff <= 5:
                            confidence *= 0.85
                        else:
                            continue
                    else:
                        confidence *= 0.9
                
                # Gender matching
                if 'gender' in criteria:
                    gender = data.get('gender', '').lower()
                    if gender and gender != 'unknown':
                        if criteria['gender'].lower() == gender:
                            confidence = min(100, confidence * 1.05)
                        else:
                            continue
                    else:
                        confidence *= 0.95
                
                # Birth place matching
                if 'birth_place' in criteria and use_fuzzy:
                    birth_place = data.get('vital_events', {}).get('birth', {}).get('place', '')
                    if birth_place:
                        score = fuzzy_match_location(criteria['birth_place'], birth_place)
                        if score >= threshold:
                            confidence = confidence * 0.9 + (score * 0.1)
                        else:
                            confidence *= 0.8
                    else:
                        confidence *= 0.9
                
                # Add to matches if above threshold
                if confidence >= threshold:
                    matches.append((data, round(confidence, 2)))
            
            except Exception as e:
                logger.error(f"Error reading {yaml_file}: {e}")
        
        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Found {len(matches)} matching persons")
        return matches
    
    # ========================================================================
    # UPDATE
    # ========================================================================
    
    def update(
        self,
        person_id: str,
        updates: Dict,
        make_backup: bool = True
    ) -> bool:
        """
        Update a person record (idempotent - only updates if values differ).
        
        Args:
            person_id: Person identifier
            updates: Dictionary of field updates (supports nested keys with dots)
            make_backup: Whether to create backup before updating
        
        Returns:
            True if successful, False otherwise
        
        Example:
            >>> success = crud.update(
            ...     "I382302780374",
            ...     {'vital_events.birth.date': '1850-01-15'}
            ... )
        """
        # Find file
        matches = list(self.persons_dir.glob(f"{person_id}_*.yaml"))
        
        if not matches:
            logger.error(f"Person not found: {person_id}")
            return False
        
        file_path = matches[0]
        data = load_yaml(file_path)
        
        # Check if updates are needed (idempotent)
        changes_needed = False
        for key, value in updates.items():
            current_value = self._get_nested_value(data, key)
            if current_value != value:
                changes_needed = True
                break
        
        if not changes_needed:
            logger.info(f"Person {person_id} already has requested values (idempotent)")
            return True
        
        # Create backup
        if make_backup:
            backup_path = create_backup(file_path, self.backup_dir)
            logger.info(f"Backup created: {backup_path}")
        
        # Apply updates
        for key, value in updates.items():
            self._set_nested_value(data, key, value)
        
        # Validate
        issues = validate_person_data(data)
        critical_issues = [i for i in issues if i.severity == 'CRITICAL']
        if critical_issues:
            logger.error(f"Validation failed after update: {critical_issues}")
            return False
        
        # Write updated data
        dump_yaml(data, file_path)
        
        logger.info(f"Updated person: {person_id}")
        logger.debug(f"  Updates: {updates}")
        
        return True
    
    def _get_nested_value(self, data: Dict, key_path: str) -> Any:
        """Get nested dictionary value using dot notation."""
        keys = key_path.split('.')
        current = data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return None
    
    def _set_nested_value(self, data: Dict, key_path: str, value: Any):
        """Set nested dictionary value using dot notation."""
        keys = key_path.split('.')
        current = data
        
        # Navigate to parent
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set value
        current[keys[-1]] = value
    
    # ========================================================================
    # DELETE
    # ========================================================================
    
    def delete(self, person_id: str, archive: bool = True) -> bool:
        """
        Delete (or archive) a person record.
        
        Always creates a backup before deletion.
        
        Args:
            person_id: Person identifier
            archive: If True, move to archive instead of deleting
        
        Returns:
            True if successful, False otherwise
        
        Example:
            >>> crud.delete("I382302780374", archive=True)
        """
        # Find file
        matches = list(self.persons_dir.glob(f"{person_id}_*.yaml"))
        
        if not matches:
            logger.error(f"Person not found: {person_id}")
            return False
        
        file_path = matches[0]
        
        # ALWAYS create backup before delete (safety)
        backup_path = create_backup(file_path, self.backup_dir)
        logger.info(f"Backup created before delete: {backup_path}")
        
        if archive:
            # Move to archive
            archive_path = self.archive_dir / file_path.name
            shutil.move(str(file_path), str(archive_path))
            logger.info(f"Archived person: {person_id} -> {archive_path}")
        else:
            # Permanent delete
            file_path.unlink()
            logger.info(f"Deleted person: {person_id}")
        
        return True
    
    # ========================================================================
    # RESTORE
    # ========================================================================
    
    def list_backups(self, person_id: str) -> List[Path]:
        """
        List available backups for a person.
        
        Args:
            person_id: Person identifier
        
        Returns:
            List of backup file paths, sorted by timestamp (newest first)
        
        Example:
            >>> backups = crud.list_backups("I382302780374")
            >>> for backup in backups:
            ...     print(backup.name)
        """
        pattern = f"{person_id}_*"
        backups = list(self.backup_dir.glob(pattern))
        
        # Sort by modification time, newest first
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        return backups
    
    def restore(
        self,
        person_id: str,
        backup_file: Optional[Path] = None
    ) -> bool:
        """
        Restore a person from backup.
        
        Args:
            person_id: Person identifier
            backup_file: Specific backup file (uses latest if None)
        
        Returns:
            True if successful, False otherwise
        
        Example:
            >>> crud.restore("I382302780374")  # Restore from latest backup
        """
        # Find backup file
        if backup_file is None:
            backups = self.list_backups(person_id)
            if not backups:
                logger.error(f"No backups found for {person_id}")
                return False
            backup_file = backups[0]
            logger.info(f"Using latest backup: {backup_file}")
        
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_file}")
            return False
        
        # Load backup data
        data = load_yaml(backup_file)
        
        # Validate
        issues = validate_person_data(data)
        critical_issues = [i for i in issues if i.severity == 'CRITICAL']
        if critical_issues:
            logger.error(f"Backup validation failed: {critical_issues}")
            return False
        
        # Generate target filename
        name = data['name']
        safe_given = sanitize_filename(name.get('given_names', 'Unknown'))
        safe_surname = sanitize_filename(name.get('surname', 'Unknown'))
        filename = f"{person_id}_{safe_given}_{safe_surname}.yaml"
        target_path = self.persons_dir / filename
        
        # If file exists, create backup before overwriting
        if target_path.exists():
            existing_backup = create_backup(target_path, self.backup_dir)
            logger.info(f"Backed up existing file: {existing_backup}")
        
        # Restore from backup
        shutil.copy2(backup_file, target_path)
        logger.info(f"Restored person: {person_id}")
        logger.debug(f"  From: {backup_file}")
        logger.debug(f"  To: {target_path}")
        
        return True
