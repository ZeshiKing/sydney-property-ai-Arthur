"""
房产数据模型
定义房产相关的数据结构
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

class PropertyType(Enum):
    """房产类型枚举"""
    APARTMENT = "Apartment / Unit / Flat"
    HOUSE = "House"
    TOWNHOUSE = "Townhouse"
    VILLA = "Villa"
    STUDIO = "Studio"
    OTHER = "Other"

@dataclass
class Property:
    """房产数据模型"""
    address: str
    suburb: str
    price: str
    price_numeric: Optional[float]
    bedrooms: int
    bathrooms: int
    parking: int
    property_type: str
    link: str
    
    def __post_init__(self):
        """后处理方法"""
        # 标准化房产类型
        if self.property_type:
            for prop_type in PropertyType:
                if prop_type.value.lower() in self.property_type.lower():
                    self.property_type = prop_type.value
                    break
    
    @property
    def display_price(self) -> str:
        """格式化显示价格"""
        return self.price if self.price else "Contact Agent"
    
    @property
    def price_per_bedroom(self) -> Optional[float]:
        """每卧室价格"""
        if self.price_numeric and self.bedrooms > 0:
            return self.price_numeric / self.bedrooms
        return None
    
    def matches_criteria(self, bedrooms: Optional[int] = None, 
                        max_price: Optional[float] = None,
                        suburb: Optional[str] = None) -> bool:
        """检查是否匹配筛选条件"""
        if bedrooms and self.bedrooms != bedrooms:
            return False
        if max_price and self.price_numeric and self.price_numeric > max_price:
            return False
        if suburb and suburb.lower() not in self.suburb.lower():
            return False
        return True

@dataclass
class UserIntent:
    """用户意图数据模型"""
    suburb: Optional[str] = None
    bedrooms: Optional[int] = None
    budget: Optional[float] = None  # 万澳币
    property_type: Optional[str] = None
    size_preference: Optional[str] = None
    location_preference: Optional[str] = None
    distance_from_city: Optional[str] = None
    special_requirements: List[str] = None
    inferred_needs: List[str] = None
    priority_analysis: str = ""
    
    def __post_init__(self):
        if self.special_requirements is None:
            self.special_requirements = []
        if self.inferred_needs is None:
            self.inferred_needs = []
    
    @property
    def budget_aud(self) -> Optional[float]:
        """预算转换为澳币"""
        return self.budget * 10000 if self.budget else None
    
    def has_criteria(self) -> bool:
        """检查是否有有效的搜索条件"""
        return any([self.suburb, self.bedrooms, self.budget])

@dataclass
class Recommendation:
    """推荐结果数据模型"""
    property: Property
    reason: str
    match_score: float = 0.0
    
    def __post_init__(self):
        """计算匹配分数"""
        self.match_score = self._calculate_match_score()
    
    def _calculate_match_score(self) -> float:
        """计算匹配分数（0-1）"""
        # 简单的分数计算逻辑，后续可以优化
        base_score = 0.5
        if self.property.price_numeric:
            base_score += 0.2
        if self.property.bedrooms > 0:
            base_score += 0.2
        if "推荐" in self.reason:
            base_score += 0.1
        return min(base_score, 1.0)