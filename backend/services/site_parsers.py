"""
Site-specific parsers for property websites.
Extracts property information from HTML content of different real estate sites.
"""

import re
import json
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
from dataclasses import dataclass
import sys
import os

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from backend.models.property import Property

class BasePropertyParser:
    """Base class for property website parsers."""
    
    def __init__(self):
        self.site_name = ""
    
    async def parse_properties(self, html_content: str, url_data: Dict[str, Any]) -> List[Property]:
        """Parse properties from HTML content. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement parse_properties method")
    
    def _clean_price(self, price_text: str) -> Dict[str, Any]:
        """Clean and parse price text into numeric and string formats."""
        if not price_text:
            return {'price': 'Contact Agent', 'price_numeric': None}
        
        # Remove common formatting
        cleaned = re.sub(r'[^\d\.,\-\$]+', ' ', price_text).strip()
        
        # Extract numeric price
        price_match = re.search(r'[\$]?([0-9,]+(?:\.[0-9]+)?)', cleaned)
        
        if price_match:
            try:
                numeric_price = float(price_match.group(1).replace(',', ''))
                return {
                    'price': price_text.strip(),
                    'price_numeric': numeric_price
                }
            except ValueError:
                pass
        
        return {'price': price_text.strip(), 'price_numeric': None}
    
    def _extract_number(self, text: str, default: int = 0) -> int:
        """Extract number from text."""
        if not text:
            return default
        
        # Find first number in text
        match = re.search(r'(\d+)', str(text))
        if match:
            return int(match.group(1))
        
        return default
    
    def _normalize_property_type(self, prop_type: str) -> str:
        """Normalize property type to standard format."""
        if not prop_type:
            return "Unknown"
        
        prop_type = prop_type.lower().strip()
        
        # Mapping common variations
        if any(word in prop_type for word in ['apartment', 'unit', 'flat']):
            return "Apartment / Unit / Flat"
        elif any(word in prop_type for word in ['house', 'home']):
            return "House"
        elif any(word in prop_type for word in ['townhouse', 'terrace']):
            return "Townhouse"
        elif 'studio' in prop_type:
            return "Studio"
        elif 'villa' in prop_type:
            return "Villa"
        else:
            return prop_type.title()

class RealEstateParser(BasePropertyParser):
    """Parser for realestate.com.au website."""
    
    def __init__(self):
        super().__init__()
        self.site_name = "realestate.com.au"
    
    async def parse_properties(self, html_content: str, url_data: Dict[str, Any]) -> List[Property]:
        """Parse properties from realestate.com.au HTML content."""
        properties = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for property cards - multiple possible selectors
            property_selectors = [
                '.property-card',
                '.listing-result',
                '.residential-card',
                '[data-testid="property-card"]',
                '.property-list-item'
            ]
            
            property_elements = []
            for selector in property_selectors:
                elements = soup.select(selector)
                if elements:
                    property_elements = elements
                    break
            
            # If no property cards found, try to find properties in script tags (JSON data)
            if not property_elements:
                properties.extend(self._parse_json_data(soup))
            
            # Parse each property card
            for element in property_elements[:20]:  # Limit to first 20 properties
                try:
                    property_data = self._parse_property_card(element, url_data)
                    if property_data:
                        properties.append(property_data)
                except Exception as e:
                    print(f"Error parsing property card: {e}")
                    continue
            
        except Exception as e:
            print(f"Error parsing realestate.com.au content: {e}")
        
        return properties
    
    def _parse_property_card(self, element, url_data: Dict[str, Any]) -> Optional[Property]:
        """Parse individual property card element."""
        try:
            # Extract price
            price_selectors = ['.price', '.property-price', '[data-testid="price"]', '.listing-result__price']
            price_text = ""
            for selector in price_selectors:
                price_el = element.select_one(selector)
                if price_el:
                    price_text = price_el.get_text(strip=True)
                    break
            
            price_data = self._clean_price(price_text)
            
            # Extract address
            address_selectors = ['.address', '.property-address', '[data-testid="address"]', '.listing-result__address']
            address = ""
            for selector in address_selectors:
                addr_el = element.select_one(selector)
                if addr_el:
                    address = addr_el.get_text(strip=True)
                    break
            
            # Extract bedrooms, bathrooms, parking
            features_selectors = [
                '.property-features',
                '.features',
                '.property-meta',
                '.listing-result__features'
            ]
            
            bedrooms = 0
            bathrooms = 0
            parking = 0
            
            for selector in features_selectors:
                features_el = element.select_one(selector)
                if features_el:
                    features_text = features_el.get_text()
                    
                    # Extract bedrooms
                    bed_match = re.search(r'(\d+)\s*(?:bed|br|bedroom)', features_text, re.IGNORECASE)
                    if bed_match:
                        bedrooms = int(bed_match.group(1))
                    
                    # Extract bathrooms
                    bath_match = re.search(r'(\d+)\s*(?:bath|bathroom)', features_text, re.IGNORECASE)
                    if bath_match:
                        bathrooms = int(bath_match.group(1))
                    
                    # Extract parking
                    park_match = re.search(r'(\d+)\s*(?:car|garage|parking)', features_text, re.IGNORECASE)
                    if park_match:
                        parking = int(park_match.group(1))
                    
                    break
            
            # Extract property type
            type_selectors = ['.property-type', '.listing-result__type', '[data-testid="property-type"]']
            property_type = "Unknown"
            for selector in type_selectors:
                type_el = element.select_one(selector)
                if type_el:
                    property_type = self._normalize_property_type(type_el.get_text(strip=True))
                    break
            
            # Extract link
            link_selectors = ['a[href]', '.property-link']
            link = url_data.get('url', '')
            for selector in link_selectors:
                link_el = element.select_one(selector)
                if link_el and link_el.get('href'):
                    href = link_el.get('href')
                    if href.startswith('/'):
                        link = f"https://www.realestate.com.au{href}"
                    elif href.startswith('http'):
                        link = href
                    break
            
            # Create property object
            if address and price_data['price']:
                return Property(
                    address=address,
                    suburb=url_data.get('suburb', ''),
                    price=price_data['price'],
                    price_numeric=price_data['price_numeric'],
                    bedrooms=bedrooms,
                    bathrooms=bathrooms,
                    parking=parking,
                    property_type=property_type,
                    link=link
                )
        
        except Exception as e:
            print(f"Error parsing realestate.com.au property card: {e}")
        
        return None
    
    def _parse_json_data(self, soup) -> List[Property]:
        """Parse properties from JSON data in script tags."""
        properties = []
        
        try:
            # Look for JSON data in script tags
            script_tags = soup.find_all('script', type='application/json')
            script_tags.extend(soup.find_all('script', string=re.compile(r'window\.__')))
            
            for script in script_tags:
                try:
                    if script.string:
                        # Try to extract JSON data
                        json_match = re.search(r'\{.*\}', script.string, re.DOTALL)
                        if json_match:
                            data = json.loads(json_match.group())
                            
                            # Look for property listings in the data
                            properties.extend(self._extract_properties_from_json(data))
                
                except (json.JSONDecodeError, Exception):
                    continue
        
        except Exception as e:
            print(f"Error parsing JSON data: {e}")
        
        return properties
    
    def _extract_properties_from_json(self, data: Dict) -> List[Property]:
        """Extract properties from JSON data structure."""
        properties = []
        
        # This would need to be implemented based on the actual JSON structure
        # For now, return empty list as we don't have the exact structure
        return properties

class DomainParser(BasePropertyParser):
    """Parser for domain.com.au website."""
    
    def __init__(self):
        super().__init__()
        self.site_name = "domain.com.au"
    
    async def parse_properties(self, html_content: str, url_data: Dict[str, Any]) -> List[Property]:
        """Parse properties from domain.com.au HTML content."""
        properties = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Domain.com.au property card selectors
            property_selectors = [
                '[data-testid="listing-card"]',
                '.listing-card',
                '.property-card',
                '.css-qrqvlg'  # Domain often uses CSS modules
            ]
            
            property_elements = []
            for selector in property_selectors:
                elements = soup.select(selector)
                if elements:
                    property_elements = elements
                    break
            
            # Parse each property
            for element in property_elements[:20]:  # Limit to 20
                try:
                    property_data = self._parse_domain_property(element, url_data)
                    if property_data:
                        properties.append(property_data)
                except Exception as e:
                    print(f"Error parsing domain property: {e}")
                    continue
        
        except Exception as e:
            print(f"Error parsing domain.com.au content: {e}")
        
        return properties
    
    def _parse_domain_property(self, element, url_data: Dict[str, Any]) -> Optional[Property]:
        """Parse individual Domain property card."""
        try:
            # Extract price (Domain has various price formats)
            price_text = ""
            price_selectors = [
                '[data-testid="listing-card-price"]',
                '.price',
                '.listing-card__price',
                '.property-price'
            ]
            
            for selector in price_selectors:
                price_el = element.select_one(selector)
                if price_el:
                    price_text = price_el.get_text(strip=True)
                    break
            
            price_data = self._clean_price(price_text)
            
            # Extract address
            address = ""
            address_selectors = [
                '[data-testid="listing-card-address"]',
                '.address',
                '.listing-card__address'
            ]
            
            for selector in address_selectors:
                addr_el = element.select_one(selector)
                if addr_el:
                    address = addr_el.get_text(strip=True)
                    break
            
            # Extract features (beds, baths, parking)
            bedrooms = bathrooms = parking = 0
            
            feature_selectors = [
                '[data-testid="property-features"]',
                '.property-features',
                '.listing-card__features'
            ]
            
            for selector in feature_selectors:
                features_el = element.select_one(selector)
                if features_el:
                    # Domain often has separate elements for each feature
                    bed_els = features_el.select('[data-testid="bed-count"], .bed, .bedroom')
                    bath_els = features_el.select('[data-testid="bath-count"], .bath, .bathroom')
                    park_els = features_el.select('[data-testid="parking-count"], .parking, .garage')
                    
                    if bed_els:
                        bedrooms = self._extract_number(bed_els[0].get_text())
                    if bath_els:
                        bathrooms = self._extract_number(bath_els[0].get_text())
                    if park_els:
                        parking = self._extract_number(park_els[0].get_text())
                    
                    break
            
            # Property type
            property_type = "Unknown"
            type_selectors = [
                '[data-testid="property-type"]',
                '.property-type',
                '.listing-card__type'
            ]
            
            for selector in type_selectors:
                type_el = element.select_one(selector)
                if type_el:
                    property_type = self._normalize_property_type(type_el.get_text(strip=True))
                    break
            
            # Extract link
            link = url_data.get('url', '')
            link_el = element.select_one('a[href]')
            if link_el and link_el.get('href'):
                href = link_el.get('href')
                if href.startswith('/'):
                    link = f"https://www.domain.com.au{href}"
                elif href.startswith('http'):
                    link = href
            
            # Create property
            if address and price_data['price']:
                return Property(
                    address=address,
                    suburb=url_data.get('suburb', ''),
                    price=price_data['price'],
                    price_numeric=price_data['price_numeric'],
                    bedrooms=bedrooms,
                    bathrooms=bathrooms,
                    parking=parking,
                    property_type=property_type,
                    link=link
                )
        
        except Exception as e:
            print(f"Error parsing domain property: {e}")
        
        return None

class RentParser(BasePropertyParser):
    """Parser for rent.com.au website."""
    
    def __init__(self):
        super().__init__()
        self.site_name = "rent.com.au"
    
    async def parse_properties(self, html_content: str, url_data: Dict[str, Any]) -> List[Property]:
        """Parse properties from rent.com.au HTML content."""
        properties = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Rent.com.au property selectors
            property_selectors = [
                '.property-item',
                '.listing-item',
                '.property-card',
                '.rent-listing'
            ]
            
            property_elements = []
            for selector in property_selectors:
                elements = soup.select(selector)
                if elements:
                    property_elements = elements
                    break
            
            # Parse each property
            for element in property_elements[:20]:  # Limit to 20
                try:
                    property_data = self._parse_rent_property(element, url_data)
                    if property_data:
                        properties.append(property_data)
                except Exception as e:
                    print(f"Error parsing rent property: {e}")
                    continue
        
        except Exception as e:
            print(f"Error parsing rent.com.au content: {e}")
        
        return properties
    
    def _parse_rent_property(self, element, url_data: Dict[str, Any]) -> Optional[Property]:
        """Parse individual Rent.com.au property."""
        try:
            # Extract price (weekly rent)
            price_text = ""
            price_selectors = ['.price', '.rent-price', '.weekly-rent', '.property-price']
            
            for selector in price_selectors:
                price_el = element.select_one(selector)
                if price_el:
                    price_text = price_el.get_text(strip=True)
                    break
            
            price_data = self._clean_price(price_text)
            
            # Extract address
            address = ""
            address_selectors = ['.address', '.property-address', '.location']
            
            for selector in address_selectors:
                addr_el = element.select_one(selector)
                if addr_el:
                    address = addr_el.get_text(strip=True)
                    break
            
            # Extract features
            bedrooms = bathrooms = parking = 0
            
            features_text = element.get_text()
            
            # Extract numbers for beds, baths, parking
            bed_match = re.search(r'(\d+)\s*(?:bed|br|bedroom)', features_text, re.IGNORECASE)
            if bed_match:
                bedrooms = int(bed_match.group(1))
            
            bath_match = re.search(r'(\d+)\s*(?:bath|bathroom)', features_text, re.IGNORECASE)
            if bath_match:
                bathrooms = int(bath_match.group(1))
            
            park_match = re.search(r'(\d+)\s*(?:car|garage|parking)', features_text, re.IGNORECASE)
            if park_match:
                parking = int(park_match.group(1))
            
            # Property type (rent.com.au is rental focused)
            property_type = "Apartment / Unit / Flat"  # Default for rentals
            type_selectors = ['.property-type', '.type']
            
            for selector in type_selectors:
                type_el = element.select_one(selector)
                if type_el:
                    property_type = self._normalize_property_type(type_el.get_text(strip=True))
                    break
            
            # Extract link
            link = url_data.get('url', '')
            link_el = element.select_one('a[href]')
            if link_el and link_el.get('href'):
                href = link_el.get('href')
                if href.startswith('/'):
                    link = f"https://www.rent.com.au{href}"
                elif href.startswith('http'):
                    link = href
            
            # Create property
            if address and price_data['price']:
                return Property(
                    address=address,
                    suburb=url_data.get('suburb', ''),
                    price=price_data['price'],
                    price_numeric=price_data['price_numeric'],
                    bedrooms=bedrooms,
                    bathrooms=bathrooms,
                    parking=parking,
                    property_type=property_type,
                    link=link
                )
        
        except Exception as e:
            print(f"Error parsing rent property: {e}")
        
        return None

# Factory function for getting the right parser
def get_parser(site: str) -> Optional[BasePropertyParser]:
    """Get the appropriate parser for a website."""
    parsers = {
        'realestate.com.au': RealEstateParser,
        'domain.com.au': DomainParser,
        'rent.com.au': RentParser
    }
    
    if site in parsers:
        return parsers[site]()
    
    return None

# Test function
async def test_parsers():
    """Test the parsers with sample HTML."""
    
    # Sample HTML for testing (simplified)
    sample_html = """
    <div class="property-card">
        <div class="price">$2,500 per week</div>
        <div class="address">123 Test Street, Bondi NSW 2026</div>
        <div class="property-features">
            <span>2 bed</span>
            <span>2 bath</span>
            <span>1 parking</span>
        </div>
        <div class="property-type">Apartment</div>
        <a href="/property/123">View Property</a>
    </div>
    """
    
    url_data = {
        'url': 'https://www.realestate.com.au/test',
        'site': 'realestate.com.au',
        'suburb': 'Bondi',
        'postcode': '2026'
    }
    
    print("Testing Property Parsers")
    print("=" * 30)
    
    # Test RealEstate parser
    parser = RealEstateParser()
    properties = await parser.parse_properties(sample_html, url_data)
    
    print(f"RealEstate Parser: Found {len(properties)} properties")
    for prop in properties:
        print(f"  {prop.address} - {prop.price} - {prop.bedrooms}BR/{prop.bathrooms}BA")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_parsers())