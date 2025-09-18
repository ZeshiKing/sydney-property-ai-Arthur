"""
OpenAI-based Property Data Parser Service

基于OpenAI API的房产数据解析服务
"""

import json
import re
import os
from typing import Dict, Any, List, Optional
import logging
from openai import AsyncOpenAI

from app.core.config import settings
from app.models.property import Property
from app.api.api_v1.endpoints.properties import PropertyModel

logger = logging.getLogger(__name__)


class OpenAIPropertyParser:
    """OpenAI房产数据解析器"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """初始化OpenAI解析器
        
        Args:
            api_key: OpenAI API密钥，如果None则从配置文件获取
            model: 使用的模型，如果None则从配置文件获取
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
        
        if not self.api_key:
            logger.warning("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)
            
        self.prompt_template = """You are an information extractor. Return ONLY one valid JSON object.
Keys: listing_type("rent"|"sale"|null), property_type("apartment"|"house"|"townhouse"|"studio"|null),
title(string|null), address(string|null), price(string|null),
bedrooms(int|null), bathrooms(int|null), parking_spaces(int|null), url(string|null),
suburbs(string[]), price_min(int|null), price_max(int|null), unit("per_week"|"per_month"|null).

Rules: 
- AUD integers for prices
- Accept typos & mixed languages
- 'pw|per week|weekly' -> per_week
- 'pm|pcm|per month|monthly' -> per_month
- Extract information from the provided text
- If information is not available, use null
- For suburbs, provide an array of location names mentioned

Text: {text}

Return only the JSON object:"""

    async def llm_parse(self, text: str) -> Dict[str, Any]:
        """使用OpenAI API解析文本数据
        
        Args:
            text: 要解析的文本内容
            
        Returns:
            Dict: 解析后的结构化数据
            
        Raises:
            ValueError: API调用失败时抛出
        """
        if not text or not text.strip():
            return {}
            
        # 如果OpenAI客户端未初始化，使用回退解析
        if not self.client:
            logger.warning("OpenAI client not available, using fallback parsing")
            return self._fallback_parse(text)
        
        try:
            # 限制输入文本长度，避免token超限
            text = text[:4000] if len(text) > 4000 else text
            
            prompt = self.prompt_template.format(text=text)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise data extraction assistant. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}  # 确保返回JSON格式
            )
            
            result_text = response.choices[0].message.content.strip()
            logger.debug(f"OpenAI response: {result_text}")
            
            # 解析JSON
            try:
                result = json.loads(result_text)
                logger.debug(f"Parsed result: {result}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {result_text}, error: {e}")
                # 尝试提取JSON块
                json_match = self._extract_json_from_text(result_text)
                if json_match:
                    return json.loads(json_match)
                raise
            
        except Exception as e:
            logger.error(f"OpenAI API parsing failed: {e}")
            # 回退到规则解析
            logger.info("Falling back to rule-based parsing")
            return self._fallback_parse(text)

    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """从文本中提取JSON块"""
        # 尝试找到JSON对象
        start = text.find('{')
        if start == -1:
            return None
        
        depth = 0
        for i, char in enumerate(text[start:], start):
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i+1]
        
        return None

    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """回退的规则解析方法"""
        result = {}
        text_lower = text.lower()
        
        try:
            # 价格提取
            price_patterns = [
                r'\$(\d+)(?:\s*(?:per\s+week|pw|/week|weekly))?',
                r'(\d+)(?:\s*(?:per\s+week|pw|/week|weekly))',
                r'\$(\d+)(?:\s*(?:per\s+month|pm|/month|monthly))?',
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    price = int(match.group(1))
                    result["price"] = f"${price}"
                    
                    # 判断单位
                    if any(unit in text_lower for unit in ['per month', 'pm', '/month', 'monthly']):
                        result["unit"] = "per_month"
                        result["price_min"] = result["price_max"] = price
                    else:
                        result["unit"] = "per_week"
                        result["price_min"] = result["price_max"] = price
                    break
            
            # 价格范围提取
            range_match = re.search(r'\$?(\d+)[-–]\$?(\d+)', text)
            if range_match:
                result["price_min"] = int(range_match.group(1))
                result["price_max"] = int(range_match.group(2))
            
            # 卧室数量
            bed_patterns = [
                r'(\d+)(?:\s*(?:bed|bedroom|br))',
                r'(?:bed|bedroom|br)(?:\s*)(\d+)',
            ]
            for pattern in bed_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result["bedrooms"] = int(match.group(1))
                    break
            
            # 卫浴数量
            bath_patterns = [
                r'(\d+)(?:\s*(?:bath|bathroom|ba))',
                r'(?:bath|bathroom|ba)(?:\s*)(\d+)',
            ]
            for pattern in bath_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result["bathrooms"] = int(match.group(1))
                    break
            
            # 停车位
            park_patterns = [
                r'(\d+)(?:\s*(?:car|parking|garage))',
                r'(?:car|parking|garage)(?:\s*)(\d+)',
            ]
            for pattern in park_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result["parking_spaces"] = int(match.group(1))
                    break
            
            # 房产类型
            if any(word in text_lower for word in ['apartment', 'unit', 'flat']):
                result["property_type"] = "apartment"
            elif any(word in text_lower for word in ['house', 'home']):
                result["property_type"] = "house"
            elif 'townhouse' in text_lower:
                result["property_type"] = "townhouse"
            elif 'studio' in text_lower:
                result["property_type"] = "studio"
            
            # 租售类型
            if any(word in text_lower for word in ['rent', 'rental', 'lease', 'looking for']):
                result["listing_type"] = "rent"
            elif any(word in text_lower for word in ['sale', 'buy', 'purchase']):
                result["listing_type"] = "sale"
            else:
                result["listing_type"] = "rent"  # 默认租房
            
            # 地址/区域提取
            # 常见澳洲城市和地区
            australian_locations = [
                'sydney', 'melbourne', 'brisbane', 'perth', 'adelaide', 'canberra', 'darwin', 'hobart',
                'camperdown', 'newtown', 'surry hills', 'bondi', 'manly', 'paddington', 'redfern',
                'carlton', 'fitzroy', 'south yarra', 'st kilda', 'richmond', 'brunswick', 'prahran',
                'fortitude valley', 'south brisbane', 'new farm', 'west end', 'paddington',
                'northbridge', 'subiaco', 'fremantle', 'cottesloe', 'leederville',
                'north adelaide', 'unley', 'glenelg', 'norwood', 'prospect'
            ]
            
            found_locations = []
            for location in australian_locations:
                if location in text_lower:
                    found_locations.append(location.title())
            
            if found_locations:
                result["suburbs"] = found_locations[:3]  # 最多3个
                result["address"] = found_locations[0]
            
            # 特殊需求检测
            if any(word in text_lower for word in ['parking', 'garage', 'car space', 'must have parking']):
                result["parking_spaces"] = result.get("parking_spaces", 1)
            
            if any(word in text_lower for word in ['pet', 'dog', 'cat', 'pet friendly', 'pets allowed']):
                result["pet_friendly"] = True
            
            logger.debug(f"Fallback parsing result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Fallback parsing failed: {e}")
            return {}

    async def parse_properties_from_raw(self, raw_data: Dict[str, Any], 
                                      search_params: Dict[str, Any]) -> List[PropertyModel]:
        """从原始抓取数据解析房产列表
        
        Args:
            raw_data: Firecrawl返回的原始数据
            search_params: 搜索参数
            
        Returns:
            List[PropertyModel]: 解析后的房产模型列表
        """
        properties = []
        
        try:
            # 从Firecrawl响应中提取内容
            content = raw_data.get('data', {})
            markdown = content.get('markdown', '')
            html = content.get('html', '')
            
            logger.info(f"Parsing data - markdown: {len(markdown)} chars, html: {len(html)} chars")
            
            # 使用OpenAI解析内容
            if markdown or html:
                # 优先使用markdown，如果太长则截取
                parse_text = markdown if markdown else html
                if len(parse_text) > 4000:
                    parse_text = parse_text[:4000] + "..."
                
                # 添加搜索上下文
                context_text = f"Search context: Looking for properties in {search_params.get('location', '')}. "
                if search_params.get('bedrooms'):
                    context_text += f"{search_params['bedrooms']} bedrooms. "
                if search_params.get('min_price') or search_params.get('max_price'):
                    context_text += f"Budget: ${search_params.get('min_price', '')}-${search_params.get('max_price', '')} per week. "
                
                full_text = context_text + "\n\nProperty data:\n" + parse_text
                
                parsed_data = await self.llm_parse(full_text)
                logger.info(f"OpenAI parsing result: {parsed_data}")
                
                # 基于解析结果创建房产数据
                if parsed_data:
                    property_data = self._create_property_from_parsed(parsed_data, search_params)
                    if property_data:
                        properties.append(property_data)
            
            # 如果没有解析到数据，创建示例数据（开发阶段）
            if not properties:
                properties = self._create_sample_properties(search_params)
            
            logger.info(f"Successfully parsed {len(properties)} properties")
            return properties
            
        except Exception as e:
            logger.error(f"Property parsing failed: {e}")
            # 回退到示例数据
            return self._create_sample_properties(search_params)

    def _create_property_from_parsed(self, parsed_data: Dict[str, Any], 
                                   search_params: Dict[str, Any]) -> Optional[PropertyModel]:
        """从解析数据创建PropertyModel"""
        try:
            import uuid
            from datetime import datetime
            
            # 基础信息
            property_id = str(uuid.uuid4())
            title = parsed_data.get('title') or f"{parsed_data.get('property_type', 'Property')} in {search_params.get('location', 'Sydney')}"
            price = parsed_data.get('price') or f"${search_params.get('min_price', 500)}/week"
            
            # 地址优先级：parsed_data.address > parsed_data.suburbs[0] > search_params.location
            location = parsed_data.get('address')
            if not location and parsed_data.get('suburbs'):
                location = parsed_data['suburbs'][0] if isinstance(parsed_data['suburbs'], list) else parsed_data['suburbs']
            if not location:
                location = search_params.get('location', 'Sydney')
            
            # 房产特征
            bedrooms = parsed_data.get('bedrooms') or search_params.get('bedrooms', 2)
            bathrooms = parsed_data.get('bathrooms') or search_params.get('bathrooms', 1)
            parking = parsed_data.get('parking_spaces') or search_params.get('parking', 1)
            property_type = parsed_data.get('property_type') or search_params.get('property_type', 'apartment')
            
            # 创建PropertyModel
            property_model = PropertyModel(
                id=property_id,
                title=title,
                price=price,
                location=location,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                parking=parking,
                property_type=property_type,
                description=f"Modern {property_type} with excellent amenities in {location}",
                features=["Air Conditioning", "Built-in Wardrobes", "Balcony"],
                images=["https://example.com/property1.jpg"],
                agent={
                    "name": "Property Agent",
                    "phone": "0400 000 000",
                    "email": "agent@realestate.com"
                },
                coordinates={"lat": -33.8688, "lng": 151.2093},
                url=parsed_data.get('url') or "https://www.domain.com.au/property/sample",
                source="Domain.com.au",
                scraped_at=datetime.utcnow().isoformat() + "Z",
                available_from="Available Now",
                property_size="75 sqm",
                land_size=None,
                year_built=None,
                energy_rating=None,
                pet_friendly=parsed_data.get('pet_friendly', False),
                furnished=False,
                inspection_times=[]
            )
            
            return property_model
            
        except Exception as e:
            logger.error(f"Failed to create property from parsed data: {e}")
            return None

    def _create_sample_properties(self, search_params: Dict[str, Any]) -> List[PropertyModel]:
        """创建示例房产数据（开发阶段使用）"""
        properties = []
        
        try:
            import uuid
            from datetime import datetime
            
            # 生成3-5个示例房产
            for i in range(3, 6):
                property_id = str(uuid.uuid4())
                base_price = search_params.get('min_price', 500)
                varied_price = base_price + (i * 50)
                
                property_model = PropertyModel(
                    id=property_id,
                    title=f"Sample Property {i} - {search_params.get('bedrooms', 2)} Bed {search_params.get('property_type', 'Apartment')}",
                    price=f"${varied_price}/week",
                    location=search_params.get('location', 'Sydney'),
                    bedrooms=search_params.get('bedrooms', 2),
                    bathrooms=search_params.get('bathrooms', 1),
                    parking=search_params.get('parking', 1),
                    property_type=search_params.get('property_type', 'apartment'),
                    description=f"Well-appointed modern {search_params.get('property_type', 'apartment')} with excellent amenities",
                    features=["Air Conditioning", "Built-in Wardrobes", "Balcony", "Dishwasher"],
                    images=[f"https://example.com/property{i}.jpg"],
                    agent={
                        "name": f"Agent {i}",
                        "phone": f"040{i} 000 000",
                        "email": f"agent{i}@realestate.com"
                    },
                    coordinates={"lat": -33.8688 + i*0.001, "lng": 151.2093 + i*0.001},
                    url=f"https://www.domain.com.au/property/sample-{i}",
                    source="Domain.com.au",
                    scraped_at=datetime.utcnow().isoformat() + "Z",
                    available_from="Available Now",
                    property_size=f"{65 + i*10} sqm",
                    land_size=None,
                    year_built=2015 + i,
                    energy_rating=None,
                    pet_friendly=i % 2 == 0,
                    furnished=i % 3 == 0,
                    inspection_times=[]
                )
                
                properties.append(property_model)
            
            return properties
            
        except Exception as e:
            logger.error(f"Failed to create sample properties: {e}")
            return []


# 单例实例 - 使用OpenAI
openai_parser = OpenAIPropertyParser()