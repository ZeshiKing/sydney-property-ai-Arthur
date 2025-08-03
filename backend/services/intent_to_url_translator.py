"""
Intent to URL Translator
Converts AI-extracted user intent into parameters for live property URL construction.
Bridges the gap between natural language understanding and property search URLs.
"""

from typing import Dict, List, Optional, Any
import re
import sys
import os

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend/models'))

from backend.services.live_property_url_builder import LivePropertyURLBuilder
from backend.models.property import UserIntent

class IntentToURLTranslator:
    """
    Translates user intent into search parameters for live property URLs.
    Handles complex intent interpretation and parameter optimization.
    """
    
    def __init__(self):
        """Initialize the translator with URL builder and mapping data."""
        self.url_builder = LivePropertyURLBuilder()
        self.price_keywords = self._load_price_keywords()
        self.property_type_mapping = self._load_property_type_mapping()
        self.location_preferences = self._load_location_preferences()
    
    def _load_price_keywords(self) -> Dict[str, float]:
        """Load price-related keywords and their interpretations."""
        return {
            # Budget modifiers
            "以内": 1.0,  # within
            "以下": 1.0,  # under
            "不超过": 1.0,  # not exceeding
            "最多": 1.0,  # at most
            "左右": 1.1,  # around (+10%)
            "大概": 1.1,  # approximately
            "差不多": 1.1,  # about
            
            # Rent vs buy price conversion (weekly rent -> annual -> property value estimate)
            "rent_to_buy_multiplier": 26 * 20,  # 26 weeks * 20 years rough estimate
            
            # Weekly to monthly conversion
            "weekly_to_monthly": 4.33,
            
            # Common price shortcuts
            "万": 10000,  # 10 thousand
            "w": 10000,
            "k": 1000,
            "千": 1000
        }
    
    def _load_property_type_mapping(self) -> Dict[str, str]:
        """Load property type mappings from natural language to search terms."""
        return {
            # Apartment variations
            "公寓": "apartment",
            "单元": "apartment", 
            "unit": "apartment",
            "flat": "apartment",
            "apartment": "apartment",
            
            # House variations
            "房子": "house",
            "别墅": "house",
            "house": "house",
            "home": "house",
            "villa": "house",
            
            # Townhouse variations
            "联排": "townhouse",
            "联排别墅": "townhouse",
            "townhouse": "townhouse",
            "terrace": "townhouse",
            
            # Studio variations
            "工作室": "studio",
            "studio": "studio",
            "loft": "studio"
        }
    
    def _load_location_preferences(self) -> Dict[str, Dict]:
        """Load location preference mappings."""
        return {
            "distance_preferences": {
                "市中心": {"target": "city_center", "radius_km": 5},
                "市区": {"target": "city_center", "radius_km": 10},
                "内城": {"target": "inner_city", "radius_km": 15},
                "郊外": {"target": "suburbs", "radius_km": 30},
                "远郊": {"target": "outer_suburbs", "radius_km": 50},
                "离市区远": {"target": "outer_suburbs", "radius_km": 40},
                "远离市区": {"target": "outer_suburbs", "radius_km": 45}
            },
            "environment_preferences": {
                "安静": ["residential", "quiet", "peaceful"],
                "热闹": ["commercial", "busy", "vibrant"],
                "便民": ["convenient", "accessible", "facilities"],
                "海边": ["coastal", "beachside", "waterfront"],
                "学校": ["school_zone", "education", "family_friendly"]
            }
        }
    
    def translate_intent_to_search_params(self, user_intent: Dict, geo_analysis: Dict = None) -> Dict[str, Any]:
        """
        Convert user intent into search parameters for URL construction.
        
        Args:
            user_intent: Dictionary containing extracted user intent
            geo_analysis: Optional geographical analysis results
            
        Returns:
            Dictionary with parameters ready for URL builder
        """
        search_params = {
            'suburb': None,
            'property_type': 'rent',  # Default to rent
            'bedrooms': None,
            'min_price': None,
            'max_price': None,
            'bathrooms': None,
            'parking': None,
            'property_style': None,
            'features': [],
            'alternative_suburbs': []
        }
        
        # Extract basic parameters
        search_params.update(self._extract_basic_params(user_intent))
        
        # Process price information
        search_params.update(self._process_price_info(user_intent, search_params))
        
        # Handle property type and style
        search_params.update(self._process_property_type(user_intent))
        
        # Process location preferences
        search_params.update(self._process_location_preferences(user_intent, geo_analysis))
        
        # Handle size preferences and inferred needs
        search_params.update(self._process_size_preferences(user_intent))
        
        # Add special requirements as features
        search_params['features'] = self._extract_features(user_intent)
        
        return search_params
    
    def _extract_basic_params(self, intent: Dict) -> Dict[str, Any]:
        """Extract basic search parameters from intent."""
        params = {}
        
        # Suburb
        if intent.get('suburb'):
            params['suburb'] = intent['suburb']
        
        # Bedrooms
        if intent.get('bedrooms'):
            params['bedrooms'] = intent['bedrooms']
        
        # Bathrooms (if specified)
        if intent.get('bathrooms'):
            params['bathrooms'] = intent['bathrooms']
        
        return params
    
    def _process_price_info(self, intent: Dict, search_params: Dict) -> Dict[str, Any]:
        """Process price information and convert to appropriate format."""
        params = {}
        
        budget = intent.get('budget')
        if not budget:
            return params
        
        # Determine if this is rent or buy based on price range
        property_type = self._infer_property_type_from_price(budget)
        params['property_type'] = property_type
        
        # Convert price based on property type
        if property_type == 'rent':
            # Budget is likely weekly rent in AUD
            params['max_price'] = budget
        elif property_type == 'buy':
            # Budget is likely total purchase price
            if budget < 10000:  # Assume this is in 10k units (e.g., "100万" = 100 * 10k)
                params['max_price'] = budget * 10000
            else:
                params['max_price'] = budget
        
        # Apply budget modifiers if specified in intent
        if intent.get('priority_analysis'):
            analysis = intent['priority_analysis'].lower()
            if any(keyword in analysis for keyword in ['灵活', 'flexible', '可以超']):
                # Allow 20% budget flexibility
                if params.get('max_price'):
                    params['max_price'] *= 1.2
        
        return params
    
    def _infer_property_type_from_price(self, budget: float) -> str:
        """Infer whether user wants to rent or buy based on budget range."""
        if budget <= 2000:  # Likely weekly rent
            return 'rent'
        elif budget <= 10000:  # Could be weekly rent or monthly budget
            return 'rent'  # Default to rent for ambiguous cases
        else:  # Likely purchase price
            return 'buy'
    
    def _process_property_type(self, intent: Dict) -> Dict[str, Any]:
        """Process property type and style preferences."""
        params = {}
        
        # Check for explicit property type mentions
        property_type = intent.get('property_type')
        if property_type and property_type.lower() in self.property_type_mapping:
            params['property_style'] = self.property_type_mapping[property_type.lower()]
        
        # Check inferred needs for property type hints
        inferred_needs = intent.get('inferred_needs', [])
        for need in inferred_needs:
            need_lower = need.lower()
            for key, value in self.property_type_mapping.items():
                if key in need_lower:
                    params['property_style'] = value
                    break
        
        return params
    
    def _process_location_preferences(self, intent: Dict, geo_analysis: Dict = None) -> Dict[str, Any]:
        """Process location preferences and geographical analysis."""
        params = {}
        
        # Use geographical analysis if available
        if geo_analysis:
            location_analysis = geo_analysis.get('location_analysis', {})
            recommended_areas = location_analysis.get('recommended_areas', [])
            
            if recommended_areas and not intent.get('suburb'):
                # Use first recommended area if no specific suburb requested
                params['suburb'] = recommended_areas[0]
                params['alternative_suburbs'] = recommended_areas[1:10]  # Up to 10 alternatives
        
        # Process distance preferences
        distance_pref = intent.get('distance_from_city')
        if distance_pref and distance_pref in self.location_preferences['distance_preferences']:
            # This could be used to expand suburb search in future versions
            pass
        
        return params
    
    def _process_size_preferences(self, intent: Dict) -> Dict[str, Any]:
        """Process size preferences and infer room requirements."""
        params = {}
        
        size_preference = intent.get('size_preference')
        current_bedrooms = intent.get('bedrooms')
        
        if size_preference == '大' and not current_bedrooms:
            # User wants "big" house but didn't specify bedrooms
            params['bedrooms'] = 3  # Default to 3BR for "big"
        elif size_preference == '小' and not current_bedrooms:
            # User wants "small" place
            params['bedrooms'] = 1  # Default to 1BR for "small"
        
        # Check for inferred bedroom needs from AI analysis
        inferred_needs = intent.get('inferred_needs', [])
        for need in inferred_needs:
            bedroom_match = re.search(r'(\d+)\s*[室房bedroom]', need.lower())
            if bedroom_match and not params.get('bedrooms'):
                params['bedrooms'] = int(bedroom_match.group(1))
        
        return params
    
    def _extract_features(self, intent: Dict) -> List[str]:
        """Extract property features from special requirements."""
        features = []
        
        special_requirements = intent.get('special_requirements', [])
        feature_mapping = {
            '停车': 'parking',
            '车位': 'parking', 
            '游泳池': 'pool',
            '健身房': 'gym',
            '阳台': 'balcony',
            '花园': 'garden',
            '海景': 'ocean_view',
            '学校': 'near_school',
            '交通': 'transport'
        }
        
        for requirement in special_requirements:
            for chinese_term, english_feature in feature_mapping.items():
                if chinese_term in requirement:
                    features.append(english_feature)
        
        return features
    
    def generate_search_urls(self, user_intent: Dict, geo_analysis: Dict = None, 
                           sites: List[str] = None, pages: int = 3) -> List[Dict[str, Any]]:
        """
        Generate complete search URLs from user intent.
        
        Args:
            user_intent: Extracted user intent
            geo_analysis: Geographical analysis results
            sites: List of sites to search (default: all)
            pages: Number of pages per site to generate
            
        Returns:
            List of URL data with metadata
        """
        # Translate intent to search parameters
        search_params = self.translate_intent_to_search_params(user_intent, geo_analysis)
        
        # Validate that we have enough information for a search
        if not any([search_params.get('suburb'), search_params.get('bedrooms'), 
                   search_params.get('max_price')]):
            # Try alternative suburbs if available
            if search_params.get('alternative_suburbs'):
                search_params['suburb'] = search_params['alternative_suburbs'][0]
            else:
                raise ValueError("Insufficient search criteria - need at least suburb, bedrooms, or price")
        
        all_urls = []
        
        # Generate URLs for primary suburb
        if search_params.get('suburb'):
            try:
                urls = self.url_builder.build_search_urls(
                    suburb=search_params['suburb'],
                    property_type=search_params.get('property_type', 'rent'),
                    bedrooms=search_params.get('bedrooms'),
                    min_price=search_params.get('min_price'),
                    max_price=search_params.get('max_price'),
                    bathrooms=search_params.get('bathrooms'),
                    parking=search_params.get('parking'),
                    property_style=search_params.get('property_style'),
                    features=search_params.get('features', []),
                    sites=sites
                )
                
                # Add metadata
                for url_data in urls:
                    url_data['search_params'] = search_params
                    url_data['priority'] = 'primary'
                
                all_urls.extend(urls)
                
                # Generate pagination URLs if requested
                if pages > 1:
                    for url_data in urls:
                        pagination_urls = self.url_builder.get_pagination_urls(url_data, pages)
                        for page_url in pagination_urls[1:]:  # Skip page 1 (already included)
                            page_url['search_params'] = search_params
                            page_url['priority'] = 'pagination'
                        all_urls.extend(pagination_urls[1:])
                
            except Exception as e:
                print(f"Error generating URLs for suburb {search_params['suburb']}: {e}")
        
        # Generate URLs for alternative suburbs (if primary suburb fails or for broader search)
        alternative_suburbs = search_params.get('alternative_suburbs', [])[:3]  # Limit to 3 alternatives
        for alt_suburb in alternative_suburbs:
            try:
                search_params_alt = search_params.copy()
                search_params_alt['suburb'] = alt_suburb
                
                urls = self.url_builder.build_search_urls(
                    suburb=alt_suburb,
                    property_type=search_params.get('property_type', 'rent'),
                    bedrooms=search_params.get('bedrooms'),
                    min_price=search_params.get('min_price'),
                    max_price=search_params.get('max_price'),
                    bathrooms=search_params.get('bathrooms'),
                    parking=search_params.get('parking'),
                    property_style=search_params.get('property_style'),
                    features=search_params.get('features', []),
                    sites=sites,
                    page=1  # Only first page for alternatives
                )
                
                # Add metadata
                for url_data in urls:
                    url_data['search_params'] = search_params_alt
                    url_data['priority'] = 'alternative'
                
                all_urls.extend(urls)
                
            except Exception as e:
                print(f"Error generating URLs for alternative suburb {alt_suburb}: {e}")
                continue
        
        return all_urls
    
    def optimize_search_strategy(self, user_intent: Dict, geo_analysis: Dict = None) -> Dict[str, Any]:
        """
        Generate an optimized search strategy based on user intent.
        
        Returns:
            Dictionary with search strategy recommendations
        """
        strategy = {
            'primary_search': {},
            'fallback_searches': [],
            'recommendations': []
        }
        
        search_params = self.translate_intent_to_search_params(user_intent, geo_analysis)
        
        # Primary search strategy
        strategy['primary_search'] = search_params
        
        # Generate fallback strategies
        fallback_strategies = []
        
        # Fallback 1: Relax price constraint by 20%
        if search_params.get('max_price'):
            relaxed_price = search_params.copy()
            relaxed_price['max_price'] *= 1.2
            relaxed_price['strategy_name'] = 'relaxed_budget'
            fallback_strategies.append(relaxed_price)
        
        # Fallback 2: Expand to nearby suburbs
        if search_params.get('alternative_suburbs'):
            nearby_search = search_params.copy()
            nearby_search['suburb'] = None  # Will use alternatives
            nearby_search['strategy_name'] = 'nearby_areas'
            fallback_strategies.append(nearby_search)
        
        # Fallback 3: Adjust bedroom requirement
        if search_params.get('bedrooms') and search_params['bedrooms'] > 1:
            fewer_bedrooms = search_params.copy()
            fewer_bedrooms['bedrooms'] -= 1
            fewer_bedrooms['strategy_name'] = 'fewer_bedrooms'
            fallback_strategies.append(fewer_bedrooms)
        
        strategy['fallback_searches'] = fallback_strategies
        
        # Generate recommendations
        recommendations = []
        
        if search_params.get('property_type') == 'buy' and search_params.get('max_price', 0) < 500000:
            recommendations.append("Consider expanding search to outer suburbs for better value")
        
        if search_params.get('bedrooms', 0) >= 3 and search_params.get('property_type') == 'rent':
            recommendations.append("3+ bedroom rentals are competitive - consider flexible move-in dates")
        
        if not search_params.get('suburb') and len(search_params.get('alternative_suburbs', [])) > 5:
            recommendations.append("Multiple areas match your preferences - consider transport connections")
        
        strategy['recommendations'] = recommendations
        
        return strategy

