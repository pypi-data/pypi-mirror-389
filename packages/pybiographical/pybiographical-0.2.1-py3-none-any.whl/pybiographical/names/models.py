"""
Name Registry Data Models

Dataclasses for representing name entries with all associated metadata.

Author: Jane Smith
Date: November 2025
Version: 0.1.0
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class LanguageOrigin:
    """Language origin information for a name."""
    primary_language: str
    language_family: Optional[str] = None
    origin_period: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'primary_language': self.primary_language,
            'language_family': self.language_family,
            'origin_period': self.origin_period
        }


@dataclass
class CrossLanguageForm:
    """Name form in a different language."""
    form: str
    language: str
    script: Optional[str] = None
    is_cognate: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'form': self.form,
            'language': self.language,
            'script': self.script,
            'is_cognate': self.is_cognate
        }


@dataclass
class SpellingVariant:
    """Spelling variation of a name."""
    form: str
    context: Optional[str] = None
    time_period: Optional[str] = None
    region: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'form': self.form,
            'context': self.context,
            'time_period': self.time_period,
            'region': self.region
        }


@dataclass
class RootWord:
    """Etymological root component."""
    word: str
    meaning: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'word': self.word,
            'meaning': self.meaning
        }


@dataclass
class EtymologyInfo:
    """Etymology and meaning information."""
    meaning: Optional[str] = None
    english_translation: Optional[str] = None
    origin_language: Optional[str] = None
    root_words: List[RootWord] = field(default_factory=list)
    historical_context: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'meaning': self.meaning,
            'english_translation': self.english_translation,
            'origin_language': self.origin_language,
            'root_words': [rw.to_dict() for rw in self.root_words],
            'historical_context': self.historical_context
        }


@dataclass
class GeographicUsage:
    """Geographic and temporal usage information."""
    region: str
    country: Optional[str] = None
    time_period: Optional[str] = None
    frequency: Optional[str] = None
    location_id: Optional[str] = None  # Reference to metadata/data/locations.json
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'location_id': self.location_id,
            'region': self.region,
            'country': self.country,
            'time_period': self.time_period,
            'frequency': self.frequency
        }


@dataclass
class PhoneticEncoding:
    """Phonetic encoding of a name."""
    value: str
    method: str  # soundex, metaphone, IPA, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'value': self.value,
            'method': self.method
        }


@dataclass
class NameChangeEvent:
    """
    Records a deliberate name change event.
    
    Tracks intentional name changes within families, often for social,
    political, or cultural reasons.
    
    Example:
        >>> change = NameChangeEvent(
        ...     from_name="Lindemann",
        ...     to_name="Lindeman",
        ...     date="1945",
        ...     person_id="PERSON-123",
        ...     reason="Anglicization after WWII to sound less German"
        ... )
    """
    from_name: str
    to_name: str
    date: Optional[str] = None  # ISO date or year
    person_id: Optional[str] = None  # Reference to person who changed it
    person_name: Optional[str] = None  # Name of person (if no ID available)
    reason: Optional[str] = None
    reason_category: Optional[str] = None  # immigration, war, marriage, simplification, etc.
    location: Optional[str] = None  # Where the change occurred
    location_id: Optional[str] = None  # Reference to location
    documentation: Optional[str] = None  # Court records, immigration papers, etc.
    affected_descendants: bool = True  # Whether descendants also use new spelling
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'from_name': self.from_name,
            'to_name': self.to_name,
            'date': self.date,
            'person_id': self.person_id,
            'person_name': self.person_name,
            'reason': self.reason,
            'reason_category': self.reason_category,
            'location': self.location,
            'location_id': self.location_id,
            'documentation': self.documentation,
            'affected_descendants': self.affected_descendants,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NameChangeEvent':
        return cls(
            from_name=data['from_name'],
            to_name=data['to_name'],
            date=data.get('date'),
            person_id=data.get('person_id'),
            person_name=data.get('person_name'),
            reason=data.get('reason'),
            reason_category=data.get('reason_category'),
            location=data.get('location'),
            location_id=data.get('location_id'),
            documentation=data.get('documentation'),
            affected_descendants=data.get('affected_descendants', True),
            notes=data.get('notes')
        )


@dataclass
class NameEntry:
    """
    Complete name entry with all associated metadata.
    
    Represents a single NAME (not a person) with:
    - Language origin and cross-language forms
    - Spelling variants and phonetic encodings
    - Etymology and meaning
    - Geographic and temporal usage patterns
    - Historical name change events (family-level)
    
    Note: This is about the NAME itself, not individuals who use it.
    Person-specific data (nicknames, aliases, preferred names) belongs
    in person/individual records, not here.
    
    Example:
        >>> entry = NameEntry(
        ...     id="name-besuchet-001",
        ...     name="besuchet",
        ...     name_type="surname",
        ...     language_origin=LanguageOrigin("French", "Romance")
        ... )
    """
    
    id: str
    name: str
    name_type: str  # given, middle, surname, patronymic, prefix
    
    # Optional fields
    language_origin: Optional[LanguageOrigin] = None
    cross_language_forms: List[CrossLanguageForm] = field(default_factory=list)
    spelling_variants: List[SpellingVariant] = field(default_factory=list)
    etymology: Optional[EtymologyInfo] = None
    geographic_usage: List[GeographicUsage] = field(default_factory=list)
    phonetic: List[PhoneticEncoding] = field(default_factory=list)
    name_changes: List[NameChangeEvent] = field(default_factory=list)
    notes: Optional[str] = None
    
    # Confidence scoring
    confidence: Optional[float] = None  # 0.0-1.0 confidence this is a valid name
    confidence_factors: Optional[Dict[str, Any]] = None  # scoring breakdown
    
    # Metadata
    date_added: Optional[datetime] = None
    date_modified: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {
            'id': self.id,
            'name': self.name,
            'name_type': self.name_type
        }
        
        if self.language_origin:
            data['language_origin'] = self.language_origin.to_dict()
        
        if self.cross_language_forms:
            data['cross_language_forms'] = [
                clf.to_dict() for clf in self.cross_language_forms
            ]
        
        if self.spelling_variants:
            data['spelling_variants'] = [
                sv.to_dict() for sv in self.spelling_variants
            ]
        
        if self.etymology:
            data['etymology'] = self.etymology.to_dict()
        
        if self.geographic_usage:
            data['geographic_usage'] = [
                gu.to_dict() for gu in self.geographic_usage
            ]
        
        if self.phonetic:
            data['phonetic'] = [p.to_dict() for p in self.phonetic]
        
        if self.name_changes:
            data['name_changes'] = [nc.to_dict() for nc in self.name_changes]
        
        if self.notes:
            data['notes'] = self.notes
        
        if self.date_added:
            data['date_added'] = self.date_added.isoformat()
        
        if self.date_modified:
            data['date_modified'] = self.date_modified.isoformat()
        
        if self.confidence is not None:
            data['confidence'] = self.confidence
        
        if self.confidence_factors:
            data['confidence_factors'] = self.confidence_factors
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NameEntry':
        """Create NameEntry from dictionary."""
        # Parse language origin
        lang_origin = None
        if 'language_origin' in data:
            lo = data['language_origin']
            lang_origin = LanguageOrigin(
                primary_language=lo['primary_language'],
                language_family=lo.get('language_family'),
                origin_period=lo.get('origin_period')
            )
        
        # Parse cross-language forms
        cross_lang = []
        if 'cross_language_forms' in data:
            cross_lang = [
                CrossLanguageForm(
                    form=clf['form'],
                    language=clf['language'],
                    script=clf.get('script'),
                    is_cognate=clf.get('is_cognate', False)
                )
                for clf in data['cross_language_forms']
            ]
        
        # Parse spelling variants
        spell_var = []
        if 'spelling_variants' in data:
            spell_var = [
                SpellingVariant(
                    form=sv['form'],
                    context=sv.get('context'),
                    time_period=sv.get('time_period'),
                    region=sv.get('region')
                )
                for sv in data['spelling_variants']
            ]
        
        # Parse etymology
        etym = None
        if 'etymology' in data:
            e = data['etymology']
            root_words = []
            if 'root_words' in e:
                root_words = [
                    RootWord(word=rw['word'], meaning=rw['meaning'])
                    for rw in e['root_words']
                ]
            etym = EtymologyInfo(
                meaning=e.get('meaning'),
                english_translation=e.get('english_translation'),
                origin_language=e.get('origin_language'),
                root_words=root_words,
                historical_context=e.get('historical_context')
            )
        
        # Parse geographic usage
        geo_usage = []
        if 'geographic_usage' in data:
            geo_usage = [
                GeographicUsage(
                    region=gu['region'],
                    country=gu.get('country'),
                    time_period=gu.get('time_period'),
                    frequency=gu.get('frequency'),
                    location_id=gu.get('location_id')
                )
                for gu in data['geographic_usage']
            ]
        
        # Parse phonetic
        phonetic = []
        if 'phonetic' in data:
            phonetic = [
                PhoneticEncoding(value=p['value'], method=p['method'])
                for p in data['phonetic']
            ]
        
        # Parse name changes
        name_changes = []
        if 'name_changes' in data:
            name_changes = [
                NameChangeEvent.from_dict(nc)
                for nc in data['name_changes']
            ]
        
        # Parse dates
        date_added = None
        if 'date_added' in data:
            date_added = datetime.fromisoformat(data['date_added'])
        
        date_modified = None
        if 'date_modified' in data:
            date_modified = datetime.fromisoformat(data['date_modified'])
        
        # Parse confidence
        confidence = data.get('confidence')
        confidence_factors = data.get('confidence_factors')
        
        return cls(
            id=data['id'],
            name=data['name'],
            name_type=data['name_type'],
            language_origin=lang_origin,
            cross_language_forms=cross_lang,
            spelling_variants=spell_var,
            etymology=etym,
            geographic_usage=geo_usage,
            phonetic=phonetic,
            name_changes=name_changes,
            notes=data.get('notes'),
            confidence=confidence,
            confidence_factors=confidence_factors,
            date_added=date_added,
            date_modified=date_modified
        )


@dataclass
class NameQueryResult:
    """Result of a name query with match confidence."""
    entry: NameEntry
    confidence: float  # 0.0 to 1.0 (match confidence)
    match_type: str  # exact, phonetic, variant, fuzzy
    name_confidence: Optional[float] = None  # 0.0 to 1.0 (name validity confidence)
    
    def __str__(self) -> str:
        if self.name_confidence is not None:
            return f"NameQueryResult(name={self.entry.name}, match={self.confidence:.2f}, name_conf={self.name_confidence:.2f}, type={self.match_type})"
        return f"NameQueryResult(name={self.entry.name}, confidence={self.confidence:.2f}, match_type={self.match_type})"
