"""
Names Registry Module

Centralized NAME (not person) management system for genealogical data.

This module manages information about NAMES themselves:
- Given names, middle names, and surnames
- Cross-language name resolution and cognates
- Etymology and meaning
- Regional and historical usage patterns
- Phonetic encodings for matching
- Historical name change events (family-level)

Note: Person-specific data (nicknames, aliases, preferred names) 
belongs in person/individual records, not in this registry.

Author: Jane Smith
Date: November 2025
Version: 0.1.0
"""

from .models import NameEntry, LanguageOrigin, EtymologyInfo, GeographicUsage
from .registry import NameRegistry
from .resolver import NameResolver

__version__ = "0.1.0"

__all__ = [
    "NameEntry",
    "LanguageOrigin",
    "EtymologyInfo",
    "GeographicUsage",
    "NameRegistry",
    "NameResolver",
]
