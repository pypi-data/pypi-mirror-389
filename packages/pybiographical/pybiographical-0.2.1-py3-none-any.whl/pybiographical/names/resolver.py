"""
Name Resolver

High-level utilities for resolving names across languages, fuzzy matching,
and phonetic search using the Names Registry.

Author: Jane Smith
Date: November 2025
Version: 0.1.0
"""

from typing import List, Optional, Dict, Any, Tuple
from difflib import SequenceMatcher

from .models import NameEntry, NameQueryResult
from .registry import NameRegistry


class NameResolver:
    """
    High-level name resolution utility.
    
    Provides convenient methods for:
    - Cross-language name resolution
    - Fuzzy name matching
    - Phonetic searches
    - Etymology-based lookups
    - Cognate discovery
    
    Example:
        >>> resolver = NameResolver(registry)
        >>> results = resolver.resolve("Schmidt", fuzzy=True, cross_language=True)
        >>> cognates = resolver.get_all_cognates("Smith")
    """
    
    def __init__(self, registry: NameRegistry):
        """
        Initialize resolver with a registry.
        
        Args:
            registry: NameRegistry instance
        """
        self.registry = registry
    
    def resolve(
        self,
        name: str,
        name_type: Optional[str] = None,
        fuzzy: bool = False,
        cross_language: bool = True,
        fuzzy_threshold: float = 0.7
    ) -> List[NameQueryResult]:
        """
        Resolve a name with various matching strategies.
        
        Args:
            name: Name to resolve
            name_type: Filter by name type (given, surname, etc.)
            fuzzy: Enable fuzzy matching
            cross_language: Include cross-language cognates
            fuzzy_threshold: Minimum similarity score (0.0-1.0)
            
        Returns:
            List of NameQueryResult ordered by confidence
        """
        results = []
        
        # Start with exact/variant/cognate search
        results = self.registry.search(
            name,
            include_variants=True,
            include_cognates=cross_language,
            name_type=name_type
        )
        
        # Add fuzzy matches if enabled
        if fuzzy:
            seen_ids = {r.entry.id for r in results}
            fuzzy_results = self._fuzzy_search(
                name,
                name_type=name_type,
                threshold=fuzzy_threshold,
                exclude_ids=seen_ids
            )
            results.extend(fuzzy_results)
        
        # Sort by confidence
        results.sort(key=lambda r: r.confidence, reverse=True)
        
        return results
    
    def _fuzzy_search(
        self,
        name: str,
        name_type: Optional[str] = None,
        threshold: float = 0.7,
        exclude_ids: Optional[set] = None
    ) -> List[NameQueryResult]:
        """
        Fuzzy string matching against all names.
        
        Args:
            name: Search query
            name_type: Optional type filter
            threshold: Minimum similarity score
            exclude_ids: Set of entry IDs to exclude
            
        Returns:
            List of fuzzy match results
        """
        results = []
        exclude = exclude_ids or set()
        name_lower = name.lower()
        
        for entry in self.registry.list_all(name_type=name_type):
            if entry.id in exclude:
                continue
            
            # Check primary name
            similarity = SequenceMatcher(None, name_lower, entry.name.lower()).ratio()
            
            if similarity >= threshold:
                # Scale confidence based on similarity
                confidence = 0.5 + (similarity - threshold) / (1.0 - threshold) * 0.3
                results.append(NameQueryResult(entry, confidence, "fuzzy"))
        
        return results
    
    def resolve_to_language(
        self,
        name: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> List[Tuple[NameEntry, float]]:
        """
        Resolve a name to its form in a target language.
        
        Args:
            name: Name to resolve
            target_language: Target language (e.g., "English", "German")
            source_language: Optional source language hint
            
        Returns:
            List of (NameEntry, confidence) tuples for target language
        """
        # Find the source entry
        source_entries = self.registry.search_exact(name)
        
        if source_language:
            source_entries = [
                e for e in source_entries
                if e.language_origin and e.language_origin.primary_language.lower() == source_language.lower()
            ]
        
        if not source_entries:
            return []
        
        results = []
        
        for source_entry in source_entries:
            # Check if target language matches primary language
            if source_entry.language_origin and source_entry.language_origin.primary_language.lower() == target_language.lower():
                results.append((source_entry, 1.0))
                continue
            
            # Check cross-language forms
            for clf in source_entry.cross_language_forms:
                if clf.language.lower() == target_language.lower():
                    # Try to find the full entry for this form
                    target_entries = self.registry.search_exact(clf.form)
                    for target_entry in target_entries:
                        if target_entry.language_origin and target_entry.language_origin.primary_language.lower() == target_language.lower():
                            confidence = 0.95 if clf.is_cognate else 0.85
                            results.append((target_entry, confidence))
        
        # Sort by confidence
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    def get_all_cognates(self, name: str) -> Dict[str, List[NameEntry]]:
        """
        Get all cognate forms of a name grouped by language.
        
        Args:
            name: Name to find cognates for
            
        Returns:
            Dict mapping language to list of entries
        """
        return self.registry.find_cognate_group(name)
    
    def find_by_meaning(
        self,
        meaning: str,
        name_type: Optional[str] = None,
        language: Optional[str] = None
    ) -> List[NameEntry]:
        """
        Find names by etymological meaning.
        
        Args:
            meaning: Search term (e.g., "metalworker", "blacksmith")
            name_type: Optional filter by type
            language: Optional filter by language
            
        Returns:
            List of matching entries
        """
        results = self.registry.find_by_etymology(meaning)
        
        # Apply filters
        if name_type:
            results = [e for e in results if e.name_type == name_type]
        
        if language:
            results = [
                e for e in results
                if e.language_origin and e.language_origin.primary_language.lower() == language.lower()
            ]
        
        return results
    
    def find_occupational_surnames(self, occupation: str) -> List[NameEntry]:
        """
        Find surnames related to an occupation across languages.
        
        Args:
            occupation: Occupation term (e.g., "smith", "baker", "miller")
            
        Returns:
            List of surname entries
        """
        return self.find_by_meaning(occupation, name_type="surname")
    
    def suggest_variants(self, name: str, max_results: int = 10) -> List[NameQueryResult]:
        """
        Suggest possible name variants using fuzzy matching.
        
        Args:
            name: Name to find variants for
            max_results: Maximum number of suggestions
            
        Returns:
            List of suggested variants
        """
        results = self.resolve(
            name,
            fuzzy=True,
            cross_language=True,
            fuzzy_threshold=0.6
        )
        
        return results[:max_results]
    
    def phonetic_match(
        self,
        name: str,
        method: str = "soundex"
    ) -> List[NameEntry]:
        """
        Find names with matching phonetic encoding.
        
        Args:
            name: Name to match phonetically
            method: Phonetic method (soundex, metaphone, etc.)
            
        Returns:
            List of phonetically matching entries
        """
        # First, find an entry with this name to get its phonetic encoding
        entries = self.registry.search_exact(name)
        
        if not entries:
            return []
        
        # Get phonetic encodings from the first entry
        phonetic_codes = [
            p.value for p in entries[0].phonetic
            if p.method == method
        ]
        
        if not phonetic_codes:
            return []
        
        # Search for all entries with matching codes
        results = []
        for code in phonetic_codes:
            results.extend(self.registry.search_phonetic(code, method))
        
        # Remove duplicates
        seen = set()
        unique_results = []
        for entry in results:
            if entry.id not in seen:
                unique_results.append(entry)
                seen.add(entry.id)
        
        return unique_results
    
    def compare_names(self, name1: str, name2: str) -> Dict[str, Any]:
        """
        Compare two names and return relationship information.
        
        Args:
            name1: First name
            name2: Second name
            
        Returns:
            Dict with comparison results including:
            - are_cognates: bool
            - similarity_score: float
            - shared_etymology: bool
            - relationship_description: str
        """
        entries1 = self.registry.search_exact(name1)
        entries2 = self.registry.search_exact(name2)
        
        if not entries1 or not entries2:
            return {
                'are_cognates': False,
                'similarity_score': 0.0,
                'shared_etymology': False,
                'relationship_description': 'One or both names not found'
            }
        
        entry1 = entries1[0]
        entry2 = entries2[0]
        
        # Check if cognates
        are_cognates = any(
            clf.form.lower() == name2.lower() and clf.is_cognate
            for clf in entry1.cross_language_forms
        ) or any(
            clf.form.lower() == name1.lower() and clf.is_cognate
            for clf in entry2.cross_language_forms
        )
        
        # Calculate similarity
        similarity = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
        
        # Check shared etymology
        shared_etymology = False
        if entry1.etymology and entry2.etymology:
            # Check if meanings overlap
            if entry1.etymology.meaning and entry2.etymology.meaning:
                shared_etymology = (
                    entry1.etymology.meaning.lower() in entry2.etymology.meaning.lower() or
                    entry2.etymology.meaning.lower() in entry1.etymology.meaning.lower()
                )
        
        # Build relationship description
        if are_cognates:
            desc = f"'{name1}' and '{name2}' are cognates across languages"
        elif shared_etymology:
            desc = f"'{name1}' and '{name2}' share etymological roots"
        elif similarity > 0.8:
            desc = f"'{name1}' and '{name2}' are likely spelling variants"
        else:
            desc = f"'{name1}' and '{name2}' appear to be distinct names"
        
        return {
            'are_cognates': are_cognates,
            'similarity_score': similarity,
            'shared_etymology': shared_etymology,
            'relationship_description': desc
        }
    
    def get_name_summary(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a comprehensive summary of a name.
        
        Args:
            name: Name to summarize
            
        Returns:
            Dict with name information or None if not found
        """
        entries = self.registry.search_exact(name)
        
        if not entries:
            return None
        
        entry = entries[0]
        
        summary = {
            'name': entry.name,
            'type': entry.name_type,
            'language': entry.language_origin.primary_language if entry.language_origin else None,
            'language_family': entry.language_origin.language_family if entry.language_origin else None,
            'meaning': entry.etymology.meaning if entry.etymology else None,
            'english_translation': entry.etymology.english_translation if entry.etymology else None,
            'spelling_variants': [v.form for v in entry.spelling_variants],
            'cognates': {},
            'geographic_usage': []
        }
        
        # Add cognates
        for clf in entry.cross_language_forms:
            if clf.is_cognate:
                summary['cognates'][clf.language] = clf.form
        
        # Add geographic usage
        for geo in entry.geographic_usage:
            summary['geographic_usage'].append({
                'region': geo.region,
                'country': geo.country,
                'time_period': geo.time_period,
                'frequency': geo.frequency
            })
        
        return summary
