"""
Location Registry Data Models

Dataclasses matching the structure of metadata/data/locations.json

Author: Jane Smith
Date: November 2025
Version: 0.1.0
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Bounds:
    """Geographic bounding box."""
    south: float
    north: float
    west: float
    east: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'south': self.south,
            'north': self.north,
            'west': self.west,
            'east': self.east
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Bounds':
        return cls(
            south=data['south'],
            north=data['north'],
            west=data['west'],
            east=data['east']
        )


@dataclass
class Geocode:
    """Geographic coordinates and accuracy information."""
    latitude: float
    longitude: float
    accuracy: str  # unknown, approximate, precise
    bounds: Optional[Bounds] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'accuracy': self.accuracy
        }
        if self.bounds:
            result['bounds'] = self.bounds.to_dict()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Geocode':
        bounds = None
        if 'bounds' in data and data['bounds']:
            bounds = Bounds.from_dict(data['bounds'])
        
        return cls(
            latitude=data['latitude'],
            longitude=data['longitude'],
            accuracy=data.get('accuracy', 'unknown'),
            bounds=bounds
        )


@dataclass
class LocationHierarchy:
    """Hierarchical location structure (locality -> county -> state -> country)."""
    locality: Optional[str] = None
    county: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None  # ISO 3166-1 alpha-2
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'locality': self.locality,
            'county': self.county,
            'state': self.state,
            'country': self.country,
            'country_code': self.country_code
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LocationHierarchy':
        return cls(
            locality=data.get('locality'),
            county=data.get('county'),
            state=data.get('state'),
            country=data.get('country'),
            country_code=data.get('country_code')
        )


@dataclass
class HistoricalName:
    """Historical name of a location at a specific time period."""
    name: str
    date_range: str
    civilization: Optional[str] = None
    note: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'date_range': self.date_range,
            'civilization': self.civilization,
            'note': self.note
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoricalName':
        return cls(
            name=data['name'],
            date_range=data['date_range'],
            civilization=data.get('civilization'),
            note=data.get('note')
        )


@dataclass
class LocationCodes:
    """Standard location codes."""
    iso_3166_1: Optional[str] = None  # Country code
    iso_3166_2: Optional[str] = None  # Subdivision code
    fips: Optional[str] = None  # FIPS code
    osm_id: Optional[str] = None  # OpenStreetMap ID
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'iso_3166_1': self.iso_3166_1,
            'iso_3166_2': self.iso_3166_2,
            'fips': self.fips,
            'osm_id': self.osm_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LocationCodes':
        return cls(
            iso_3166_1=data.get('iso_3166_1'),
            iso_3166_2=data.get('iso_3166_2'),
            fips=data.get('fips'),
            osm_id=data.get('osm_id')
        )


@dataclass
class LocationSource:
    """Source information for geocoded data."""
    geocoder: str
    query: str
    provider_id: Optional[str] = None
    licence: Optional[str] = None
    timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'geocoder': self.geocoder,
            'query': self.query,
            'provider_id': self.provider_id,
            'licence': self.licence,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LocationSource':
        return cls(
            geocoder=data['geocoder'],
            query=data['query'],
            provider_id=data.get('provider_id'),
            licence=data.get('licence'),
            timestamp=data.get('timestamp')
        )


@dataclass
class Location:
    """
    Complete location entry matching metadata/data/locations.json structure.
    
    Represents a geographic location with:
    - Modern and historical names
    - Geographic coordinates and boundaries
    - Administrative hierarchy
    - Relationships to other locations
    - Standard codes and source information
    
    Example:
        >>> loc = Location(
        ...     location_id="LOC-00001",
        ...     modern_name="Harvey, Wells County, North Dakota, USA",
        ...     geocode=Geocode(47.78, -99.93, "precise")
        ... )
    """
    
    location_id: str
    modern_name: str
    
    # Optional fields
    admin_level: Optional[int] = None
    admin_type: Optional[str] = None
    historical_names: List[HistoricalName] = field(default_factory=list)
    geocode: Optional[Geocode] = None
    hierarchy: Optional[LocationHierarchy] = None
    contained_by: List[str] = field(default_factory=list)  # Parent location IDs
    contains: List[str] = field(default_factory=list)  # Child location IDs
    alternate_spellings: List[str] = field(default_factory=list)
    codes: Optional[LocationCodes] = None
    source: Optional[LocationSource] = None
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {
            'location_id': self.location_id,
            'modern_name': self.modern_name,
            'admin_level': self.admin_level,
            'admin_type': self.admin_type
        }
        
        if self.historical_names:
            data['historical_names'] = [hn.to_dict() for hn in self.historical_names]
        
        if self.geocode:
            data['geocode'] = self.geocode.to_dict()
        
        if self.hierarchy:
            data['hierarchy'] = self.hierarchy.to_dict()
        
        data['contained_by'] = self.contained_by
        data['contains'] = self.contains
        data['alternate_spellings'] = self.alternate_spellings
        
        if self.codes:
            data['codes'] = self.codes.to_dict()
        
        if self.source:
            data['source'] = self.source.to_dict()
        
        data['notes'] = self.notes
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Location':
        """Create Location from dictionary."""
        # Parse historical names
        historical_names = []
        if 'historical_names' in data:
            historical_names = [
                HistoricalName.from_dict(hn) 
                for hn in data['historical_names']
            ]
        
        # Parse geocode
        geocode = None
        if 'geocode' in data and data['geocode']:
            geocode = Geocode.from_dict(data['geocode'])
        
        # Parse hierarchy
        hierarchy = None
        if 'hierarchy' in data and data['hierarchy']:
            hierarchy = LocationHierarchy.from_dict(data['hierarchy'])
        
        # Parse codes
        codes = None
        if 'codes' in data and data['codes']:
            codes = LocationCodes.from_dict(data['codes'])
        
        # Parse source
        source = None
        if 'source' in data and data['source']:
            source = LocationSource.from_dict(data['source'])
        
        return cls(
            location_id=data['location_id'],
            modern_name=data['modern_name'],
            admin_level=data.get('admin_level'),
            admin_type=data.get('admin_type'),
            historical_names=historical_names,
            geocode=geocode,
            hierarchy=hierarchy,
            contained_by=data.get('contained_by', []),
            contains=data.get('contains', []),
            alternate_spellings=data.get('alternate_spellings', []),
            codes=codes,
            source=source,
            notes=data.get('notes', '')
        )
    
    def get_display_name(self, include_country: bool = True) -> str:
        """Get a formatted display name."""
        if not self.hierarchy:
            return self.modern_name
        
        parts = []
        if self.hierarchy.locality:
            parts.append(self.hierarchy.locality)
        if self.hierarchy.county:
            parts.append(self.hierarchy.county)
        if self.hierarchy.state:
            parts.append(self.hierarchy.state)
        if include_country and self.hierarchy.country:
            parts.append(self.hierarchy.country)
        
        return ", ".join(parts) if parts else self.modern_name
    
    def has_coordinates(self) -> bool:
        """Check if location has geocode coordinates."""
        return self.geocode is not None
    
    def distance_to(self, other: 'Location') -> Optional[float]:
        """
        Calculate distance to another location in kilometers.
        Returns None if either location lacks coordinates.
        """
        if not self.has_coordinates() or not other.has_coordinates():
            return None
        
        from math import radians, cos, sin, asin, sqrt
        
        # Haversine formula
        lat1, lon1 = radians(self.geocode.latitude), radians(self.geocode.longitude)
        lat2, lon2 = radians(other.geocode.latitude), radians(other.geocode.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r


@dataclass
class LocationQueryResult:
    """Result of a location query with match confidence."""
    location: Location
    confidence: float  # 0.0 to 1.0
    match_type: str  # exact, fuzzy, historical, hierarchical
    
    def __str__(self) -> str:
        return f"LocationQueryResult(location_id={self.location.location_id}, name={self.location.modern_name}, confidence={self.confidence:.2f})"
