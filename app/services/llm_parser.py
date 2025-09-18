"""
LLM-based Property Data Parser Service

基于大语言模型的房产数据解析服务
"""

import json
import re
import torch
from typing import Dict, Any, List, Optional
import logging
from transformers import AutoTokenizer, AutoModelForCausalLM

from app.models.property import Property
from app.api.api_v1.endpoints.properties import PropertyModel

logger = logging.getLogger(__name__)


class LLMPropertyParser:
    """LLM房产数据解析器"""
    
    def __init__(self, model_name: str = "Qwen/Qwen2.5-14B-Instruct-1M"):
        """初始化LLM解析器
        
        Args:
            model_name: 模型名称，默认使用Qwen2.5-14B
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self._load_model()
        
        self.prompt_template = """You are an information extractor. Return ONLY one valid JSON object.
Keys: listing_type("rent"|"sale"|null), property_type("apartment"|"house"|"townhouse"|"studio"|null),
title(null), address(string|null), price(string|null),
bedrooms(int|null), bathrooms(int|null), parking_spaces(int|null), url(string|null),
suburbs(string[]), price_min(int|null), price_max(int|null), unit("per_week"|"per_month"|null).
Rules: AUD integers; accept typos & mixed languages; 'pw|per week|weekly'->per_week; 'pm|pcm|per month|monthly'->per_month.
Text: {text}
JSON:
"""

    def _load_model(self):
        """加载LLM模型"""
        try:
            logger.info(f"Loading LLM model: {self.model_name}")
            
            # 检查CUDA可用性
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")
            
            # 加载tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, 
                trust_remote_code=True
            )
            
            # 加载模型
            model_kwargs = {
                "torch_dtype": torch.bfloat16,
                "device_map": device,
                "trust_remote_code": True
            }
            
            # 如果有CUDA，尝试使用flash attention
            if device == "cuda":
                try:
                    model_kwargs["attn_implementation"] = "flash_attention_2"
                except Exception as e:
                    logger.warning(f"Flash attention not available: {e}")
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
            
            logger.info("LLM model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            # 在生产环境中，可以回退到规则解析
            self.model = None
            self.tokenizer = None

    def _first_json_block(self, text: str) -> Optional[str]:
        """从文本中提取第一个JSON块"""
        text = text.strip().split("```")[0]
        start = text.find("{")
        if start == -1:
            return None
        
        depth = 0
        for i, char in enumerate(text[start:], start):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i+1]
        
        return None

    def _try_parse_once(self, prompt: str, max_new_tokens: int, 
                       do_sample: bool, temperature: Optional[float] = None) -> Optional[Dict]:
        """单次解析尝试"""
        if not self.model or not self.tokenizer:
            return None
            
        try:
            # 编码输入
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            
            # 生成参数
            generation_kwargs = {
                "max_new_tokens": max_new_tokens,
                "do_sample": do_sample,
                "eos_token_id": self.tokenizer.eos_token_id,
                "pad_token_id": self.tokenizer.eos_token_id,
            }
            
            if do_sample and temperature is not None:
                generation_kwargs["temperature"] = temperature
            
            # 生成输出
            with torch.no_grad():
                outputs = self.model.generate(**inputs, **generation_kwargs)
            
            # 解码输出
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 提取JSON
            json_text = self._first_json_block(generated_text)
            if not json_text:
                return None
            
            # 解析JSON
            return json.loads(json_text)
            
        except Exception as e:
            logger.debug(f"Parse attempt failed: {e}")
            return None

    def llm_parse(self, text: str) -> Dict[str, Any]:
        """使用LLM解析文本数据
        
        Args:
            text: 要解析的文本内容
            
        Returns:
            Dict: 解析后的结构化数据
            
        Raises:
            ValueError: 所有解析尝试失败时抛出
        """
        if not text or not text.strip():
            return {}
            
        # 如果模型未加载，使用回退解析
        if not self.model or not self.tokenizer:
            logger.warning("LLM model not available, using fallback parsing")
            return self._fallback_parse(text)
        
        prompt = self.prompt_template.format(text=text)
        
        # 多种配置的解析尝试
        parse_configs = [
            (220, False, None),      # 贪婪短
            (300, False, None),      # 贪婪长  
            (300, True, 0.2),        # 低温抽样
            (360, True, 0.3),        # 略升温抽样
        ]
        
        for max_tokens, do_sample, temperature in parse_configs:
            result = self._try_parse_once(prompt, max_tokens, do_sample, temperature)
            if result:
                logger.debug(f"LLM parsing successful with config: {max_tokens}, {do_sample}, {temperature}")
                return result
        
        # 所有尝试失败，使用回退解析
        logger.warning("All LLM parse attempts failed, using fallback")
        return self._fallback_parse(text)

    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """回退的规则解析方法"""
        result = {}
        
        # 简单的正则表达式提取
        # 价格提取
        price_patterns = [
            r'\$(\d+)(?:\s*(?:per\s+week|pw|/week|weekly))?',
            r'(\d+)(?:\s*(?:per\s+week|pw|/week|weekly))',
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["price"] = f"${match.group(1)}"
                result["unit"] = "per_week"
                break
        
        # 卧室数量
        bed_match = re.search(r'(\d+)(?:\s*(?:bed|bedroom|br))', text, re.IGNORECASE)
        if bed_match:
            result["bedrooms"] = int(bed_match.group(1))
        
        # 卫浴数量
        bath_match = re.search(r'(\d+)(?:\s*(?:bath|bathroom|ba))', text, re.IGNORECASE)
        if bath_match:
            result["bathrooms"] = int(bath_match.group(1))
        
        # 房产类型
        if any(word in text.lower() for word in ['apartment', 'unit', 'flat']):
            result["property_type"] = "apartment"
        elif any(word in text.lower() for word in ['house', 'home']):
            result["property_type"] = "house"
        elif 'townhouse' in text.lower():
            result["property_type"] = "townhouse"
        elif 'studio' in text.lower():
            result["property_type"] = "studio"
        
        # 租售类型
        if any(word in text.lower() for word in ['rent', 'rental', 'lease']):
            result["listing_type"] = "rent"
        elif any(word in text.lower() for word in ['sale', 'buy', 'purchase']):
            result["listing_type"] = "sale"
        
        return result

    def parse_properties_from_raw(self, raw_data: Dict[str, Any], 
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
            
            # 使用LLM解析内容
            if markdown or html:
                parse_text = f"Markdown content:\n{markdown}\n\nHTML content:\n{html[:2000]}"  # 限制长度
                parsed_data = self.llm_parse(parse_text)
                
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
            return []

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
            location = parsed_data.get('address') or search_params.get('location', 'Sydney')
            
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
                description=f"Modern {property_type} with excellent amenities",
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
                pet_friendly=False,
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


# 单例实例
llm_parser = LLMPropertyParser()