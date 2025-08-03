"""
Property Deduplication and Standardization System
Identifies duplicate properties across multiple sources and merges/standardizes the data.
"""

import re
import hashlib
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import difflib
import sys
import os

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from backend.models.property import Property

@dataclass
class PropertyMatch:
    """Represents a match between properties from different sources."""
    property1: Property
    property2: Property
    match_score: float
    match_criteria: List[str]
    confidence: str  # 'high', 'medium', 'low'

@dataclass
class DeduplicationResult:
    """Result of the deduplication process."""
    unique_properties: List[Property]
    duplicates_found: int
    matches: List[PropertyMatch]
    standardization_changes: Dict[str, int]
    processing_time_ms: int

class PropertyDeduplicator:
    """
    Handles deduplication and standardization of property listings from multiple sources.
    Uses various matching algorithms to identify duplicates and merge information.
    """
    
    def __init__(self, 
                 address_similarity_threshold: float = 0.85,
                 price_tolerance_percent: float = 5.0,
                 coordinate_tolerance_meters: float = 50.0):
        """
        Initialize the deduplicator.
        
        Args:
            address_similarity_threshold: Minimum similarity score for address matching (0-1)
            price_tolerance_percent: Acceptable price difference percentage
            coordinate_tolerance_meters: GPS coordinate tolerance in meters
        """
        self.address_similarity_threshold = address_similarity_threshold
        self.price_tolerance_percent = price_tolerance_percent
        self.coordinate_tolerance_meters = coordinate_tolerance_meters
        
        # Standardization mappings
        self.property_type_mapping = self._load_property_type_mapping()
        self.suburb_aliases = self._load_suburb_aliases()
        
    def _load_property_type_mapping(self) -> Dict[str, str]:
        """Load property type standardization mapping."""
        return {
            # Apartment variations
            "apartment": "Apartment / Unit / Flat",
            "unit": "Apartment / Unit / Flat", 
            "flat": "Apartment / Unit / Flat",
            "apt": "Apartment / Unit / Flat",
            "condo": "Apartment / Unit / Flat",
            "condominium": "Apartment / Unit / Flat",
            "studio apartment": "Studio",
            "studio unit": "Studio",
            
            # House variations
            "house": "House",
            "home": "House",
            "detached house": "House",
            "family home": "House",
            "residence": "House",
            "dwelling": "House",
            
            # Townhouse variations
            "townhouse": "Townhouse",
            "town house": "Townhouse",
            "terrace": "Townhouse",
            "terrace house": "Townhouse",
            "row house": "Townhouse",
            
            # Villa variations
            "villa": "Villa",
            "villas": "Villa",
            
            # Other types
            "studio": "Studio",
            "penthouse": "Penthouse",
            "duplex": "Duplex",
            "retirement living": "Retirement Living",
            "serviced apartment": "Serviced Apartment"
        }
    
    def _load_suburb_aliases(self) -> Dict[str, List[str]]:
        """Load suburb name aliases and variations."""
        return {
            "Bondi": ["Bondi Beach", "North Bondi"],
            "Sydney": ["Sydney CBD", "Sydney City", "City"],
            "Parramatta": ["Parramatta CBD", "Parramatta City"],
            "Chatswood": ["Chatswood West"],
            "Lane Cove": ["Lane Cove North", "Lane Cove West"],
            # Add more as needed
        }
    
    def deduplicate_properties(self, properties: List[Property]) -> DeduplicationResult:
        """
        Main deduplication method that processes a list of properties.
        
        Args:
            properties: List of properties from various sources
            
        Returns:
            DeduplicationResult with unique properties and metadata
        """
        start_time = datetime.now()
        
        # Step 1: Standardize all properties
        standardized_properties = []
        standardization_changes = {
            'addresses_cleaned': 0,
            'property_types_standardized': 0,
            'prices_normalized': 0,
            'suburbs_standardized': 0
        }
        
        for prop in properties:
            standardized_prop, changes = self._standardize_property(prop)
            standardized_properties.append(standardized_prop)
            
            # Track changes
            for key, value in changes.items():
                if key in standardization_changes:
                    standardization_changes[key] += value
        
        # Step 2: Find duplicates
        unique_properties = []
        matches = []
        processed_indices = set()
        
        for i, prop1 in enumerate(standardized_properties):
            if i in processed_indices:
                continue
            
            # Find all matches for this property
            current_matches = []
            
            for j, prop2 in enumerate(standardized_properties[i+1:], i+1):
                if j in processed_indices:
                    continue
                
                match = self._compare_properties(prop1, prop2)
                if match:
                    current_matches.append((j, match))
            
            if current_matches:
                # This property has duplicates - merge them
                properties_to_merge = [prop1]
                indices_to_mark = [i]
                
                for idx, match in current_matches:
                    properties_to_merge.append(standardized_properties[idx])
                    indices_to_mark.append(idx)
                    matches.append(match)
                
                # Merge all properties
                merged_property = self._merge_properties(properties_to_merge)
                unique_properties.append(merged_property)
                
                # Mark all indices as processed
                processed_indices.update(indices_to_mark)
                
            else:
                # No duplicates found, add as unique
                unique_properties.append(prop1)
                processed_indices.add(i)
        
        # Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return DeduplicationResult(
            unique_properties=unique_properties,
            duplicates_found=len(properties) - len(unique_properties),
            matches=matches,
            standardization_changes=standardization_changes,
            processing_time_ms=processing_time
        )
    
    def _standardize_property(self, property: Property) -> Tuple[Property, Dict[str, int]]:
        """Standardize a single property and return changes made."""
        changes = {
            'addresses_cleaned': 0,
            'property_types_standardized': 0, 
            'prices_normalized': 0,
            'suburbs_standardized': 0
        }
        
        # Create a copy to avoid modifying original
        standardized = Property(
            address=property.address,
            suburb=property.suburb,
            price=property.price,
            price_numeric=property.price_numeric,
            bedrooms=property.bedrooms,
            bathrooms=property.bathrooms,
            parking=property.parking,
            property_type=property.property_type,
            link=property.link
        )
        
        # Standardize address
        original_address = standardized.address
        standardized.address = self._standardize_address(standardized.address)
        if standardized.address != original_address:
            changes['addresses_cleaned'] = 1
        
        # Standardize property type
        original_type = standardized.property_type
        standardized.property_type = self._standardize_property_type(standardized.property_type)
        if standardized.property_type != original_type:
            changes['property_types_standardized'] = 1
        
        # Standardize price
        original_price = standardized.price
        standardized.price, standardized.price_numeric = self._standardize_price(
            standardized.price, standardized.price_numeric
        )
        if standardized.price != original_price:
            changes['prices_normalized'] = 1
        
        # Standardize suburb
        original_suburb = standardized.suburb
        standardized.suburb = self._standardize_suburb(standardized.suburb)
        if standardized.suburb != original_suburb:
            changes['suburbs_standardized'] = 1
        
        return standardized, changes
    
    def _standardize_address(self, address: str) -> str:
        """Standardize address format."""
        if not address:
            return ""
        
        # Convert to title case
        address = address.title()
        
        # Standardize common abbreviations
        replacements = {
            r'\bSt\b': 'Street',
            r'\bRd\b': 'Road', 
            r'\bAve\b': 'Avenue',
            r'\bDr\b': 'Drive',
            r'\bCres\b': 'Crescent',
            r'\bPl\b': 'Place',
            r'\bLn\b': 'Lane',
            r'\bCt\b': 'Court',
            r'\bPde\b': 'Parade',
            r'\bTce\b': 'Terrace',
            r'\bNsw\b': 'NSW',
        }
        
        for pattern, replacement in replacements.items():
            address = re.sub(pattern, replacement, address, flags=re.IGNORECASE)
        
        # Remove extra spaces
        address = re.sub(r'\s+', ' ', address).strip()
        
        return address
    
    def _standardize_property_type(self, property_type: str) -> str:
        """Standardize property type to consistent format."""
        if not property_type:
            return "Unknown"
        
        property_type_lower = property_type.lower().strip()
        
        # Check direct mapping first
        if property_type_lower in self.property_type_mapping:
            return self.property_type_mapping[property_type_lower]
        
        # Check for partial matches
        for key, value in self.property_type_mapping.items():
            if key in property_type_lower or property_type_lower in key:
                return value
        
        # If no match found, return title case version
        return property_type.title()
    
    def _standardize_price(self, price: str, price_numeric: Optional[float]) -> Tuple[str, Optional[float]]:
        """Standardize price format."""
        if not price:
            return "Contact Agent", None
        
        # Clean price string
        price_clean = price.strip()
        
        # Handle "Contact Agent" variations
        contact_variations = ['contact agent', 'contact', 'price on application', 'poa', 'enquire']
        if any(var in price_clean.lower() for var in contact_variations):
            return "Contact Agent", None
        
        # Extract numeric price if not already available
        if price_numeric is None:
            price_match = re.search(r'[\$]?([0-9,]+(?:\.[0-9]+)?)', price_clean)
            if price_match:
                try:
                    price_numeric = float(price_match.group(1).replace(',', ''))
                except ValueError:
                    price_numeric = None
        
        # Format price consistently
        if price_numeric:
            if price_numeric >= 1000000:
                formatted_price = f"${price_numeric:,.0f}"
            elif price_numeric >= 1000:
                formatted_price = f"${price_numeric:,.0f}"
            else:
                formatted_price = f"${price_numeric:.0f}"
        else:
            formatted_price = price_clean
        
        return formatted_price, price_numeric
    
    def _standardize_suburb(self, suburb: str) -> str:
        """Standardize suburb name."""
        if not suburb:
            return ""
        
        suburb = suburb.title().strip()
        
        # Check for aliases
        for main_suburb, aliases in self.suburb_aliases.items():
            if suburb in aliases:
                return main_suburb
        
        return suburb
    
    def _compare_properties(self, prop1: Property, prop2: Property) -> Optional[PropertyMatch]:
        """Compare two properties and return match if they are likely duplicates."""
        
        match_criteria = []
        total_score = 0.0
        max_score = 0.0
        
        # 1. Address similarity (weight: 40%)
        address_score = self._calculate_address_similarity(prop1.address, prop2.address)
        if address_score >= self.address_similarity_threshold:
            match_criteria.append(f"Address similarity: {address_score:.2f}")
            total_score += address_score * 0.4
        max_score += 0.4
        
        # 2. Price similarity (weight: 20%)
        price_score = self._calculate_price_similarity(prop1.price_numeric, prop2.price_numeric)
        if price_score > 0.7:  # Price threshold
            match_criteria.append(f"Price similarity: {price_score:.2f}")
            total_score += price_score * 0.2
        max_score += 0.2
        
        # 3. Property features (weight: 30%)
        features_score = self._calculate_features_similarity(prop1, prop2)
        if features_score > 0.8:  # Features threshold
            match_criteria.append(f"Features similarity: {features_score:.2f}")
            total_score += features_score * 0.3
        max_score += 0.3
        
        # 4. Suburb match (weight: 10%)
        suburb_score = 1.0 if prop1.suburb.lower() == prop2.suburb.lower() else 0.0
        if suburb_score > 0:
            match_criteria.append("Suburb match")
            total_score += suburb_score * 0.1
        max_score += 0.1
        
        # Calculate final match score
        if max_score > 0:
            final_score = total_score / max_score
        else:
            final_score = 0.0
        
        # Determine if this is a match
        if final_score >= 0.8:
            confidence = 'high'
        elif final_score >= 0.6:
            confidence = 'medium'
        elif final_score >= 0.4:
            confidence = 'low'
        else:
            return None  # Not a match
        
        # Additional check: must have at least 2 matching criteria
        if len(match_criteria) >= 2:
            return PropertyMatch(
                property1=prop1,
                property2=prop2,
                match_score=final_score,
                match_criteria=match_criteria,
                confidence=confidence
            )
        
        return None
    
    def _calculate_address_similarity(self, addr1: str, addr2: str) -> float:
        """Calculate similarity between two addresses."""
        if not addr1 or not addr2:
            return 0.0
        
        # Normalize addresses for comparison
        addr1_norm = re.sub(r'[^\w\s]', '', addr1.lower()).strip()
        addr2_norm = re.sub(r'[^\w\s]', '', addr2.lower()).strip()
        
        # Use sequence matcher for similarity
        similarity = difflib.SequenceMatcher(None, addr1_norm, addr2_norm).ratio()
        
        # Boost score if street numbers match
        number1 = re.search(r'^(\d+)', addr1_norm)
        number2 = re.search(r'^(\d+)', addr2_norm)
        
        if number1 and number2 and number1.group(1) == number2.group(1):
            similarity = min(1.0, similarity + 0.1)
        
        return similarity
    
    def _calculate_price_similarity(self, price1: Optional[float], price2: Optional[float]) -> float:
        """Calculate price similarity score."""
        if price1 is None or price2 is None:
            if price1 is None and price2 is None:
                return 1.0  # Both are "Contact Agent"
            return 0.0
        
        if price1 == 0 or price2 == 0:
            return 0.0
        
        # Calculate percentage difference
        avg_price = (price1 + price2) / 2
        diff_percent = abs(price1 - price2) / avg_price * 100
        
        if diff_percent <= self.price_tolerance_percent:
            return 1.0 - (diff_percent / self.price_tolerance_percent * 0.3)
        else:
            return max(0.0, 1.0 - (diff_percent / 50.0))  # Gradual decline
    
    def _calculate_features_similarity(self, prop1: Property, prop2: Property) -> float:
        """Calculate similarity based on property features."""
        score = 0.0
        matches = 0
        total_features = 3  # bedrooms, bathrooms, parking
        
        # Bedrooms
        if prop1.bedrooms == prop2.bedrooms:
            score += 1.0
            matches += 1
        elif abs(prop1.bedrooms - prop2.bedrooms) == 1:
            score += 0.5  # Close match
        
        # Bathrooms  
        if prop1.bathrooms == prop2.bathrooms:
            score += 1.0
            matches += 1
        elif abs(prop1.bathrooms - prop2.bathrooms) == 1:
            score += 0.5
        
        # Parking
        if prop1.parking == prop2.parking:
            score += 1.0
            matches += 1
        elif abs(prop1.parking - prop2.parking) == 1:
            score += 0.5
        
        return score / total_features
    
    def _merge_properties(self, properties: List[Property]) -> Property:
        """Merge multiple properties into a single comprehensive property."""
        if len(properties) == 1:
            return properties[0]
        
        # Use the first property as base
        merged = Property(
            address=properties[0].address,
            suburb=properties[0].suburb,
            price=properties[0].price,
            price_numeric=properties[0].price_numeric,
            bedrooms=properties[0].bedrooms,
            bathrooms=properties[0].bathrooms,
            parking=properties[0].parking,
            property_type=properties[0].property_type,
            link=properties[0].link
        )
        
        # Merge information from other sources
        all_links = [prop.link for prop in properties if prop.link]
        
        # Prefer numeric price over "Contact Agent"
        for prop in properties:
            if prop.price_numeric and not merged.price_numeric:
                merged.price = prop.price
                merged.price_numeric = prop.price_numeric
                break
        
        # Take the most complete address
        for prop in properties:
            if len(prop.address) > len(merged.address):
                merged.address = prop.address
        
        # Prefer more specific property type
        property_type_priority = {
            "Unknown": 0,
            "Apartment / Unit / Flat": 2,
            "House": 2,
            "Townhouse": 2,
            "Studio": 3,
            "Penthouse": 4,
            "Villa": 3
        }
        
        for prop in properties:
            current_priority = property_type_priority.get(merged.property_type, 1)
            new_priority = property_type_priority.get(prop.property_type, 1)
            
            if new_priority > current_priority:
                merged.property_type = prop.property_type
        
        # Combine links (prefer domain.com.au, then realestate.com.au)
        link_priority = {
            'domain.com.au': 3,
            'realestate.com.au': 2,
            'rent.com.au': 1
        }
        
        best_link = merged.link
        best_priority = 0
        
        for link in all_links:
            for site, priority in link_priority.items():
                if site in link and priority > best_priority:
                    best_link = link
                    best_priority = priority
                    break
        
        merged.link = best_link
        
        return merged

