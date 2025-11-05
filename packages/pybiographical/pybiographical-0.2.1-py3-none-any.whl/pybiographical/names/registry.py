"""
Name Registry

CRUD operations and search functionality for the Names Registry.

Author: Jane Smith
Date: November 2025
Version: 0.1.0
"""

import json
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import (
    NameEntry, NameQueryResult, LanguageOrigin, CrossLanguageForm,
    SpellingVariant, EtymologyInfo, GeographicUsage, PhoneticEncoding, RootWord
)


class NameRegistry:
    """
    Registry for managing name entries with CRUD operations and search.
    
    Provides:
    - Loading/saving from JSON files
    - CRUD operations (create, read, update, delete)
    - Search by exact name, variants, phonetics, cognates
    - Fuzzy matching support
    
    Example:
        >>> registry = NameRegistry("/path/to/metadata/data/names.json")
        >>> registry.load()
        >>> results = registry.search("Schmidt", include_cognates=True)
    """
    
    def __init__(self, data_file: Optional[str] = None):
        """
        Initialize the registry.
        
        Args:
            data_file: Path to JSON data file. If None, uses in-memory only.
        """
        self.data_file = Path(data_file) if data_file else None
        self.entries: Dict[str, NameEntry] = {}
        self._name_index: Dict[str, List[str]] = {}  # name -> [ids]
        self._phonetic_index: Dict[str, List[str]] = {}  # phonetic -> [ids]
        self._cognate_index: Dict[str, List[str]] = {}  # form -> [ids]
    
    def load(self) -> None:
        """Load entries from JSON file."""
        if not self.data_file or not self.data_file.exists():
            return
        
        with open(self.data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.entries.clear()
        for entry_data in data.get('names', []):
            entry = NameEntry.from_dict(entry_data)
            self.entries[entry.id] = entry
        
        self._rebuild_indexes()
    
    def save(self) -> None:
        """Save entries to JSON file."""
        if not self.data_file:
            raise ValueError("No data file specified")
        
        # Ensure directory exists
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'metadata': {
                'version': '1.0.0',
                'last_updated': datetime.now().isoformat(),
                'total_entries': len(self.entries)
            },
            'names': [entry.to_dict() for entry in self.entries.values()]
        }
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _rebuild_indexes(self) -> None:
        """Rebuild all search indexes."""
        self._name_index.clear()
        self._phonetic_index.clear()
        self._cognate_index.clear()
        
        for entry_id, entry in self.entries.items():
            # Index primary name
            name_lower = entry.name.lower()
            self._name_index.setdefault(name_lower, []).append(entry_id)
            
            # Index spelling variants
            for variant in entry.spelling_variants:
                var_lower = variant.form.lower()
                self._name_index.setdefault(var_lower, []).append(entry_id)
            
            # Index phonetic encodings
            for phonetic in entry.phonetic:
                self._phonetic_index.setdefault(phonetic.value, []).append(entry_id)
            
            # Index cross-language forms
            for clf in entry.cross_language_forms:
                form_lower = clf.form.lower()
                self._cognate_index.setdefault(form_lower, []).append(entry_id)
    
    # CRUD Operations
    
    def create(self, entry: NameEntry) -> NameEntry:
        """
        Create a new name entry.
        
        Args:
            entry: NameEntry to add
            
        Returns:
            The created entry
            
        Raises:
            ValueError: If ID already exists
        """
        if entry.id in self.entries:
            raise ValueError(f"Entry with ID {entry.id} already exists")
        
        entry.date_added = datetime.now()
        entry.date_modified = datetime.now()
        
        self.entries[entry.id] = entry
        self._rebuild_indexes()
        
        return entry
    
    def read(self, entry_id: str) -> Optional[NameEntry]:
        """
        Read a name entry by ID.
        
        Args:
            entry_id: The entry ID
            
        Returns:
            NameEntry if found, None otherwise
        """
        return self.entries.get(entry_id)
    
    def update(self, entry: NameEntry) -> NameEntry:
        """
        Update an existing name entry.
        
        Args:
            entry: NameEntry with updated data
            
        Returns:
            The updated entry
            
        Raises:
            ValueError: If entry ID doesn't exist
        """
        if entry.id not in self.entries:
            raise ValueError(f"Entry with ID {entry.id} not found")
        
        entry.date_modified = datetime.now()
        self.entries[entry.id] = entry
        self._rebuild_indexes()
        
        return entry
    
    def delete(self, entry_id: str) -> bool:
        """
        Delete a name entry.
        
        Args:
            entry_id: The entry ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        if entry_id in self.entries:
            del self.entries[entry_id]
            self._rebuild_indexes()
            return True
        return False
    
    def list_all(self, name_type: Optional[str] = None) -> List[NameEntry]:
        """
        List all entries, optionally filtered by type.
        
        Args:
            name_type: Optional filter (given, middle, surname, etc.)
            
        Returns:
            List of matching entries
        """
        if name_type:
            return [e for e in self.entries.values() if e.name_type == name_type]
        return list(self.entries.values())
    
    # Search Operations
    
    def search_exact(self, name: str) -> List[NameEntry]:
        """
        Search for exact name matches (case-insensitive).
        
        Args:
            name: The name to search for
            
        Returns:
            List of matching entries
        """
        name_lower = name.lower()
        entry_ids = self._name_index.get(name_lower, [])
        return [self.entries[eid] for eid in entry_ids]
    
    def search_phonetic(self, phonetic_value: str, method: str = "soundex") -> List[NameEntry]:
        """
        Search by phonetic encoding.
        
        Args:
            phonetic_value: The phonetic code
            method: Encoding method (soundex, metaphone, etc.)
            
        Returns:
            List of matching entries
        """
        entry_ids = self._phonetic_index.get(phonetic_value, [])
        
        # Filter by method if specified
        results = []
        for eid in entry_ids:
            entry = self.entries[eid]
            for p in entry.phonetic:
                if p.value == phonetic_value and (not method or p.method == method):
                    results.append(entry)
                    break
        
        return results
    
    def search_cognates(self, name: str) -> List[NameEntry]:
        """
        Search for cognate forms across languages.
        
        Args:
            name: The name to search for
            
        Returns:
            List of entries with cognate relationships
        """
        name_lower = name.lower()
        entry_ids = self._cognate_index.get(name_lower, [])
        return [self.entries[eid] for eid in entry_ids]
    
    def search(
        self,
        query: str,
        include_variants: bool = True,
        include_cognates: bool = False,
        name_type: Optional[str] = None
    ) -> List[NameQueryResult]:
        """
        Comprehensive search with confidence scoring.
        
        Args:
            query: Search query
            include_variants: Include spelling variants
            include_cognates: Include cross-language cognates
            name_type: Filter by name type
            
        Returns:
            List of NameQueryResult ordered by confidence
        """
        results = []
        seen_ids = set()
        
        # Exact matches (highest confidence)
        for entry in self.search_exact(query):
            if name_type and entry.name_type != name_type:
                continue
            if entry.id not in seen_ids:
                name_conf = entry.confidence if entry.confidence is not None else 0.5
                results.append(NameQueryResult(entry, 1.0, "exact", name_conf))
                seen_ids.add(entry.id)
        
        # Variant matches
        if include_variants:
            for entry in self.search_exact(query):
                if entry.id not in seen_ids:
                    if name_type and entry.name_type != name_type:
                        continue
                    # Check if match was via variant
                    is_variant = any(v.form.lower() == query.lower() for v in entry.spelling_variants)
                    if is_variant:
                        name_conf = entry.confidence if entry.confidence is not None else 0.5
                        results.append(NameQueryResult(entry, 0.9, "variant", name_conf))
                        seen_ids.add(entry.id)
        
        # Cognate matches
        if include_cognates:
            for entry in self.search_cognates(query):
                if entry.id not in seen_ids:
                    if name_type and entry.name_type != name_type:
                        continue
                    name_conf = entry.confidence if entry.confidence is not None else 0.5
                    results.append(NameQueryResult(entry, 0.8, "cognate", name_conf))
                    seen_ids.add(entry.id)
        
        # Sort by combined confidence (descending)
        results.sort(key=lambda r: min(r.confidence, r.name_confidence) if r.name_confidence else r.confidence, reverse=True)
        
        return results
    
    def find_by_etymology(self, meaning: str) -> List[NameEntry]:
        """
        Find names by etymological meaning.
        
        Args:
            meaning: Search term in meaning or English translation
            
        Returns:
            List of matching entries
        """
        meaning_lower = meaning.lower()
        results = []
        
        for entry in self.entries.values():
            if not entry.etymology:
                continue
            
            # Check meaning
            if entry.etymology.meaning and meaning_lower in entry.etymology.meaning.lower():
                results.append(entry)
                continue
            
            # Check English translation
            if entry.etymology.english_translation and meaning_lower in entry.etymology.english_translation.lower():
                results.append(entry)
                continue
            
            # Check root word meanings
            for root in entry.etymology.root_words:
                if meaning_lower in root.meaning.lower():
                    results.append(entry)
                    break
        
        return results
    
    def find_by_language(self, language: str) -> List[NameEntry]:
        """
        Find names by primary language.
        
        Args:
            language: Language name
            
        Returns:
            List of matching entries
        """
        return [
            e for e in self.entries.values()
            if e.language_origin and e.language_origin.primary_language.lower() == language.lower()
        ]
    
    def find_cognate_group(self, name: str) -> Dict[str, List[NameEntry]]:
        """
        Find all cognate names related to a given name.
        
        Args:
            name: The name to find cognates for
            
        Returns:
            Dict mapping language to list of entries
        """
        # Find the primary entry
        primary_entries = self.search_exact(name)
        if not primary_entries:
            return {}
        
        # Collect all cognate forms
        cognate_group = {}
        
        for entry in primary_entries:
            # Add primary entry
            if entry.language_origin:
                lang = entry.language_origin.primary_language
                cognate_group.setdefault(lang, []).append(entry)
            
            # Add cross-language cognates
            for clf in entry.cross_language_forms:
                if clf.is_cognate:
                    cognate_entries = self.search_exact(clf.form)
                    for cog_entry in cognate_entries:
                        cognate_group.setdefault(clf.language, []).append(cog_entry)
        
        return cognate_group
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        stats = {
            'total_entries': len(self.entries),
            'by_type': {},
            'by_language': {},
            'with_etymology': 0,
            'with_phonetic': 0,
            'with_cognates': 0
        }
        
        for entry in self.entries.values():
            # Count by type
            stats['by_type'][entry.name_type] = stats['by_type'].get(entry.name_type, 0) + 1
            
            # Count by language
            if entry.language_origin:
                lang = entry.language_origin.primary_language
                stats['by_language'][lang] = stats['by_language'].get(lang, 0) + 1
            
            # Count features
            if entry.etymology:
                stats['with_etymology'] += 1
            if entry.phonetic:
                stats['with_phonetic'] += 1
            if entry.cross_language_forms:
                stats['with_cognates'] += 1
        
        return stats
    
    # Enrichment Operations
    
    def backup(self) -> Optional[str]:
        """
        Create timestamped backup of JSON file.
        
        Returns:
            Backup file path, or None if no data_file
        """
        if not self.data_file or not self.data_file.exists():
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_path = Path(str(self.data_file) + f'.{timestamp}.bak')
        shutil.copy2(self.data_file, backup_path)
        return str(backup_path)
    
    def merge_geographic_usage(
        self,
        name_id: str,
        usage_entries: List[GeographicUsage],
        merge_strategy: str = "accumulate"
    ) -> None:
        """
        Merge geographic usage entries into existing name.
        
        Args:
            name_id: ID of the name entry
            usage_entries: List of GeographicUsage objects to merge
            merge_strategy: How to merge ("accumulate" or "replace")
            
        Raises:
            ValueError: If entry not found or invalid strategy
        """
        entry = self.entries.get(name_id)
        if not entry:
            raise ValueError(f"Entry {name_id} not found")
        
        if merge_strategy not in ("accumulate", "replace"):
            raise ValueError(f"Invalid merge_strategy: {merge_strategy}")
        
        if merge_strategy == "replace":
            entry.geographic_usage = usage_entries
        else:  # accumulate
            # Build index of existing usage by (location_id, region, country, time_period)
            existing_index = {}
            for gu in entry.geographic_usage:
                key = (gu.location_id, gu.region, gu.country, gu.time_period)
                existing_index[key] = gu
            
            # Merge new entries
            for new_gu in usage_entries:
                key = (new_gu.location_id, new_gu.region, new_gu.country, new_gu.time_period)
                if key in existing_index:
                    # Already exists - preserve (could aggregate counts in future)
                    continue
                else:
                    entry.geographic_usage.append(new_gu)
        
        entry.date_modified = datetime.now()
        self._rebuild_indexes()
    
    def update_fields(self, name_id: str, fields: Dict[str, Any]) -> None:
        """
        Update specific fields of a name entry.
        
        Args:
            name_id: ID of the name entry
            fields: Dict of field names -> values to update
            
        Raises:
            ValueError: If entry not found
        """
        entry = self.entries.get(name_id)
        if not entry:
            raise ValueError(f"Entry {name_id} not found")
        
        # Update allowed fields
        for field_name, value in fields.items():
            if hasattr(entry, field_name):
                setattr(entry, field_name, value)
        
        entry.date_modified = datetime.now()
        self._rebuild_indexes()
