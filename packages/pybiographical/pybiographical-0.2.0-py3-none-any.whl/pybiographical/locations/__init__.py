"""
Locations Registry Module

Centralized location management system for genealogical data with:
- Location CRUD operations
- Hierarchical location relationships
- Geocoding support
- Historical name tracking
- Location search and resolution

Author: Jane Smith
Date: November 2025
Version: 0.1.0
"""

from .models import (
    Location,
    Geocode,
    LocationHierarchy,
    HistoricalName,
    LocationSource
)
from .registry import LocationRegistry

__version__ = "0.1.0"

__all__ = [
    "Location",
    "Geocode",
    "LocationHierarchy",
    "HistoricalName",
    "LocationSource",
    "LocationRegistry",
]
