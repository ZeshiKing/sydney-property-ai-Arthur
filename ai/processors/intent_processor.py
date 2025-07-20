"""
用户意图处理器
专门处理自然语言用户输入的意图识别
"""

import re
import json
from typing import Dict, Any, Optional

import anthropic

from backend.models.property import UserIntent
from backend.utils.logger import api_logger
from config.settings import settings

class IntentProcessor:
    """用户意图处理器类"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.logger = api_logger
        
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None
            self.logger.warning("No Anthropic API key provided, using fallback processing")
    
    def extract_intent(self, user_input: str) -> UserIntent:
        """
        提取用户意图
        
        Args:
            user_input: 用户输入文本
            
        Returns:
            UserIntent对象
        """
        try:
            if self.client:
                return self._extract_with_ai(user_input)
            else:
                return self._extract_with_fallback(user_input)
        except Exception as e:
            self.logger.error(f"Intent extraction failed: {e}")
            return self._extract_with_fallback(user_input)
    
    def _extract_with_ai(self, user_input: str) -> UserIntent:
        """使用AI模型提取意图"""
        prompt = self._build_ai_prompt(user_input)
        
        try:
            response = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = json.loads(response.content[0].text.strip())
            self.logger.info(f"AI intent extraction successful for input: {user_input[:50]}...")
            
            return UserIntent(
                suburb=result.get("suburb"),
                bedrooms=result.get("bedrooms"),
                budget=result.get("budget"),
                property_type=result.get("property_type"),
                size_preference=result.get("size_preference"),
                location_preference=result.get("location_preference"),
                distance_from_city=result.get("distance_from_city"),
                special_requirements=result.get("special_requirements", []),
                inferred_needs=result.get("inferred_needs", []),
                priority_analysis=result.get("priority_analysis", "")
            )
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse AI response: {e}")
            return self._extract_with_fallback(user_input)
        except Exception as e:
            self.logger.error(f"AI intent extraction failed: {e}")
            return self._extract_with_fallback(user_input)
    
    def _extract_with_fallback(self, user_input: str) -> UserIntent:
        """使用规则引擎提取意图"""
        self.logger.info(f"Using fallback intent extraction for: {user_input[:50]}...")
        
        intent_data = {
            "suburb": self._extract_suburb(user_input),
            "bedrooms": self._extract_bedrooms(user_input),
            "budget": self._extract_budget(user_input),
            "special_requirements": self._extract_special_requirements(user_input)
        }
        
        return UserIntent(**intent_data)
    
    def _build_ai_prompt(self, user_input: str) -> str:
        """构建AI分析提示词"""
        return f"""
你是一个专业的房产需求分析师，请深度分析以下用户的房屋需求描述，提取并推理关键信息。

用户输入："{user_input}"

请分析以下维度：

1. **基础需求**：
   - 卧室：2室、2b、两个卧室、2bedroom、1b1b、2室1厅、双卧等
   - 区域：在Bondi、Bondi地区、邦迪、靠近Bondi、Bondi附近等
   - 预算：100万、100w、一百万、100万澳币、不超过100万、预算100万以内等

2. **口语化表达识别**：
   - 大小：大一点的、宽敞的、小巧的、紧凑的 → 推测面积需求
   - 位置：离市区远的、偏远的、郊外的、市中心的、繁华的
   - 环境：安静的、热闹的、便民的、偏僻的

3. **地理位置关系**：
   - 距离概念：离市区远、靠近海边、远离喧嚣、市中心附近
   - 交通便利：地铁沿线、公交方便、交通便利
   - 周边设施：学校附近、商圈周边、医院附近

4. **隐含需求推测**：
   - "大一点的" → 可能需要更多卧室或更大面积
   - "离市区远" → 可能预算有限，愿意牺牲便利换取性价比
   - "安静" → 可能需要住宅区而非商业区
   - "便民" → 可能需要生活设施齐全的区域

请以JSON格式返回分析结果：
{{
    "suburb": "具体区域名称或null",
    "bedrooms": 卧室数量(数字)或null,
    "budget": 预算万澳币(数字)或null,
    "size_preference": "大、中、小 或 null",
    "location_preference": "市中心、郊外、海边、安静区域 等或null",
    "distance_from_city": "近、中、远 或 null",
    "special_requirements": ["明确的特殊要求"],
    "inferred_needs": ["推测的隐含需求"],
    "priority_analysis": "用户最重视的因素分析"
}}

只返回JSON，不要其他文字。
"""
    
    def _extract_suburb(self, text: str) -> Optional[str]:
        """提取区域信息"""
        patterns = [
            r'在(.+?)区', r'在(.+?)地区', r'在(.+?)买', r'在(.+?)找', r'在(.+?)租',
            r'(.+?)区域', r'(.+?)附近', r'想住(.+?)', r'考虑(.+?)', r'靠近(.+?)',
            r'(.+?)地区', r'(.+?)那边', r'(.+?)周边'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                suburb = match.group(1).strip()
                # 清理常见后缀
                suburb = re.sub(r'(的房子|房源|地方|那里|那边)$', '', suburb)
                return suburb
        return None
    
    def _extract_bedrooms(self, text: str) -> Optional[int]:
        """提取卧室数量"""
        patterns = [
            r'(\d+)室', r'(\d+)房', r'(\d+)个卧室', r'(\d+)间卧室',
            r'(\d+)b\b', r'(\d+)bedroom', r'(\d+)bed',
            r'(\d+)室(\d+)厅', r'(\d+)b(\d+)b'
        ]
        
        # 中文数字映射
        chinese_numbers = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '单': 1, '双': 2}
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bedroom_str = match.group(1)
                if bedroom_str in chinese_numbers:
                    return chinese_numbers[bedroom_str]
                elif bedroom_str.isdigit():
                    return int(bedroom_str)
        return None
    
    def _extract_budget(self, text: str) -> Optional[float]:
        """提取预算信息"""
        patterns = [
            r'预算(\d+)万', r'(\d+)万以内', r'(\d+)万澳币', r'(\d+)w\b',
            r'最多(\d+)万', r'不超过(\d+)万', r'(\d+)万左右', r'(\d+)万预算',
            r'(\d+)万到(\d+)万', r'(\d+)-(\d+)万', r'(\d+)万以下'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) >= 2 and match.group(2):
                    # 范围预算，取上限
                    return float(match.group(2))
                else:
                    budget_str = match.group(1)
                    if budget_str.isdigit():
                        return float(budget_str)
        return None
    
    def _extract_special_requirements(self, text: str) -> list:
        """提取特殊要求"""
        requirements = []
        keywords = {
            "安静": "环境安静", "静": "环境安静",
            "交通": "交通便利", "地铁": "交通便利", "公交": "交通便利",
            "学校": "靠近学校", "学区": "靠近学校",
            "海边": "海景房", "海景": "海景房", "海滩": "海景房",
            "新房": "新建房屋", "新": "新建房屋",
            "停车": "停车位", "车位": "停车位",
            "花园": "带花园", "院子": "带花园",
            "阳台": "带阳台", "balcony": "带阳台"
        }
        
        for keyword, description in keywords.items():
            if keyword in text.lower():
                if description not in requirements:
                    requirements.append(description)
        
        return requirements

# 全局意图处理器实例
intent_processor = IntentProcessor()