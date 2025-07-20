import requests
from bs4 import BeautifulSoup
import re
import logging
from urllib.parse import urljoin, urlparse
import time
import json
from config import get_request_headers, get_random_proxy, apply_rate_limit, REQUEST_CONFIG, SEARCH_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DomainSpider:
    def __init__(self):
        self.base_url = SEARCH_CONFIG['domain']['base_url']
        self.search_url = SEARCH_CONFIG['domain']['search_url']
        self.max_pages = SEARCH_CONFIG['domain']['max_pages']
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
        if 'Contact Agent' in price_text or 'POA' in price_text or 'Auction' in price_text:
            return price_text, None
        
        # 处理价格范围 (e.g., "$500,000 - $600,000")
        price_range_match = re.search(r'\$([0-9,]+)\s*-\s*\$([0-9,]+)', price_text)
        if price_range_match:
            try:
                min_price = float(price_range_match.group(1).replace(',', ''))
                max_price = float(price_range_match.group(2).replace(',', ''))
                avg_price = (min_price + max_price) / 2
                return price_text, avg_price
            except:
                pass
        
        # 提取单一价格
        price_match = re.search(r'\$([0-9,]+)', price_text)
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
            
            # Domain网站通常在data属性中存储信息
            property_data_elem = property_element.find(attrs={'data-testid': re.compile(r'listing|property')})
            
            # 获取价格
            price_elem = property_element.find(attrs={'data-testid': 'listing-card-price'}) or \
                        property_element.find(class_=re.compile(r'price|Price'))
            price_text = price_elem.get_text(strip=True) if price_elem else None
            price_original, price_numeric = self.parse_price(price_text)
            
            # 获取地址
            address_elem = property_element.find(attrs={'data-testid': 'listing-card-address'}) or \
                          property_element.find(class_=re.compile(r'address|Address'))
            address = address_elem.get_text(strip=True) if address_elem else None
            
            # 获取suburb
            suburb_elem = property_element.find(attrs={'data-testid': 'listing-card-suburb'}) or \
                         property_element.find(class_=re.compile(r'suburb|Suburb'))
            suburb = suburb_elem.get_text(strip=True) if suburb_elem else None
            
            # 如果没有找到suburb，尝试从address中提取
            if not suburb and address:
                address_parts = address.split(',')
                if len(address_parts) >= 2:
                    suburb = address_parts[-2].strip()
            
            # 获取房产类型
            property_type_elem = property_element.find(attrs={'data-testid': 'listing-card-property-type'}) or \
                                property_element.find(class_=re.compile(r'property-type|propertyType'))
            property_type = property_type_elem.get_text(strip=True) if property_type_elem else None
            
            # 获取房间信息
            features_elem = property_element.find(attrs={'data-testid': 'listing-card-features'}) or \
                           property_element.find(class_=re.compile(r'features|Features'))
            
            bedrooms = None
            bathrooms = None
            parking = None
            
            if features_elem:
                features_text = features_elem.get_text()
                
                # 提取卧室数
                bed_match = re.search(r'(\d+)\s*bed|(\d+)\s*Bed', features_text)
                if bed_match:
                    bedrooms = int(bed_match.group(1) or bed_match.group(2))
                
                # 提取浴室数
                bath_match = re.search(r'(\d+)\s*bath|(\d+)\s*Bath', features_text)
                if bath_match:
                    bathrooms = int(bath_match.group(1) or bath_match.group(2))
                
                # 提取停车位数
                car_match = re.search(r'(\d+)\s*car|(\d+)\s*Car', features_text)
                if car_match:
                    parking = int(car_match.group(1) or car_match.group(2))
            
            # 如果features_elem没有找到，尝试单独查找
            if bedrooms is None:
                bed_elem = property_element.find(class_=re.compile(r'bed|Bed'))
                if bed_elem:
                    bed_match = re.search(r'(\d+)', bed_elem.get_text())
                    bedrooms = int(bed_match.group(1)) if bed_match else None
            
            if bathrooms is None:
                bath_elem = property_element.find(class_=re.compile(r'bath|Bath'))
                if bath_elem:
                    bath_match = re.search(r'(\d+)', bath_elem.get_text())
                    bathrooms = int(bath_match.group(1)) if bath_match else None
            
            if parking is None:
                parking_elem = property_element.find(class_=re.compile(r'car|Car|parking|Parking'))
                if parking_elem:
                    parking_match = re.search(r'(\d+)', parking_elem.get_text())
                    parking = int(parking_match.group(1)) if parking_match else None
            
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
                'source': 'domain.com.au'
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
        
        # 查找房产列表容器（根据Domain网站结构调整）
        property_elements = soup.find_all('div', attrs={'data-testid': 'listing-card'}) or \
                          soup.find_all('div', class_=re.compile(r'listing|property|card'))
        
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
            
            # 构建分页URL（Domain使用不同的分页参数）
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
        logger.info("Starting domain.com.au scraper...")
        return self.scrape_all_pages()

if __name__ == "__main__":
    spider = DomainSpider()
    properties = spider.run()
    
    # 打印前几条数据作为示例
    for i, prop in enumerate(properties[:5]):
        print(f"Property {i+1}:")
        for key, value in prop.items():
            print(f"  {key}: {value}")
        print()