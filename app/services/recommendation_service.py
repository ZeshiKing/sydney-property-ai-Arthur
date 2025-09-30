"""
Property Recommendation Service

房产智能推荐服务
"""

from __future__ import annotations

import json
import math
import time
import datetime as dt
from typing import TYPE_CHECKING, Dict, Any, List, Optional
import logging

if TYPE_CHECKING:
    from app.api.api_v1.endpoints.properties import PropertyModel

logger = logging.getLogger(__name__)


class PropertyRecommendationService:
    """房产推荐服务"""
    
    def __init__(self):
        """初始化推荐服务"""
        # 推荐权重配置
        self.weights = {
            "priceU": 0.34,    # 用户价格偏好
            "area": 0.22,      # 区域匹配
            "beds": 0.14,      # 卧室数量
            "baths": 0.08,     # 卫浴数量
            "ptype": 0.06,     # 房产类型
            "priceA": 0.08,    # 区域价格合理性
            "park": 0.05,      # 停车位
            "features": 0.02,  # 特色功能
            "fresh": 0.01      # 数据新鲜度
        }
        
        # 相似房产类型集合
        self.similar_types = {"apartment", "unit", "flat"}
    
    def build_query_from_request(self, search_request: Dict[str, Any], 
                               file_default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """从搜索请求构建标准化查询参数
        
        Args:
            search_request: 搜索请求参数
            file_default: 默认配置参数
            
        Returns:
            Dict: 标准化查询参数
        """
        file_default = file_default or {}
        
        # 区域处理
        location = search_request.get('location', '').strip().lower()
        if not location:
            loc = file_default.get('location', {})
            if isinstance(loc, dict):
                location = loc.get('suburb', '').strip().lower()
            else:
                location = str(loc).strip().lower()
        
        # 类型处理
        listing_type = (search_request.get('listing_type', '') or 
                       file_default.get('listingType', '')).lower()
        if not listing_type:
            listing_type = 'rent'  # 默认租房
            
        property_type = (search_request.get('property_type', '') or 
                        file_default.get('propertyType', '')).lower()
        
        # 卧室卫浴
        bedrooms = self._to_int(search_request.get('bedrooms'))
        bathrooms = self._to_int(search_request.get('bathrooms'))
        
        if bedrooms is None:
            br = file_default.get('bedrooms', {})
            bedrooms = br.get('min') if isinstance(br, dict) else self._to_int(br)
        
        # 价格处理
        min_price = self._to_int(search_request.get('min_price'))
        max_price = self._to_int(search_request.get('max_price'))
        
        # 如果没有价格范围，从默认配置获取
        if min_price is None and max_price is None:
            pr = file_default.get('priceRange', {})
            min_price = self._to_int(pr.get('min'))
            max_price = self._to_int(pr.get('max'))
        
        # 价格区间自动扩展
        if min_price is not None and max_price is None:
            max_price = min_price + max(int(0.08 * min_price), 100)
        if max_price is not None and min_price is None:
            min_price = max_price - max(int(0.08 * max_price), 100)
        if min_price is not None and max_price is not None and min_price == max_price:
            band = max(int(0.08 * min_price), 100)
            min_price, max_price = min_price - band, max_price + band
        
        # 停车位和宠物
        parking_required = (self._to_int(search_request.get('parking', 0)) or 0) > 0
        pets_required = bool(search_request.get('pet_friendly', False))
        
        query = {
            'suburb': location,
            'listingType': listing_type,
            'propertyType': property_type,
            'beds_min': bedrooms,
            'baths_min': bathrooms,
            'pmin': min_price,
            'pmax': max_price,
            'unit': 'per_week',
            'must_park': parking_required,
            'pets_req': pets_required
        }
        
        logger.debug(f"Normalized query: {query}")
        return query
    
    def recommend_properties(self, properties: List[PropertyModel], 
                           query: Dict[str, Any], topk: int = 10) -> List[Dict[str, Any]]:
        """推荐房产
        
        Args:
            properties: 房产列表
            query: 标准化查询参数
            topk: 返回Top K结果
            
        Returns:
            List[Dict]: 推荐结果列表
        """
        if not properties:
            return []
        
        # 计算区域价格范围
        area_prices = [self._extract_price_per_week(prop.price) for prop in properties]
        area_prices = [p for p in area_prices if p is not None]
        
        area_min = min(area_prices) if area_prices else None
        area_max = max(area_prices) if area_prices else None
        
        recommendations = []
        
        for prop in properties:
            # 硬性筛选条件
            if not self._passes_hard_filters(prop, query):
                continue
            
            # 计算推荐得分
            score_info = self._calculate_score(prop, query, area_min, area_max)
            
            if score_info:
                recommendations.append(score_info)
        
        # 排序：总分降序 -> 价格接近用户预算中心 -> 价格更低
        def sort_key(x):
            price_delta = self._price_delta_to_user(x, query)
            price_value = x.get('price_pw') or float('inf')
            return (-x['score'], price_delta, price_value)
        
        recommendations.sort(key=sort_key)
        
        return recommendations[:topk]
    
    def _passes_hard_filters(self, prop: PropertyModel, query: Dict[str, Any]) -> bool:
        """检查是否通过硬性筛选条件"""
        # 区域筛选
        prop_location = (prop.location or '').strip().lower()
        query_location = query.get('suburb', '').strip().lower()
        
        if query_location and query_location not in prop_location:
            return False
        
        # 租售类型筛选
        if query.get('listingType'):
            # 这里假设所有房产都是租房，实际情况需要从prop中获取
            pass
        
        # 卧室最小要求
        beds_min = query.get('beds_min')
        if beds_min is not None and (prop.bedrooms is None or prop.bedrooms < beds_min):
            return False
        
        # 卫浴最小要求
        baths_min = query.get('baths_min')
        if baths_min is not None and (prop.bathrooms is None or prop.bathrooms < baths_min):
            return False
        
        # 停车位要求
        if query.get('must_park', False):
            if not (isinstance(prop.parking, int) and prop.parking > 0):
                return False
        
        return True
    
    def _calculate_score(self, prop: PropertyModel, query: Dict[str, Any], 
                        area_min: Optional[float], area_max: Optional[float]) -> Optional[Dict[str, Any]]:
        """计算房产推荐得分"""
        try:
            # 提取基本信息
            price_pw = self._extract_price_per_week(prop.price)
            prop_type = (prop.property_type or '').lower()
            
            # 计算各项子得分
            score_price_user = self._score_price_user(price_pw, query.get('pmin'), query.get('pmax'))
            score_area = 1.0  # 区域已通过硬筛选
            score_beds = self._score_bedrooms(prop.bedrooms, query.get('beds_min'))
            score_baths = self._score_bathrooms(prop.bathrooms, query.get('baths_min'))
            score_ptype = self._score_property_type(prop_type, query.get('propertyType'))
            score_price_area = self._score_price_area(price_pw, area_min, area_max)
            score_parking = self._score_parking(prop.parking, query.get('must_park', False))
            score_features = self._score_features(prop.features)
            score_fresh = self._score_freshness(prop.scraped_at)
            
            # 计算总得分
            total_score = 100 * (
                self.weights["priceU"] * score_price_user +
                self.weights["area"] * score_area +
                self.weights["beds"] * score_beds +
                self.weights["baths"] * score_baths +
                self.weights["ptype"] * score_ptype +
                self.weights["priceA"] * score_price_area +
                self.weights["park"] * score_parking +
                self.weights["features"] * score_features +
                self.weights["fresh"] * score_fresh
            )
            
            return {
                "id": prop.id,
                "score": round(total_score, 2),
                "price_pw": price_pw,
                "bedrooms": prop.bedrooms,
                "bathrooms": prop.bathrooms,
                "parking": prop.parking,
                "propertyType": prop_type,
                "address": prop.location,
                "title": prop.title,
                "url": prop.url,
                "agent": prop.agent,
                "features": prop.features,
                "images": prop.images,
                "subscores": {
                    "price_user": round(100 * self.weights["priceU"] * score_price_user, 2),
                    "area": round(100 * self.weights["area"] * score_area, 2),
                    "beds": round(100 * self.weights["beds"] * score_beds, 2),
                    "baths": round(100 * self.weights["baths"] * score_baths, 2),
                    "ptype": round(100 * self.weights["ptype"] * score_ptype, 2),
                    "price_area": round(100 * self.weights["priceA"] * score_price_area, 2),
                    "parking": round(100 * self.weights["park"] * score_parking, 2),
                    "features": round(100 * self.weights["features"] * score_features, 2),
                    "fresh": round(100 * self.weights["fresh"] * score_fresh, 2),
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating score for property {prop.id}: {e}")
            return None
    
    # 得分计算辅助方法
    def _score_price_user(self, price_pw: Optional[float], pmin: Optional[int], pmax: Optional[int]) -> float:
        """用户价格偏好得分"""
        if price_pw is None or pmin is None or pmax is None:
            return 0.3
        center = (pmin + pmax) / 2
        scale = max(30.0, (pmax - pmin) / 2 or 30.0)
        return self._clamp01(1.0 - abs(price_pw - center) / scale)
    
    def _score_bedrooms(self, bedrooms: Optional[int], beds_min: Optional[int]) -> float:
        """卧室数量得分"""
        if beds_min is None:
            return 0.7 if bedrooms is None else 0.7 + 0.15 * min(bedrooms, 2) / 2
        if bedrooms is None or bedrooms < beds_min:
            return 0.0
        diff = bedrooms - beds_min
        return {0: 1.0, 1: 0.8, 2: 0.6}.get(diff, 0.5)
    
    def _score_bathrooms(self, bathrooms: Optional[int], baths_min: Optional[int]) -> float:
        """卫浴数量得分"""
        if baths_min is None:
            return 0.7 if bathrooms is None else min(1.0, 0.7 + 0.3 * min(bathrooms, 2) / 2)
        if bathrooms is None or bathrooms < baths_min:
            return 0.0
        diff = bathrooms - baths_min
        return {0: 1.0, 1: 0.8, 2: 0.6}.get(diff, 0.5)
    
    def _score_property_type(self, prop_type: str, want_type: Optional[str]) -> float:
        """房产类型得分"""
        if not want_type:
            return 0.7
        if prop_type == want_type:
            return 1.0
        if {prop_type, want_type} <= self.similar_types:
            return 0.7
        return 0.2
    
    def _score_price_area(self, price_pw: Optional[float], area_min: Optional[float], area_max: Optional[float]) -> float:
        """区域价格合理性得分"""
        if price_pw is None or area_min is None or area_max is None:
            return 0.5
        if area_min >= area_max:
            return 0.5
        if area_min <= price_pw <= area_max:
            rel = (price_pw - area_min) / (area_max - area_min + 1e-9)
            return self._clamp01(1.0 - 0.6 * abs(rel - 0.4))
        over = area_min - price_pw if price_pw < area_min else price_pw - area_max
        scale = max(50.0, (area_max - area_min) / 3)
        return self._clamp01(1.0 - over / scale)
    
    def _score_parking(self, parking: Optional[int], must_park: bool) -> float:
        """停车位得分"""
        has_parking = isinstance(parking, int) and parking > 0
        if must_park:
            return 1.0 if has_parking else 0.0
        return 1.0 if has_parking else 0.7
    
    def _score_features(self, features: Optional[List[str]]) -> float:
        """特色功能得分"""
        if not features:
            return 0.0
        
        bonus_features = ['air conditioning', 'balcony', 'furnished', 'dishwasher', 'gym', 'pool']
        feature_text = ' '.join(features).lower()
        
        score = 0.0
        for feature in bonus_features:
            if feature in feature_text:
                score += 0.2
        
        return min(1.0, score)
    
    def _score_freshness(self, scraped_at: Optional[str]) -> float:
        """数据新鲜度得分"""
        if not scraped_at:
            return 0.7
        
        try:
            scraped_time = dt.datetime.fromisoformat(scraped_at.replace('Z', '+00:00'))
            now = dt.datetime.now(dt.timezone.utc)
            days = (now - scraped_time).days
            
            if days <= 7:
                return 1.0
            elif days <= 30:
                return 0.85
            elif days <= 90:
                return 0.6
            else:
                return 0.4
        except:
            return 0.7
    
    # 辅助方法
    def _extract_price_per_week(self, price_str: Optional[str]) -> Optional[float]:
        """从价格字符串提取周租金"""
        if not price_str:
            return None
        
        import re
        # 匹配价格数字
        match = re.search(r'\$?(\d+)', price_str)
        if match:
            amount = float(match.group(1))
            # 简单假设都是周租金
            return amount
        
        return None
    
    def _price_delta_to_user(self, recommendation: Dict[str, Any], query: Dict[str, Any]) -> float:
        """计算价格与用户预算中心的距离"""
        pmin = query.get('pmin')
        pmax = query.get('pmax')
        price_pw = recommendation.get('price_pw')
        
        if pmin is None or pmax is None or price_pw is None:
            return 1e9
        
        center = (pmin + pmax) / 2
        return abs(price_pw - center)
    
    def _to_int(self, value: Any) -> Optional[int]:
        """安全转换为整数"""
        try:
            return int(float(value))
        except:
            return None
    
    def _clamp01(self, value: float) -> float:
        """将值限制在[0,1]范围内"""
        return max(0.0, min(1.0, value))


# 单例实例
recommendation_service = PropertyRecommendationService()