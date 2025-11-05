"""
Location Registry

CRUD operations and search functionality for the Location Registry.

Author: Jane Smith
Date: November 2025
Version: 0.1.0
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from .models import (
    Location, LocationQueryResult, Geocode, LocationHierarchy,
    HistoricalName, LocationCodes, LocationSource, Bounds
)


class LocationRegistry:
    """
    Registry for managing location entries with CRUD operations and search.
    
    Provides:
    - Loading/saving from JSON files
    - CRUD operations (create, read, update, delete)
    - Search by name, hierarchy, coordinates
    - Historical name lookup
    - Hierarchical queries (contained_by/contains)
    
    Example:
        >>> registry = LocationRegistry("/path/to/metadata/data/locations.json")
        >>> registry.load()
        >>> results = registry.search("Harvey")
    """
    
    def __init__(self, data_file: Optional[str] = None):
        """
        Initialize the registry.
        
        Args:
            data_file: Path to JSON data file. If None, uses in-memory only.
        """
        self.data_file = Path(data_file) if data_file else None
        self.locations: Dict[str, Location] = {}
        self._name_index: Dict[str, List[str]] = {}  # name -> [location_ids]
        self._country_index: Dict[str, List[str]] = {}  # country -> [location_ids]
        self._code_index: Dict[str, str] = {}  # code -> location_id
    
    def load(self) -> None:
        """Load locations from JSON file."""
        if not self.data_file or not self.data_file.exists():
            return
        
        with open(self.data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.locations.clear()
        for loc_data in data.get('locations', []):
            location = Location.from_dict(loc_data)
            self.locations[location.location_id] = location
        
        self._rebuild_indexes()
    
    def save(self) -> None:
        """Save locations to JSON file."""
        if not self.data_file:
            raise ValueError("No data file specified")
        
        # Ensure directory exists
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'metadata': {
                'version': '1.0.0',
                'last_updated': datetime.now().isoformat(),
                'total_locations': len(self.locations)
            },
            'locations': [loc.to_dict() for loc in self.locations.values()]
        }
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _rebuild_indexes(self) -> None:
        """Rebuild all search indexes."""
        self._name_index.clear()
        self._country_index.clear()
        self._code_index.clear()
        
        for loc_id, location in self.locations.items():
            # Index modern name
            name_lower = location.modern_name.lower()
            self._name_index.setdefault(name_lower, []).append(loc_id)
            
            # Index historical names
            for hist_name in location.historical_names:
                hist_lower = hist_name.name.lower()
                self._name_index.setdefault(hist_lower, []).append(loc_id)
            
            # Index alternate spellings
            for alt_spelling in location.alternate_spellings:
                alt_lower = alt_spelling.lower()
                self._name_index.setdefault(alt_lower, []).append(loc_id)
            
            # Index by country
            if location.hierarchy and location.hierarchy.country:
                country_lower = location.hierarchy.country.lower()
                self._country_index.setdefault(country_lower, []).append(loc_id)
            
            # Index codes
            if location.codes:
                if location.codes.iso_3166_1:
                    self._code_index[location.codes.iso_3166_1] = loc_id
                if location.codes.iso_3166_2:
                    self._code_index[location.codes.iso_3166_2] = loc_id
                if location.codes.fips:
                    self._code_index[location.codes.fips] = loc_id
    
    # CRUD Operations
    
    def create(self, location: Location) -> Location:
        """
        Create a new location entry.
        
        Args:
            location: Location to add
            
        Returns:
            The created location
            
        Raises:
            ValueError: If location_id already exists
        """
        if location.location_id in self.locations:
            raise ValueError(f"Location with ID {location.location_id} already exists")
        
        self.locations[location.location_id] = location
        self._rebuild_indexes()
        
        return location
    
    def read(self, location_id: str) -> Optional[Location]:
        """
        Read a location by ID.
        
        Args:
            location_id: The location ID
            
        Returns:
            Location if found, None otherwise
        """
        return self.locations.get(location_id)
    
    def update(self, location: Location) -> Location:
        """
        Update an existing location.
        
        Args:
            location: Location with updated data
            
        Returns:
            The updated location
            
        Raises:
            ValueError: If location_id doesn't exist
        """
        if location.location_id not in self.locations:
            raise ValueError(f"Location with ID {location.location_id} not found")
        
        self.locations[location.location_id] = location
        self._rebuild_indexes()
        
        return location
    
    def delete(self, location_id: str) -> bool:
        """
        Delete a location.
        
        Args:
            location_id: The location ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        if location_id in self.locations:
            del self.locations[location_id]
            self._rebuild_indexes()
            return True
        return False
    
    def list_all(
        self,
        admin_type: Optional[str] = None,
        country: Optional[str] = None
    ) -> List[Location]:
        """
        List all locations with optional filters.
        
        Args:
            admin_type: Filter by administrative type
            country: Filter by country
            
        Returns:
            List of matching locations
        """
        results = list(self.locations.values())
        
        if admin_type:
            results = [loc for loc in results if loc.admin_type == admin_type]
        
        if country:
            country_lower = country.lower()
            results = [
                loc for loc in results
                if loc.hierarchy and loc.hierarchy.country and 
                loc.hierarchy.country.lower() == country_lower
            ]
        
        return results
    
    # Search Operations
    
    def search_exact(self, name: str) -> List[Location]:
        """
        Search for exact location name matches (case-insensitive).
        
        Args:
            name: The location name to search for
            
        Returns:
            List of matching locations
        """
        name_lower = name.lower()
        location_ids = self._name_index.get(name_lower, [])
        return [self.locations[lid] for lid in location_ids]
    
    def search_by_code(self, code: str) -> Optional[Location]:
        """
        Search by ISO, FIPS, or other standard code.
        
        Args:
            code: Location code
            
        Returns:
            Location if found, None otherwise
        """
        location_id = self._code_index.get(code)
        return self.locations.get(location_id) if location_id else None
    
    def search_by_hierarchy(
        self,
        locality: Optional[str] = None,
        county: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None
    ) -> List[Location]:
        """
        Search by hierarchical components.
        
        Args:
            locality: Locality/city name
            county: County name
            state: State/province name
            country: Country name
            
        Returns:
            List of matching locations
        """
        results = []
        
        for location in self.locations.values():
            if not location.hierarchy:
                continue
            
            match = True
            
            if locality and (not location.hierarchy.locality or 
                           location.hierarchy.locality.lower() != locality.lower()):
                match = False
            
            if county and (not location.hierarchy.county or
                          location.hierarchy.county.lower() != county.lower()):
                match = False
            
            if state and (not location.hierarchy.state or
                         location.hierarchy.state.lower() != state.lower()):
                match = False
            
            if country and (not location.hierarchy.country or
                           location.hierarchy.country.lower() != country.lower()):
                match = False
            
            if match:
                results.append(location)
        
        return results
    
    def search_by_coordinates(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0
    ) -> List[Tuple[Location, float]]:
        """
        Search for locations near coordinates.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            radius_km: Search radius in kilometers
            
        Returns:
            List of (Location, distance_km) tuples within radius
        """
        from math import radians, cos, sin, asin, sqrt
        
        results = []
        
        for location in self.locations.values():
            if not location.has_coordinates():
                continue
            
            # Calculate distance using Haversine formula
            lat1, lon1 = radians(latitude), radians(longitude)
            lat2 = radians(location.geocode.latitude)
            lon2 = radians(location.geocode.longitude)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            distance = 6371 * c  # Earth radius in km
            
            if distance <= radius_km:
                results.append((location, distance))
        
        # Sort by distance
        results.sort(key=lambda x: x[1])
        
        return results
    
    def search(
        self,
        query: str,
        include_historical: bool = True,
        country: Optional[str] = None
    ) -> List[LocationQueryResult]:
        """
        Comprehensive search with confidence scoring.
        
        Args:
            query: Search query
            include_historical: Include historical names
            country: Optional country filter
            
        Returns:
            List of LocationQueryResult ordered by confidence
        """
        from difflib import SequenceMatcher
        
        results = []
        seen_ids = set()
        
        # Exact matches (highest confidence)
        for location in self.search_exact(query):
            if country and (not location.hierarchy or 
                          not location.hierarchy.country or
                          location.hierarchy.country.lower() != country.lower()):
                continue
            
            if location.location_id not in seen_ids:
                # Determine match type
                match_type = "exact"
                if include_historical:
                    for hist in location.historical_names:
                        if hist.name.lower() == query.lower():
                            match_type = "historical"
                            break
                
                results.append(LocationQueryResult(location, 1.0, match_type))
                seen_ids.add(location.location_id)
        
        # Fuzzy matches for remaining locations
        query_lower = query.lower()
        for location in self.locations.values():
            if location.location_id in seen_ids:
                continue
            
            if country and (not location.hierarchy or
                          not location.hierarchy.country or
                          location.hierarchy.country.lower() != country.lower()):
                continue
            
            # Check modern name similarity
            similarity = SequenceMatcher(
                None, query_lower, location.modern_name.lower()
            ).ratio()
            
            if similarity >= 0.7:
                confidence = 0.5 + (similarity - 0.7) / 0.3 * 0.3
                results.append(LocationQueryResult(location, confidence, "fuzzy"))
                seen_ids.add(location.location_id)
        
        # Sort by confidence
        results.sort(key=lambda r: r.confidence, reverse=True)
        
        return results
    
    def find_contained_by(self, location_id: str) -> List[Location]:
        """
        Find parent locations (administrative hierarchy).
        
        Args:
            location_id: Location to find parents for
            
        Returns:
            List of parent locations
        """
        location = self.read(location_id)
        if not location:
            return []
        
        return [
            self.locations[parent_id]
            for parent_id in location.contained_by
            if parent_id in self.locations
        ]
    
    def find_contains(self, location_id: str) -> List[Location]:
        """
        Find child locations.
        
        Args:
            location_id: Location to find children for
            
        Returns:
            List of child locations
        """
        location = self.read(location_id)
        if not location:
            return []
        
        return [
            self.locations[child_id]
            for child_id in location.contains
            if child_id in self.locations
        ]
    
    def find_by_country(self, country: str) -> List[Location]:
        """
        Find all locations in a country.
        
        Args:
            country: Country name
            
        Returns:
            List of locations in that country
        """
        country_lower = country.lower()
        location_ids = self._country_index.get(country_lower, [])
        return [self.locations[lid] for lid in location_ids]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        stats = {
            'total_locations': len(self.locations),
            'by_admin_type': {},
            'by_country': {},
            'with_coordinates': 0,
            'with_historical_names': 0,
            'by_admin_level': {}
        }
        
        for location in self.locations.values():
            # Count by admin type
            if location.admin_type:
                stats['by_admin_type'][location.admin_type] = \
                    stats['by_admin_type'].get(location.admin_type, 0) + 1
            
            # Count by country
            if location.hierarchy and location.hierarchy.country:
                country = location.hierarchy.country
                stats['by_country'][country] = stats['by_country'].get(country, 0) + 1
            
            # Count by admin level
            if location.admin_level is not None:
                level = str(location.admin_level)
                stats['by_admin_level'][level] = \
                    stats['by_admin_level'].get(level, 0) + 1
            
            # Count features
            if location.has_coordinates():
                stats['with_coordinates'] += 1
            if location.historical_names:
                stats['with_historical_names'] += 1
        
        return stats
