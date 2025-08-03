"""
Concurrent Property Fetcher
Handles live data acquisition from multiple property websites with concurrent processing,
rate limiting, error handling, and response caching.
"""

import asyncio
import aiohttp
import time
import random
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import hashlib
import os
import sys

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from backend.models.property import Property

@dataclass
class FetchResult:
    """Result of a property fetch operation."""
    url: str
    site: str
    success: bool
    status_code: Optional[int] = None
    content: Optional[str] = None
    properties: List[Property] = None
    error: Optional[str] = None
    fetch_time: Optional[datetime] = None
    response_time_ms: Optional[int] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = []
        if self.fetch_time is None:
            self.fetch_time = datetime.now()

@dataclass
class SiteConfig:
    """Configuration for a property website."""
    name: str
    base_domain: str
    rate_limit_delay: float  # Seconds between requests
    max_concurrent: int
    headers: Dict[str, str]
    timeout: int
    retry_attempts: int
    parser_class: str

class PropertyFetchCache:
    """Simple in-memory cache for property fetch results."""
    
    def __init__(self, cache_ttl_minutes: int = 30):
        self.cache = {}
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
    
    def _generate_key(self, url: str) -> str:
        """Generate cache key from URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def get(self, url: str) -> Optional[FetchResult]:
        """Get cached result if not expired."""
        key = self._generate_key(url)
        if key in self.cache:
            result, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.cache_ttl:
                return result
            else:
                # Remove expired entry
                del self.cache[key]
        return None
    
    def set(self, url: str, result: FetchResult):
        """Cache the result."""
        key = self._generate_key(url)
        self.cache[key] = (result, datetime.now())
    
    def clear_expired(self):
        """Remove expired cache entries."""
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if now - timestamp >= self.cache_ttl
        ]
        for key in expired_keys:
            del self.cache[key]

class RateLimiter:
    """Rate limiter for website requests."""
    
    def __init__(self):
        self.last_request_times = {}
    
    async def wait_if_needed(self, site: str, delay: float):
        """Wait if necessary to respect rate limit."""
        if site in self.last_request_times:
            elapsed = time.time() - self.last_request_times[site]
            if elapsed < delay:
                wait_time = delay - elapsed
                await asyncio.sleep(wait_time)
        
        self.last_request_times[site] = time.time()

class ConcurrentPropertyFetcher:
    """
    Handles concurrent fetching of property data from multiple websites.
    Includes rate limiting, caching, error handling, and response parsing.
    """
    
    def __init__(self, cache_ttl_minutes: int = 30, max_concurrent_total: int = 10):
        """
        Initialize the concurrent property fetcher.
        
        Args:
            cache_ttl_minutes: Cache time-to-live in minutes
            max_concurrent_total: Maximum total concurrent requests across all sites
        """
        self.cache = PropertyFetchCache(cache_ttl_minutes)
        self.rate_limiter = RateLimiter()
        self.max_concurrent_total = max_concurrent_total
        self.semaphore = asyncio.Semaphore(max_concurrent_total)
        
        # Site configurations
        self.site_configs = {
            'realestate.com.au': SiteConfig(
                name='realestate.com.au',
                base_domain='realestate.com.au',
                rate_limit_delay=2.0,  # 2 seconds between requests
                max_concurrent=3,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                },
                timeout=30,
                retry_attempts=3,
                parser_class='RealEstateParser'
            ),
            'domain.com.au': SiteConfig(
                name='domain.com.au',
                base_domain='domain.com.au',
                rate_limit_delay=1.5,  # 1.5 seconds between requests
                max_concurrent=4,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-AU,en;q=0.9',
                    'Cache-Control': 'no-cache',
                },
                timeout=25,
                retry_attempts=3,
                parser_class='DomainParser'
            ),
            'rent.com.au': SiteConfig(
                name='rent.com.au',
                base_domain='rent.com.au',
                rate_limit_delay=1.0,  # 1 second between requests
                max_concurrent=5,
                headers={
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                },
                timeout=20,
                retry_attempts=2,
                parser_class='RentParser'
            )
        }
    
    async def fetch_properties_concurrent(self, url_data_list: List[Dict[str, Any]]) -> List[FetchResult]:
        """
        Fetch properties from multiple URLs concurrently.
        
        Args:
            url_data_list: List of URL data dictionaries from URL builder
            
        Returns:
            List of FetchResult objects
        """
        # Clear expired cache entries
        self.cache.clear_expired()
        
        # Group URLs by site for proper rate limiting
        urls_by_site = {}
        for url_data in url_data_list:
            site = url_data['site']
            if site not in urls_by_site:
                urls_by_site[site] = []
            urls_by_site[site].append(url_data)
        
        # Create tasks for each site
        tasks = []
        for site, site_urls in urls_by_site.items():
            if site in self.site_configs:
                task = self._fetch_site_urls(site, site_urls)
                tasks.append(task)
        
        # Execute all tasks concurrently
        results = []
        if tasks:
            site_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for site_result in site_results:
                if isinstance(site_result, Exception):
                    print(f"Site fetch error: {site_result}")
                    continue
                
                if isinstance(site_result, list):
                    results.extend(site_result)
                else:
                    results.append(site_result)
        
        return results
    
    async def _fetch_site_urls(self, site: str, url_data_list: List[Dict[str, Any]]) -> List[FetchResult]:
        """Fetch all URLs for a specific site with rate limiting."""
        config = self.site_configs[site]
        semaphore = asyncio.Semaphore(config.max_concurrent)
        
        async def fetch_single_url(url_data: Dict[str, Any]) -> FetchResult:
            async with semaphore:
                return await self._fetch_single_property_page(url_data, config)
        
        # Create tasks for all URLs
        tasks = [fetch_single_url(url_data) for url_data in url_data_list]
        
        # Execute with rate limiting
        results = []
        for task in tasks:
            # Rate limiting delay
            await self.rate_limiter.wait_if_needed(site, config.rate_limit_delay)
            
            try:
                result = await task
                results.append(result)
            except Exception as e:
                # Create error result
                url = url_data_list[len(results)]['url'] if len(results) < len(url_data_list) else 'unknown'
                error_result = FetchResult(
                    url=url,
                    site=site,
                    success=False,
                    error=f"Task execution error: {str(e)}"
                )
                results.append(error_result)
        
        return results
    
    async def _fetch_single_property_page(self, url_data: Dict[str, Any], config: SiteConfig) -> FetchResult:
        """Fetch a single property page with caching and error handling."""
        url = url_data['url']
        site = url_data['site']
        
        # Check cache first
        cached_result = self.cache.get(url)
        if cached_result:
            return cached_result
        
        # Prepare result object
        result = FetchResult(url=url, site=site, success=False)
        
        async with self.semaphore:  # Global concurrency limit
            start_time = time.time()
            
            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=config.timeout),
                    headers=config.headers
                ) as session:
                    
                    # Retry logic
                    last_exception = None
                    for attempt in range(config.retry_attempts):
                        try:
                            # Add random delay to avoid thundering herd
                            if attempt > 0:
                                await asyncio.sleep(random.uniform(1, 3))
                            
                            async with session.get(url) as response:
                                response_time = int((time.time() - start_time) * 1000)
                                result.status_code = response.status
                                result.response_time_ms = response_time
                                
                                if response.status == 200:
                                    content = await response.text()
                                    result.content = content
                                    result.success = True
                                    
                                    # Parse properties from content
                                    properties = await self._parse_properties(content, site, url_data)
                                    result.properties = properties
                                    
                                    # Cache successful result
                                    self.cache.set(url, result)
                                    break
                                    
                                elif response.status == 429:  # Rate limited
                                    result.error = f"Rate limited (429) on attempt {attempt + 1}"
                                    await asyncio.sleep(5)  # Wait longer for rate limit
                                    continue
                                    
                                elif response.status in [403, 404]:  # Client errors
                                    result.error = f"Client error {response.status}"
                                    break  # Don't retry client errors
                                    
                                else:  # Server errors
                                    result.error = f"HTTP {response.status} on attempt {attempt + 1}"
                                    continue
                                    
                        except asyncio.TimeoutError:
                            last_exception = "Request timeout"
                            result.error = f"Timeout on attempt {attempt + 1}"
                            continue
                            
                        except aiohttp.ClientError as e:
                            last_exception = str(e)
                            result.error = f"Client error on attempt {attempt + 1}: {str(e)}"
                            continue
                            
                        except Exception as e:
                            last_exception = str(e)
                            result.error = f"Unexpected error on attempt {attempt + 1}: {str(e)}"
                            continue
                    
                    # If we exhausted all retries
                    if not result.success and last_exception:
                        result.error = f"Failed after {config.retry_attempts} attempts. Last error: {last_exception}"
                        
            except Exception as e:
                result.error = f"Session error: {str(e)}"
        
        return result
    
    async def _parse_properties(self, content: str, site: str, url_data: Dict[str, Any]) -> List[Property]:
        """Parse properties from HTML content based on site."""
        try:
            # Import parser based on site
            if site == 'realestate.com.au':
                from backend.services.site_parsers import RealEstateParser
                parser = RealEstateParser()
            elif site == 'domain.com.au':
                from backend.services.site_parsers import DomainParser
                parser = DomainParser()
            elif site == 'rent.com.au':
                from backend.services.site_parsers import RentParser
                parser = RentParser()
            else:
                print(f"No parser available for site: {site}")
                return []
            
            # Parse properties
            properties = await parser.parse_properties(content, url_data)
            return properties
            
        except ImportError:
            print(f"Parser not yet implemented for {site}")
            return []
        except Exception as e:
            print(f"Error parsing properties from {site}: {e}")
            return []
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'cache_size': len(self.cache.cache),
            'cache_ttl_minutes': self.cache.cache_ttl.total_seconds() / 60,
            'last_cleared': datetime.now().isoformat()
        }
    
    def clear_cache(self):
        """Clear all cached results."""
        self.cache.cache.clear()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all configured sites."""
        health_status = {}
        
        for site, config in self.site_configs.items():
            try:
                start_time = time.time()
                
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers=config.headers
                ) as session:
                    
                    test_url = f"https://{config.base_domain}"
                    async with session.get(test_url) as response:
                        response_time = int((time.time() - start_time) * 1000)
                        
                        health_status[site] = {
                            'status': 'healthy' if response.status == 200 else 'unhealthy',
                            'status_code': response.status,
                            'response_time_ms': response_time,
                            'last_checked': datetime.now().isoformat()
                        }
                        
            except Exception as e:
                health_status[site] = {
                    'status': 'error',
                    'error': str(e),
                    'last_checked': datetime.now().isoformat()
                }
        
        return health_status

