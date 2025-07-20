import requests
from bs4 import BeautifulSoup
import re
import logging
from urllib.parse import urljoin, urlparse
import time
from config import get_request_headers, get_random_proxy, apply_rate_limit, REQUEST_CONFIG, SEARCH_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealEstateSpider:
    def __init__(self):
        self.base_url = SEARCH_CONFIG['realestate']['base_url']
        self.search_url = SEARCH_CONFIG['realestate']['search_url']
        self.max_pages = SEARCH_CONFIG['realestate']['max_pages']
        self.session = requests.Session()
        
    def make_request(self, url, retries=0):
        """发送HTTP请求"""
        try:
            headers = get_request_headers()
            proxy = get_random_proxy()
            
            response = self.session.get(
                url, 
                headers=headers, 
                proxies=proxy, 
                timeout=REQUEST_CONFIG['timeout']
            )
            
            if response.status_code == 200:
                return response
            elif response.status_code == 429:  # 被限制
                logger.warning(f"Rate limited, waiting...")
                time.sleep(REQUEST_CONFIG['retry_delay'] * 2)
                
        except Exception as e:
            logger.error(f"Request failed: {e}")
            
        # 重试逻辑
        if retries < REQUEST_CONFIG['max_retries']:
            logger.info(f"Retrying request ({retries + 1}/{REQUEST_CONFIG['max_retries']})")
            time.sleep(REQUEST_CONFIG['retry_delay'])
            return self.make_request(url, retries + 1)
            
        return None
    
    def parse_price(self, price_text):
        """解析价格文本"""
        if not price_text:
            return None, None
            
        price_text = price_text.strip()
        
        # 处理各种价格格式
        if 'Contact Agent' in price_text or 'POA' in price_text:
            return price_text, None
            
        # 提取数字价格
        price_match = re.search(r'\$?([0-9,]+)', price_text)
        if price_match:
            try:
                price_numeric = float(price_match.group(1).replace(',', ''))
                return price_text, price_numeric
            except:
                pass
                
        return price_text, None
    
    def parse_property_details(self, property_element):
        """解析单个房产详情"""
        try:
            # 获取链接
            link_elem = property_element.find('a', href=True)
            link = urljoin(self.base_url, link_elem['href']) if link_elem else None
            
            # 获取价格
            price_elem = property_element.find(class_=re.compile(r'price|Price'))
            price_text = price_elem.get_text(strip=True) if price_elem else None
            price_original, price_numeric = self.parse_price(price_text)
            
            # 获取地址
            address_elem = property_element.find(class_=re.compile(r'address|Address'))
            address = address_elem.get_text(strip=True) if address_elem else None
            
            # 获取房产类型
            property_type_elem = property_element.find(class_=re.compile(r'type|Type'))
            property_type = property_type_elem.get_text(strip=True) if property_type_elem else None
            
            # 获取卧室数
            bedrooms_elem = property_element.find(class_=re.compile(r'bed|Bed'))
            bedrooms = None
            if bedrooms_elem:
                bed_match = re.search(r'(\d+)', bedrooms_elem.get_text())
                bedrooms = int(bed_match.group(1)) if bed_match else None
            
            # 获取浴室数
            bathrooms_elem = property_element.find(class_=re.compile(r'bath|Bath'))
            bathrooms = None
            if bathrooms_elem:
                bath_match = re.search(r'(\d+)', bathrooms_elem.get_text())
                bathrooms = int(bath_match.group(1)) if bath_match else None
            
            # 获取停车位数
            parking_elem = property_element.find(class_=re.compile(r'car|Car|parking|Parking'))
            parking = None
            if parking_elem:
                parking_match = re.search(r'(\d+)', parking_elem.get_text())
                parking = int(parking_match.group(1)) if parking_match else None
            
            # 获取suburb
            suburb = None
            if address:
                address_parts = address.split(',')
                if len(address_parts) >= 2:
                    suburb = address_parts[-2].strip()
            
            return {
                'price': price_original,
                'price_numeric': price_numeric,
                'address': address,
                'suburb': suburb,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'parking': parking,
                'property_type': property_type,
                'link': link,
                'source': 'realestate.com.au'
            }
            
        except Exception as e:
            logger.error(f"Error parsing property details: {e}")
            return None
    
    def scrape_search_page(self, url):
        """爬取搜索页面"""
        response = self.make_request(url)
        if not response:
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        properties = []
        
        # 查找房产列表容器（需要根据实际网站结构调整）
        property_elements = soup.find_all('div', class_=re.compile(r'listing|property|card'))
        
        for prop_elem in property_elements:
            property_data = self.parse_property_details(prop_elem)
            if property_data:
                properties.append(property_data)
        
        logger.info(f"Found {len(properties)} properties on page")
        return properties
    
    def scrape_all_pages(self):
        """爬取所有页面"""
        all_properties = []
        
        for page in range(1, self.max_pages + 1):
            logger.info(f"Scraping page {page}/{self.max_pages}")
            
            # 构建分页URL
            page_url = f"{self.search_url}?page={page}"
            
            properties = self.scrape_search_page(page_url)
            if not properties:
                logger.warning(f"No properties found on page {page}, stopping")
                break
                
            all_properties.extend(properties)
            
            # 应用速率限制
            apply_rate_limit()
            
        logger.info(f"Total properties scraped: {len(all_properties)}")
        return all_properties
    
    def run(self):
        """运行爬虫"""
        logger.info("Starting realestate.com.au scraper...")
        return self.scrape_all_pages()

if __name__ == "__main__":
    spider = RealEstateSpider()
    properties = spider.run()
    
    # 打印前几条数据作为示例
    for i, prop in enumerate(properties[:5]):
        print(f"Property {i+1}:")
        for key, value in prop.items():
            print(f"  {key}: {value}")
        print()