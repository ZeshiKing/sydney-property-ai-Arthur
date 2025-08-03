"""
Live Recommendation Engine
Integrates all components to provide real-time property recommendations using live data.
Combines URL building, data fetching, deduplication, and AI analysis.
"""

import asyncio
import time
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import sys
import os

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from backend.services.intent_to_url_translator import IntentToURLTranslator
from backend.services.concurrent_property_fetcher import ConcurrentPropertyFetcher
from backend.services.property_deduplicator import PropertyDeduplicator, DeduplicationResult
from backend.models.property import Property, UserIntent
import anthropic

class LiveRecommendationEngine:
    """
    Enhanced recommendation engine that provides real-time property recommendations
    using live data from multiple property websites.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 cache_ttl_minutes: int = 30,
                 max_properties_per_site: int = 20,
                 enable_fallback_to_static: bool = True):
        """
        Initialize the live recommendation engine.
        
        Args:
            api_key: Anthropic API key for Claude integration
            cache_ttl_minutes: Cache duration for fetched data
            max_properties_per_site: Maximum properties to fetch per site
            enable_fallback_to_static: Whether to fallback to static data on failure
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.enable_fallback_to_static = enable_fallback_to_static
        
        # Initialize components
        self.intent_translator = IntentToURLTranslator()
        self.property_fetcher = ConcurrentPropertyFetcher(
            cache_ttl_minutes=cache_ttl_minutes,
            max_concurrent_total=8
        )
        self.deduplicator = PropertyDeduplicator()
        
        # Configuration
        self.max_properties_per_site = max_properties_per_site
        self.supported_sites = ['realestate.com.au', 'domain.com.au', 'rent.com.au']
        
        # Performance metrics
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'average_response_time': 0,
            'cache_hit_rate': 0,
            'fallback_usage': 0
        }
    
    async def get_live_recommendations(self, 
                                     user_input: str,
                                     user_intent: Dict[str, Any],
                                     geo_analysis: Dict[str, Any] = None,
                                     max_recommendations: int = 5,
                                     include_alternatives: bool = True) -> Dict[str, Any]:
        """
        Get live property recommendations based on user intent.
        
        Args:
            user_input: Original user input text
            user_intent: Extracted user intent from AI
            geo_analysis: Geographical analysis results
            max_recommendations: Maximum number of recommendations to return
            include_alternatives: Whether to include alternative options
            
        Returns:
            Dictionary containing recommendations, metadata, and performance info
        """
        start_time = time.time()
        self.metrics['total_requests'] += 1
        
        try:
            # Phase 1: Generate search URLs
            search_urls = self.intent_translator.generate_search_urls(
                user_intent=user_intent,
                geo_analysis=geo_analysis,
                sites=self.supported_sites,
                pages=2  # Fetch first 2 pages
            )
            
            if not search_urls:
                raise ValueError("No search URLs could be generated from user intent")
            
            # Phase 2: Fetch live property data
            print(f"Fetching from {len(search_urls)} URLs across {len(self.supported_sites)} sites...")
            fetch_results = await self.property_fetcher.fetch_properties_concurrent(search_urls)
            
            # Phase 3: Extract and combine properties
            all_properties = []
            fetch_metadata = {
                'successful_fetches': 0,
                'failed_fetches': 0,
                'total_properties_found': 0,
                'sites_data': {}
            }
            
            for result in fetch_results:
                site_data = {
                    'success': result.success,
                    'properties_found': len(result.properties),
                    'response_time_ms': result.response_time_ms,
                    'error': result.error
                }
                fetch_metadata['sites_data'][result.site] = site_data
                
                if result.success:
                    all_properties.extend(result.properties)
                    fetch_metadata['successful_fetches'] += 1
                    fetch_metadata['total_properties_found'] += len(result.properties)
                else:
                    fetch_metadata['failed_fetches'] += 1
            
            # Phase 4: Deduplicate and standardize
            if all_properties:
                dedup_result = self.deduplicator.deduplicate_properties(all_properties)
                unique_properties = dedup_result.unique_properties
            else:
                # Fallback to static data if enabled and no live data found
                if self.enable_fallback_to_static:
                    print("No live properties found, falling back to static data...")
                    unique_properties = await self._get_static_fallback_properties(user_intent, geo_analysis)
                    self.metrics['fallback_usage'] += 1
                else:
                    unique_properties = []
            
            # Phase 5: Generate AI recommendations
            if unique_properties:
                ai_recommendations = await self._generate_ai_recommendations(
                    user_input=user_input,
                    user_intent=user_intent,
                    properties=unique_properties[:20],  # Limit for AI processing
                    geo_analysis=geo_analysis,
                    max_recommendations=max_recommendations
                )
            else:
                ai_recommendations = {
                    'recommendations': ["Sorry, no properties found matching your criteria. Try adjusting your search parameters."],
                    'analysis': "No properties available for analysis.",
                    'suggestions': ["Consider expanding your search area", "Increase your budget range", "Reduce bedroom requirements"]
                }
            
            # Phase 6: Compile final response
            response_time = time.time() - start_time
            self.metrics['successful_requests'] += 1
            self.metrics['average_response_time'] = (
                (self.metrics['average_response_time'] * (self.metrics['total_requests'] - 1) + response_time) 
                / self.metrics['total_requests']
            )
            
            return {
                'recommendations': ai_recommendations['recommendations'],
                'analysis': ai_recommendations.get('analysis', ''),
                'suggestions': ai_recommendations.get('suggestions', []),
                'properties_data': {
                    'total_found': len(unique_properties),
                    'total_raw': fetch_metadata['total_properties_found'],
                    'duplicates_removed': fetch_metadata['total_properties_found'] - len(unique_properties),
                    'properties': unique_properties[:10] if include_alternatives else []
                },
                'metadata': {
                    'search_urls_generated': len(search_urls),
                    'fetch_results': fetch_metadata,
                    'processing_time_ms': int(response_time * 1000),
                    'data_source': 'live' if all_properties else 'static_fallback',
                    'deduplication': dedup_result.__dict__ if 'dedup_result' in locals() else None
                },
                'success': True
            }
            
        except Exception as e:
            print(f"Error in live recommendation engine: {e}")
            
            # Try fallback to static data
            if self.enable_fallback_to_static:
                try:
                    static_properties = await self._get_static_fallback_properties(user_intent, geo_analysis)
                    if static_properties:
                        ai_recommendations = await self._generate_ai_recommendations(
                            user_input=user_input,
                            user_intent=user_intent,
                            properties=static_properties[:10],
                            geo_analysis=geo_analysis,
                            max_recommendations=max_recommendations
                        )
                        
                        response_time = time.time() - start_time
                        self.metrics['fallback_usage'] += 1
                        
                        return {
                            'recommendations': ai_recommendations['recommendations'],
                            'analysis': ai_recommendations.get('analysis', ''),
                            'suggestions': ai_recommendations.get('suggestions', []),
                            'properties_data': {
                                'total_found': len(static_properties),
                                'properties': static_properties[:10] if include_alternatives else []
                            },
                            'metadata': {
                                'processing_time_ms': int(response_time * 1000),
                                'data_source': 'static_fallback',
                                'error': str(e)
                            },
                            'success': True
                        }
                except Exception as fallback_error:
                    print(f"Fallback also failed: {fallback_error}")
            
            # Complete failure
            response_time = time.time() - start_time
            return {
                'recommendations': ["Sorry, we're experiencing technical difficulties. Please try again later."],
                'analysis': f"Error occurred: {str(e)}",
                'suggestions': ["Try again in a few minutes", "Check your search criteria", "Contact support if the problem persists"],
                'properties_data': {'total_found': 0, 'properties': []},
                'metadata': {
                    'processing_time_ms': int(response_time * 1000),
                    'data_source': 'error',
                    'error': str(e)
                },
                'success': False
            }
    
    async def _generate_ai_recommendations(self, 
                                         user_input: str,
                                         user_intent: Dict[str, Any],
                                         properties: List[Property],
                                         geo_analysis: Dict[str, Any] = None,
                                         max_recommendations: int = 5) -> Dict[str, Any]:
        """Generate AI-powered recommendations using Claude."""
        
        if not self.api_key:
            return {
                'recommendations': [self._generate_fallback_recommendation(prop) for prop in properties[:max_recommendations]],
                'analysis': "AI analysis unavailable - missing API key",
                'suggestions': ["Configure API key for enhanced recommendations"]
            }
        
        try:
            client = anthropic.Anthropic(api_key=self.api_key)
            
            # Prepare properties data for Claude
            properties_text = []
            for i, prop in enumerate(properties[:15], 1):  # Limit to avoid token limits
                prop_text = f"""
Property {i}:
- Address: {prop.address}
- Price: {prop.price}
- Bedrooms: {prop.bedrooms}
- Bathrooms: {prop.bathrooms}
- Parking: {prop.parking}
- Type: {prop.property_type}
- Link: {prop.link}
"""
                properties_text.append(prop_text)
            
            # Build context
            context_parts = []
            
            if user_intent.get('inferred_needs'):
                context_parts.append(f"AI推测的隐含需求: {', '.join(user_intent['inferred_needs'])}")
            
            if user_intent.get('priority_analysis'):
                context_parts.append(f"需求优先级分析: {user_intent['priority_analysis']}")
            
            if geo_analysis and geo_analysis.get('comprehensive_recommendations', {}).get('search_strategy'):
                context_parts.append(f"地理分析策略: {geo_analysis['comprehensive_recommendations']['search_strategy']}")
            
            additional_context = "\n".join(context_parts) if context_parts else "无额外分析上下文"
            
            prompt = f"""你是一位专业的房产推荐顾问，基于用户需求和实时房源数据提供个性化推荐。

用户原始需求：{user_input}

🧠 AI深度分析：
{additional_context}

📊 实时房源数据（共{len(properties)}套房源）：
{"".join(properties_text)}

请基于以下原则提供推荐：

1. **智能匹配**：
   - 优先匹配用户明确需求
   - 考虑AI推测的隐含需求
   - 结合地理位置偏好和实时市场情况

2. **个性化推荐理由**：
   - 解释为什么这个房源特别适合用户
   - 结合用户的口语化表达（如"大一点的"、"离市区远"）
   - 说明房源如何满足用户的生活方式需求

3. **实时市场洞察**：
   - 基于当前可用房源提供市场分析
   - 识别性价比最优选择
   - 提供替代建议和市场趋势

请提供：
1. 3-5条个性化推荐（格式：推荐X：[房源地址 - 价格] - [详细推荐理由]）
2. 市场分析总结
3. 搜索优化建议（如果当前结果不理想）

输出格式：
推荐1：...
推荐2：...
推荐3：...

市场分析：[基于实时数据的分析]

搜索建议：[优化建议1, 优化建议2, 优化建议3]"""
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            
            # Parse the response
            recommendations = []
            analysis = ""
            suggestions = []
            
            lines = content.split('\n')
            current_section = "recommendations"
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('推荐') and '：' in line:
                    recommendations.append(line.split('：', 1)[1])
                elif line.startswith('市场分析：'):
                    current_section = "analysis"
                    analysis = line.split('：', 1)[1]
                elif line.startswith('搜索建议：'):
                    current_section = "suggestions"
                    suggestions_text = line.split('：', 1)[1]
                    suggestions = [s.strip() for s in suggestions_text.split(',')]
                elif current_section == "analysis" and line:
                    analysis += " " + line
                elif current_section == "suggestions" and line and ',' in line:
                    suggestions.extend([s.strip() for s in line.split(',')])
            
            # Fallback parsing if structured parsing fails
            if not recommendations:
                recommendation_lines = [l for l in lines if l.strip() and not l.startswith(('市场分析', '搜索建议'))]
                recommendations = recommendation_lines[:max_recommendations]
            
            return {
                'recommendations': recommendations[:max_recommendations],
                'analysis': analysis.strip() if analysis else "基于实时房源数据的智能分析",
                'suggestions': [s for s in suggestions if s][:3]
            }
            
        except Exception as e:
            print(f"AI recommendation generation failed: {e}")
            return {
                'recommendations': [self._generate_fallback_recommendation(prop) for prop in properties[:max_recommendations]],
                'analysis': f"AI分析暂时不可用: {str(e)}",
                'suggestions': ["请稍后重试", "检查网络连接", "联系技术支持"]
            }
    
    def _generate_fallback_recommendation(self, property: Property) -> str:
        """Generate a simple fallback recommendation without AI."""
        features = []
        if property.bedrooms > 0:
            features.append(f"{property.bedrooms}室")
        if property.bathrooms > 0:
            features.append(f"{property.bathrooms}浴")
        if property.parking > 0:
            features.append(f"{property.parking}车位")
        
        features_text = "/".join(features) if features else "详情见链接"
        
        return f"{property.address} - {property.price} - {features_text} - 符合您的基本需求"
    
    async def _get_static_fallback_properties(self, 
                                            user_intent: Dict[str, Any], 
                                            geo_analysis: Dict[str, Any] = None) -> List[Property]:
        """Get properties from static CSV data as fallback."""
        try:
            # Import the original function for static data
            from recommend_claude import filter_properties_flexible, load_property_data
            
            df = load_property_data()
            
            # Convert user_intent to the format expected by the static function
            suburb = user_intent.get('suburb')
            bedrooms = user_intent.get('bedrooms') 
            budget = user_intent.get('budget')
            
            # Apply filters
            filtered_df = filter_properties_flexible(
                df=df,
                suburb=suburb,
                bedrooms=bedrooms,
                budget=budget,
                geo_analysis=geo_analysis,
                intent_analysis={'size_analysis': {}}
            )
            
            # Convert DataFrame to Property objects
            properties = []
            for _, row in filtered_df.head(10).iterrows():
                try:
                    prop = Property(
                        address=row['address'],
                        suburb=row['suburb'], 
                        price=row['price'],
                        price_numeric=row.get('price_numeric'),
                        bedrooms=int(row.get('bedrooms', 0)),
                        bathrooms=int(row.get('bathrooms', 0)),
                        parking=int(row.get('parking', 0)),
                        property_type=row.get('property_type', 'Unknown'),
                        link=row.get('link', '')
                    )
                    properties.append(prop)
                except Exception as e:
                    print(f"Error converting row to Property: {e}")
                    continue
            
            return properties
            
        except Exception as e:
            print(f"Static fallback failed: {e}")
            return []
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the recommendation engine."""
        return {
            **self.metrics,
            'cache_stats': self.property_fetcher.get_cache_stats(),
            'uptime': datetime.now().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health_status = {
            'overall_status': 'healthy',
            'components': {},
            'last_check': datetime.now().isoformat()
        }
        
        try:
            # Check property fetcher
            fetcher_health = await self.property_fetcher.health_check()
            health_status['components']['property_fetcher'] = fetcher_health
            
            # Check AI API
            if self.api_key:
                try:
                    client = anthropic.Anthropic(api_key=self.api_key)
                    # Simple test call
                    test_response = client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=10,
                        messages=[{"role": "user", "content": "Hello"}]
                    )
                    health_status['components']['ai_api'] = {'status': 'healthy'}
                except Exception as e:
                    health_status['components']['ai_api'] = {'status': 'error', 'error': str(e)}
            else:
                health_status['components']['ai_api'] = {'status': 'not_configured'}
            
            # Check overall health
            unhealthy_components = [
                name for name, status in health_status['components'].items()
                if isinstance(status, dict) and status.get('status') != 'healthy'
            ]
            
            if unhealthy_components:
                health_status['overall_status'] = 'degraded'
                
        except Exception as e:
            health_status['overall_status'] = 'error'
            health_status['error'] = str(e)
        
        return health_status

# Test function
async def test_live_recommendation_engine():
    """Test the live recommendation engine."""
    
    print("Testing Live Recommendation Engine")
    print("=" * 50)
    
    # Initialize engine (without real API key for testing)
    engine = LiveRecommendationEngine(
        api_key=None,  # Will use fallback recommendations
        cache_ttl_minutes=15,
        enable_fallback_to_static=True
    )
    
    # Test intent
    test_intent = {
        'suburb': 'Bondi',
        'bedrooms': 2, 
        'budget': 800,  # $800/week
        'property_type': 'rent',
        'special_requirements': ['parking'],
        'inferred_needs': ['靠近海滩', '交通便利']
    }
    
    test_geo_analysis = {
        'location_analysis': {
            'recommended_areas': ['Bondi', 'Bondi Beach', 'North Bondi'],
            'distance_preference': '近',
            'area_characteristics': ['海滨', '便利']
        }
    }
    
    # Test health check first
    print("Performing health check...")
    health = await engine.health_check()
    print(f"Overall status: {health['overall_status']}")
    
    # Note: In a real test environment, this would make actual HTTP requests
    # For demo purposes, we'll simulate the process
    print("\nNote: This is a demo - actual web scraping would require proper setup")
    print("The system would:")
    print("1. Generate search URLs for Bondi rental properties")
    print("2. Fetch live data from realestate.com.au, domain.com.au, rent.com.au") 
    print("3. Deduplicate and standardize the results")
    print("4. Generate AI recommendations based on live data")
    
    # Show metrics
    metrics = engine.get_performance_metrics()
    print(f"\nEngine metrics: {metrics}")

if __name__ == "__main__":
    asyncio.run(test_live_recommendation_engine())