if __name__ == "__main__":
    # Test the intent translator
    translator = IntentToURLTranslator()
    
    print("Testing Intent to URL Translator")
    print("=" * 50)
    
    # Test case 1: Rent apartment in Bondi
    test_intent_1 = {
        'suburb': 'Bondi',
        'bedrooms': 2,
        'budget': 800,
        'size_preference': '中',
        'location_preference': '海边',
        'special_requirements': ['停车位', '阳台'],
        'inferred_needs': ['靠近海滩', '交通便利']
    }
    
    print("Test 1: Rent 2BR in Bondi with parking")
    print("-" * 30)
    search_params = translator.translate_intent_to_search_params(test_intent_1)
    print(f"Search Parameters: {search_params}")
    
    try:
        urls = translator.generate_search_urls(test_intent_1, pages=2)
        print(f"Generated {len(urls)} URLs")
        for url_data in urls[:3]:  # Show first 3
            print(f"  {url_data['site']}: {url_data['url'][:80]}...")
    except Exception as e:
        print(f"Error generating URLs: {e}")
    
    print()
    
    # Test case 2: Buy house with flexible requirements
    test_intent_2 = {
        'bedrooms': 3,
        'budget': 120,  # 120万
        'size_preference': '大',
        'location_preference': '郊外',
        'distance_from_city': '远',
        'special_requirements': ['学校附近', '花园'],
        'inferred_needs': ['家庭友好', '性价比高']
    }
    
    # Mock geo analysis
    mock_geo = {
        'location_analysis': {
            'recommended_areas': ['Castle Hill', 'Kellyville', 'Blacktown', 'Liverpool'],
            'distance_preference': '远',
            'area_characteristics': ['家庭友好', '性价比高']
        }
    }
    
    print("Test 2: Buy 3BR family house in outer suburbs")
    print("-" * 30)
    search_params = translator.translate_intent_to_search_params(test_intent_2, mock_geo)
    print(f"Search Parameters: {search_params}")
    
    try:
        strategy = translator.optimize_search_strategy(test_intent_2, mock_geo)
        print(f"Search Strategy: {strategy['primary_search']['suburb']} + {len(strategy['fallback_searches'])} fallbacks")
        print(f"Recommendations: {strategy['recommendations']}")
    except Exception as e:
        print(f"Error generating strategy: {e}")