# Test and utility functions
def test_deduplicator():
    """Test the property deduplicator."""
    
    # Create test properties with duplicates
    test_properties = [
        Property(
            address="123 Test Street, Bondi NSW 2026",
            suburb="Bondi",
            price="$2,500 per week",
            price_numeric=2500.0,
            bedrooms=2,
            bathrooms=2,
            parking=1,
            property_type="Apartment",
            link="https://www.domain.com.au/property/123"
        ),
        Property(
            address="123 Test St, Bondi NSW 2026",  # Same property, different format
            suburb="Bondi",
            price="$2,500 weekly",
            price_numeric=2500.0,
            bedrooms=2,
            bathrooms=2,
            parking=1,
            property_type="Apartment / Unit / Flat",
            link="https://www.realestate.com.au/property/123"
        ),
        Property(
            address="456 Different Road, Chatswood NSW 2067",
            suburb="Chatswood",
            price="Contact Agent",
            price_numeric=None,
            bedrooms=3,
            bathrooms=2,
            parking=2,
            property_type="House",
            link="https://www.domain.com.au/property/456"
        )
    ]
    
    print("Testing Property Deduplicator")
    print("=" * 40)
    
    deduplicator = PropertyDeduplicator()
    result = deduplicator.deduplicate_properties(test_properties)
    
    print(f"Original properties: {len(test_properties)}")
    print(f"Unique properties: {len(result.unique_properties)}")
    print(f"Duplicates found: {result.duplicates_found}")
    print(f"Processing time: {result.processing_time_ms}ms")
    print(f"Standardization changes: {result.standardization_changes}")
    
    print("\nMatches found:")
    for match in result.matches:
        print(f"  Match score: {match.match_score:.2f} ({match.confidence})")
        print(f"  Criteria: {', '.join(match.match_criteria)}")
        print(f"  Properties: {match.property1.address} <-> {match.property2.address}")
    
    print("\nUnique properties after deduplication:")
    for i, prop in enumerate(result.unique_properties, 1):
        print(f"  {i}. {prop.address} - {prop.price} - {prop.bedrooms}BR")

if __name__ == "__main__":
    test_deduplicator()