# Utility functions for testing and demonstration
async def test_concurrent_fetcher():
    """Test the concurrent property fetcher."""
    
    # Create sample URL data
    sample_urls = [
        {
            'url': 'https://www.realestate.com.au/rent/in-bondi,+nsw+2026/list-1?bedrooms=2',
            'site': 'realestate.com.au',
            'filters': {'bedrooms': 2},
            'suburb': 'Bondi',
            'postcode': '2026'
        },
        {
            'url': 'https://www.domain.com.au/rent/bondi-nsw-2026?bedrooms=2',
            'site': 'domain.com.au',
            'filters': {'bedrooms': 2},
            'suburb': 'Bondi',
            'postcode': '2026'
        }
    ]
    
    # Initialize fetcher
    fetcher = ConcurrentPropertyFetcher(cache_ttl_minutes=15)
    
    print("Testing Concurrent Property Fetcher")
    print("=" * 50)
    
    # Health check
    print("Performing health check...")
    health_status = await fetcher.health_check()
    for site, status in health_status.items():
        print(f"  {site}: {status['status']} ({status.get('response_time_ms', 'N/A')}ms)")
    
    print()
    
    # Fetch properties
    print("Fetching properties...")
    start_time = time.time()
    
    results = await fetcher.fetch_properties_concurrent(sample_urls)
    
    total_time = time.time() - start_time
    
    print(f"Completed in {total_time:.2f} seconds")
    print(f"Total results: {len(results)}")
    
    # Display results
    for result in results:
        print(f"\n{result.site}:")
        print(f"  URL: {result.url[:60]}...")
        print(f"  Success: {result.success}")
        print(f"  Status: {result.status_code}")
        print(f"  Response Time: {result.response_time_ms}ms")
        if result.error:
            print(f"  Error: {result.error}")
        print(f"  Properties Found: {len(result.properties)}")
    
    # Cache stats
    print(f"\nCache Stats: {fetcher.get_cache_stats()}")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_concurrent_fetcher())