"""
推荐服务模块
处理房产推荐的核心业务逻辑
"""

from typing import List, Optional, Dict, Any

import anthropic

from backend.models.property import Property, UserIntent, Recommendation
from backend.services.data_service import data_service
from backend.utils.logger import api_logger
from config.settings import settings

class RecommendationService:
    """推荐服务类"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.logger = api_logger
        
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None
            self.logger.warning("No Anthropic API key provided")
    
    def generate_recommendations(self, 
                               user_input: str,
                               intent: UserIntent,
                               geo_analysis: Optional[Dict] = None,
                               intent_analysis: Optional[Dict] = None) -> List[str]:
        """
        生成个性化房产推荐
        
        Args:
            user_input: 用户原始输入
            intent: 解析后的用户意图
            geo_analysis: 地理分析结果
            intent_analysis: 意图分析结果
            
        Returns:
            推荐文本列表
        """
        try:
            # 验证API密钥
            if not self.client:
                raise ValueError("请设置环境变量 ANTHROPIC_API_KEY")
            
            # 验证用户意图
            if not intent.has_criteria():
                raise ValueError("无法解析用户偏好，请提供更多详细信息")
            
            # 获取筛选后的房源
            filtered_properties = data_service.filter_properties_flexible(
                intent, geo_analysis
            )
            
            if not filtered_properties:
                raise RuntimeError("未找到匹配的房源")
            
            self.logger.info(f"Found {len(filtered_properties)} properties for recommendation")
            
            # 构建推荐提示词
            prompt = self._build_recommendation_prompt(
                user_input, intent, filtered_properties, geo_analysis, intent_analysis
            )
            
            # 调用Claude API生成推荐
            response = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=settings.MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # 解析推荐结果
            recommendations = self._parse_recommendations(response.content[0].text)
            
            self.logger.info(f"Generated {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Recommendation generation failed: {e}")
            raise
    
    def _build_recommendation_prompt(self, 
                                   user_input: str, 
                                   intent: UserIntent,
                                   properties: List[Property],
                                   geo_analysis: Optional[Dict] = None,
                                   intent_analysis: Optional[Dict] = None) -> str:
        """构建推荐提示词"""
        
        # 构建用户需求描述
        requirements = []
        if intent.suburb:
            requirements.append(f"区域：{intent.suburb}")
        if intent.bedrooms:
            requirements.append(f"卧室：{intent.bedrooms}室")
        if intent.budget:
            requirements.append(f"预算：{intent.budget}万澳币以内")
        
        requirements_text = "、".join(requirements) if requirements else "任意条件"
        
        # 准备房源数据
        properties_info = []
        for prop in properties:
            properties_info.append(f"""
地址: {prop.address}
价格: {prop.display_price}
卧室: {prop.bedrooms}室
浴室: {prop.bathrooms}浴
停车: {prop.parking}个车位
类型: {prop.property_type}
链接: {prop.link}
""")
        
        properties_text = "\n".join(properties_info)
        
        # 构建附加上下文
        additional_context = ""
        
        # 添加地理分析结果
        if geo_analysis:
            location_analysis = geo_analysis.get("location_analysis", {})
            if location_analysis.get("distance_preference"):
                additional_context += f"\n📍 地理位置偏好：{location_analysis['distance_preference']}离市中心"
            if location_analysis.get("area_characteristics"):
                additional_context += f"\n🌟 区域特征偏好：{', '.join(location_analysis['area_characteristics'])}"
        
        # 添加意图分析结果
        if intent_analysis:
            size_analysis = intent_analysis.get("size_analysis", {})
            if size_analysis.get("size_preference"):
                additional_context += f"\n📐 房屋大小偏好：{size_analysis['size_preference']}"
            if size_analysis.get("inferred_bedrooms"):
                additional_context += f"\n🛏️ AI推测卧室需求：{size_analysis['inferred_bedrooms']}室"
        
        return f"""你是一位专业的房产推荐顾问，请基于深度需求分析为用户提供个性化推荐。

用户原始需求：{user_input}
提取的明确需求：{requirements_text}

🧠 AI深度分析结果：{additional_context}

🏠 匹配的悉尼房源数据（{len(properties)}套房源）：
{properties_text}

请基于以下原则提供推荐：

1. **智能匹配**：
   - 优先匹配用户明确需求
   - 考虑AI推测的隐含需求
   - 结合地理位置偏好和区域特征

2. **个性化推荐理由**：
   - 解释为什么这个房源适合用户
   - 结合用户的口语化表达（如"大一点的"、"离市区远"）
   - 说明房源如何满足用户的生活方式需求

3. **全面考虑**：
   - 如果用户要求"离市区远"，重点推荐外环区域的性价比房源
   - 如果用户要求"大一点的"，重点推荐空间较大的房源
   - 如果用户要求"安静"，重点推荐住宅区而非商业区

请提供3-5条推荐，格式：
推荐1：[具体房源地址 - 价格] - [个性化推荐理由，说明如何满足用户的具体需求]
推荐2：[具体房源地址 - 价格] - [个性化推荐理由，说明如何满足用户的具体需求]
推荐3：[具体房源地址 - 价格] - [个性化推荐理由，说明如何满足用户的具体需求]
（如有更多优质选择可继续）"""
    
    def _parse_recommendations(self, content: str) -> List[str]:
        """解析推荐结果"""
        recommendations = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('推荐1：'):
                recommendations.append(line[4:])
            elif line.startswith('推荐2：'):
                recommendations.append(line[4:])
            elif line.startswith('推荐3：'):
                recommendations.append(line[4:])
            elif line.startswith('推荐4：'):
                recommendations.append(line[4:])
            elif line.startswith('推荐5：'):
                recommendations.append(line[4:])
        
        # 如果解析失败，返回原始内容的有效行
        if len(recommendations) == 0:
            lines = [l.strip() for l in content.split('\n') if l.strip()]
            recommendations = lines[:5] if len(lines) >= 5 else lines
        
        return recommendations

# 全局推荐服务实例
recommendation_service = RecommendationService()