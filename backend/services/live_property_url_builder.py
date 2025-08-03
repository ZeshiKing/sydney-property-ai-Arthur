"""
Live Property URL Builder
Constructs dynamic URLs for property websites based on user intent and search criteria.
Supports multiple property sources with intelligent URL generation.
"""

from typing import List, Dict, Optional, Tuple
from urllib.parse import urlencode, quote
import sys
import os

# Add the data directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../data'))
from sydney_suburb_postcode_mapping import get_postcode_for_suburb, normalize_suburb_name

class LivePropertyURLBuilder:
    """
    Dynamic URL builder for property websites.
    Constructs search URLs based on user intent and location preferences.
    """
    
    def __init__(self):
        """Initialize the URL builder with supported websites."""
        self.supported_sites = {
            'realestate.com.au': {
                'base_url': 'https://www.realestate.com.au',
                'rent_path': '/rent',
                'buy_path': '/buy', 
                'sold_path': '/sold',
                'location_format': '/in-{suburb},+nsw+{postcode}',
                'list_format': '/list-{page}',
                'supports_filters': True
            },
            'domain.com.au': {
                'base_url': 'https://www.domain.com.au',
                'rent_path': '/rent',
                'buy_path': '/sale',
                'sold_path': '/sold',
                'location_format': '/{suburb}-nsw-{postcode}',
                'list_format': '?page={page}',
                'supports_filters': True
            },
            'rent.com.au': {
                'base_url': 'https://www.rent.com.au',
                'rent_path': '/properties',
                'buy_path': None,  # Rent.com.au is rental only
                'sold_path': None,
                'location_format': '/{suburb}-nsw-{postcode}',
                'list_format': '?page={page}',
                'supports_filters': True
            }
        }
    
    def build_search_urls(self, 
                         suburb: str = None,
                         property_type: str = 'rent',  # 'rent', 'buy', 'sold'
                         bedrooms: int = None,
                         min_price: float = None,
                         max_price: float = None,
                         bathrooms: int = None,
                         parking: int = None,
                         property_style: str = None,  # 'apartment', 'house', 'townhouse'
                         features: List[str] = None,
                         page: int = 1,
                         sites: List[str] = None) -> List[Dict[str, str]]:
        """
        Build search URLs for multiple property websites.
        
        Args:
            suburb: Target suburb name
            property_type: 'rent', 'buy', or 'sold'
            bedrooms: Number of bedrooms
            min_price: Minimum price (weekly for rent, total for buy)
            max_price: Maximum price (weekly for rent, total for buy)
            bathrooms: Number of bathrooms
            parking: Number of parking spaces
            property_style: Property type filter
            features: List of features (e.g., ['pool', 'gym'])
            page: Page number for pagination
            sites: List of sites to generate URLs for (default: all)
            
        Returns:
            List of dictionaries with 'site', 'url', and 'filters' keys
        """
        if not suburb:
            raise ValueError("Suburb is required for URL construction")
        
        # Get postcode for suburb
        postcode = get_postcode_for_suburb(suburb)
        if not postcode:
            raise ValueError(f"Postcode not found for suburb: {suburb}")
        
        # Normalize suburb name for URLs
        normalized_suburb = normalize_suburb_name(suburb)
        
        # Default to all sites if not specified
        if sites is None:
            sites = list(self.supported_sites.keys())
        
        urls = []
        
        for site in sites:
            if site not in self.supported_sites:
                continue
                
            site_config = self.supported_sites[site]
            
            # Skip if site doesn't support the property type
            if property_type == 'rent' and not site_config['rent_path']:
                continue
            elif property_type == 'buy' and not site_config['buy_path']:
                continue
            elif property_type == 'sold' and not site_config['sold_path']:
                continue
            
            try:
                url_data = self._build_site_url(
                    site, site_config, normalized_suburb, postcode, 
                    property_type, bedrooms, min_price, max_price,
                    bathrooms, parking, property_style, features, page
                )
                urls.append(url_data)
            except Exception as e:
                print(f"Error building URL for {site}: {e}")
                continue
        
        return urls
    
    def _build_site_url(self, site: str, config: Dict, suburb: str, postcode: str,
                       property_type: str, bedrooms: int, min_price: float, 
                       max_price: float, bathrooms: int, parking: int,
                       property_style: str, features: List[str], page: int) -> Dict[str, str]:
        """Build URL for a specific site."""
        
        # Get the appropriate path based on property type
        if property_type == 'rent':
            path = config['rent_path']
        elif property_type == 'buy':
            path = config['buy_path']
        elif property_type == 'sold':
            path = config['sold_path']
        else:
            raise ValueError(f"Unsupported property type: {property_type}")
        
        # Build location part
        location = config['location_format'].format(
            suburb=suburb, postcode=postcode
        )
        
        # Start building the URL
        base_url = config['base_url']
        
        if site == 'realestate.com.au':
            url, filters = self._build_realestate_url(
                base_url, path, location, bedrooms, min_price, max_price,
                bathrooms, parking, property_style, features, page
            )
        elif site == 'domain.com.au':
            url, filters = self._build_domain_url(
                base_url, path, location, bedrooms, min_price, max_price,
                bathrooms, parking, property_style, features, page
            )
        elif site == 'rent.com.au':
            url, filters = self._build_rent_url(
                base_url, path, location, bedrooms, min_price, max_price,
                bathrooms, parking, property_style, features, page
            )
        else:
            raise ValueError(f"URL building not implemented for site: {site}")
        
        return {
            'site': site,
            'url': url,
            'filters': filters,
            'suburb': suburb,
            'postcode': postcode
        }
    
    def _build_realestate_url(self, base_url: str, path: str, location: str,
                             bedrooms: int, min_price: float, max_price: float,
                             bathrooms: int, parking: int, property_style: str,
                             features: List[str], page: int) -> Tuple[str, Dict]:
        """Build realestate.com.au URL with filters."""
        
        # Base URL structure: https://www.realestate.com.au/rent/in-bondi,+nsw+2026/list-1
        url = f"{base_url}{path}{location}/list-{page}"
        
        # Build query parameters
        params = {}
        filters = {}
        
        if bedrooms is not None:
            params['bedrooms'] = str(bedrooms)
            filters['bedrooms'] = bedrooms
        
        if bathrooms is not None:
            params['bathrooms'] = str(bathrooms)
            filters['bathrooms'] = bathrooms
        
        if parking is not None:
            params['parking'] = str(parking)
            filters['parking'] = parking
        
        # Price filters
        if min_price is not None or max_price is not None:
            price_range = []
            if min_price is not None:
                price_range.append(str(int(min_price)))
                filters['min_price'] = min_price
            else:
                price_range.append('0')
            
            if max_price is not None:
                price_range.append(str(int(max_price)))
                filters['max_price'] = max_price
            else:
                price_range.append('any')
            
            params['price'] = '-'.join(price_range)
        
        # Property type filters
        if property_style:
            style_mapping = {
                'apartment': 'apartment',
                'house': 'house',
                'townhouse': 'townhouse',
                'unit': 'apartment',
                'flat': 'apartment'
            }
            if property_style.lower() in style_mapping:
                params['property_types'] = style_mapping[property_style.lower()]
                filters['property_style'] = property_style
        
        # Add query parameters to URL
        if params:
            url += '?' + urlencode(params)
        
        return url, filters
    
    def _build_domain_url(self, base_url: str, path: str, location: str,
                         bedrooms: int, min_price: float, max_price: float,
                         bathrooms: int, parking: int, property_style: str,
                         features: List[str], page: int) -> Tuple[str, Dict]:
        """Build domain.com.au URL with filters."""
        
        # Base URL structure: https://www.domain.com.au/rent/bondi-nsw-2026?page=1
        url = f"{base_url}{path}{location}"
        
        # Build query parameters
        params = {}
        filters = {}
        
        if page > 1:
            params['page'] = str(page)
        
        if bedrooms is not None:
            params['bedrooms'] = str(bedrooms)
            filters['bedrooms'] = bedrooms
        
        if bathrooms is not None:
            params['bathrooms'] = str(bathrooms)
            filters['bathrooms'] = bathrooms
        
        if parking is not None:
            params['carspaces'] = str(parking)
            filters['parking'] = parking
        
        # Price filters
        if min_price is not None:
            params['price-from'] = str(int(min_price))
            filters['min_price'] = min_price
        
        if max_price is not None:
            params['price-to'] = str(int(max_price))
            filters['max_price'] = max_price
        
        # Property type filters
        if property_style:
            style_mapping = {
                'apartment': 'apartment',
                'house': 'house',
                'townhouse': 'townhouse',
                'unit': 'unit',
                'flat': 'apartment'
            }
            if property_style.lower() in style_mapping:
                params['ptype'] = style_mapping[property_style.lower()]
                filters['property_style'] = property_style
        
        # Add query parameters to URL
        if params:
            url += '?' + urlencode(params)
        
        return url, filters
    
    def _build_rent_url(self, base_url: str, path: str, location: str,
                       bedrooms: int, min_price: float, max_price: float,
                       bathrooms: int, parking: int, property_style: str,
                       features: List[str], page: int) -> Tuple[str, Dict]:
        """Build rent.com.au URL with filters."""
        
        # Base URL structure: https://www.rent.com.au/properties/bondi-nsw-2026?page=1
        url = f"{base_url}{path}{location}"
        
        # Build query parameters
        params = {}
        filters = {}
        
        if page > 1:
            params['page'] = str(page)
        
        if bedrooms is not None:
            params['bedrooms'] = str(bedrooms)
            filters['bedrooms'] = bedrooms
        
        if bathrooms is not None:
            params['bathrooms'] = str(bathrooms)
            filters['bathrooms'] = bathrooms
        
        if parking is not None:
            params['parking'] = str(parking)
            filters['parking'] = parking
        
        # Price filters (weekly rent)
        if min_price is not None:
            params['rent_low'] = str(int(min_price))
            filters['min_price'] = min_price
        
        if max_price is not None:
            params['rent_high'] = str(int(max_price))
            filters['max_price'] = max_price
        
        # Property type filters
        if property_style:
            style_mapping = {
                'apartment': 'apartment',
                'house': 'house',
                'townhouse': 'townhouse',
                'unit': 'unit',
                'flat': 'apartment'
            }
            if property_style.lower() in style_mapping:
                params['property_type'] = style_mapping[property_style.lower()]
                filters['property_style'] = property_style
        
        # Add query parameters to URL
        if params:
            url += '?' + urlencode(params)
        
        return url, filters
    
    def get_pagination_urls(self, base_url_data: Dict[str, str], total_pages: int = 5) -> List[Dict[str, str]]:
        """
        Generate pagination URLs for a base search.
        
        Args:
            base_url_data: Result from build_search_urls
            total_pages: Number of pages to generate
            
        Returns:
            List of URL data for different pages
        """
        pagination_urls = []
        
        for page in range(1, total_pages + 1):
            # Extract components from original URL
            site = base_url_data['site']
            suburb = base_url_data['suburb'] 
            postcode = base_url_data['postcode']
            filters = base_url_data['filters']
            
            # Reconstruct URL for this page
            try:
                # This is a simplified approach - in practice you'd need to 
                # reconstruct with all the original parameters
                config = self.supported_sites[site]
                
                if site == 'realestate.com.au':
                    # Replace list-X with list-{page}
                    new_url = base_url_data['url'].replace('/list-1', f'/list-{page}')
                elif site in ['domain.com.au', 'rent.com.au']:
                    # Update page parameter
                    if '?' in base_url_data['url']:
                        base_part, query_part = base_url_data['url'].split('?', 1)
                        # Simple replacement - could be improved
                        if 'page=' in query_part:
                            new_url = base_url_data['url'].replace('page=1', f'page={page}')
                        else:
                            new_url = f"{base_url_data['url']}&page={page}"
                    else:
                        new_url = f"{base_url_data['url']}?page={page}"
                else:
                    new_url = base_url_data['url']
                
                pagination_urls.append({
                    'site': site,
                    'url': new_url,
                    'filters': filters,
                    'suburb': suburb,
                    'postcode': postcode,
                    'page': page
                })
                
            except Exception as e:
                print(f"Error generating pagination URL for page {page}: {e}")
                continue
        
        return pagination_urls

    def validate_url(self, url: str) -> bool:
        """Validate that a constructed URL is properly formatted."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return all([parsed.scheme, parsed.netloc, parsed.path])
        except:
            return False

if __name__ == "__main__":
    # Test the URL builder
    builder = LivePropertyURLBuilder()
    
    # Test basic URL construction
    print("Testing Live Property URL Builder")
    print("=" * 50)
    
    test_cases = [
        {
            'suburb': 'Bondi',
            'property_type': 'rent',
            'bedrooms': 2,
            'max_price': 800,
            'description': 'Rent 2BR in Bondi under $800/week'
        },
        {
            'suburb': 'Chatswood',
            'property_type': 'buy',
            'bedrooms': 3,
            'min_price': 800000,
            'max_price': 1200000,
            'property_style': 'apartment',
            'description': 'Buy 3BR apartment in Chatswood $800k-$1.2M'
        },
        {
            'suburb': 'Manly',
            'property_type': 'rent',
            'bedrooms': 1,
            'max_price': 600,
            'parking': 1,
            'description': 'Rent 1BR in Manly under $600/week with parking'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['description']}")
        print("-" * 40)
        
        # Remove description from test_case before passing to builder
        test_params = {k: v for k, v in test_case.items() if k != 'description'}
        
        try:
            urls = builder.build_search_urls(**test_params)
            
            for url_data in urls:
                print(f"Site: {url_data['site']}")
                print(f"URL: {url_data['url']}")
                print(f"Filters: {url_data['filters']}")
                print(f"Valid: {builder.validate_url(url_data['url'])}")
                print()
                
        except Exception as e:
            print(f"Error: {e}")
            print()
    
    print(f"Total supported sites: {len(builder.supported_sites)}")
    print(f"Sites: {', '.join(builder.supported_sites.keys())}")