"""
悉尼地区地理分析模块
用于分析地理位置、距离关系和区域特征
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional

class SydneyGeoAnalyzer:
    """悉尼地区地理分析器"""
    
    def __init__(self):
        """初始化地理分析器"""
        self.city_center = "Sydney"  # 市中心
        self.geo_data = self._load_geo_data()
    
    def _load_geo_data(self) -> Dict:
        """加载悉尼地区地理数据"""
        return {
            # 市中心区域（距离市中心0-5km）
            "city_center": {
                "suburbs": ["Sydney", "Circular Quay", "The Rocks", "Barangaroo", "Millers Point", 
                           "Dawes Point", "Pyrmont", "Ultimo", "Haymarket", "Darlinghurst", 
                           "Surry Hills", "Potts Point", "Kings Cross", "Woolloomooloo"],
                "distance_from_city": "近",
                "characteristics": ["繁华", "便利", "商业区", "交通枢纽", "高端", "昂贵"],
                "price_range": "high"
            },
            
            # 内城区（距离市中心5-15km）
            "inner_city": {
                "suburbs": ["Bondi", "Bondi Beach", "Coogee", "Paddington", "Newtown", "Glebe", 
                           "Leichhardt", "Balmain", "Rozelle", "Annandale", "Marrickville", 
                           "Enmore", "Redfern", "Erskineville", "Alexandria", "Waterloo",
                           "Cremorne", "Mosman", "Neutral Bay", "North Sydney", "Crows Nest"],
                "distance_from_city": "近",
                "characteristics": ["便利", "文化", "咖啡文化", "年轻", "活跃", "交通便利"],
                "price_range": "medium-high"
            },
            
            # 中环区（距离市中心15-25km）
            "middle_ring": {
                "suburbs": ["Chatswood", "Hornsby", "Parramatta", "Burwood", "Strathfield", 
                           "Ashfield", "Croydon", "Bankstown", "Liverpool", "Blacktown",
                           "Eastwood", "Epping", "Ryde", "Meadowbank", "Olympic Park",
                           "Homebush", "Concord", "Drummoyne", "Five Dock", "Canada Bay"],
                "distance_from_city": "中",
                "characteristics": ["平衡", "家庭友好", "学校", "购物中心", "多元文化"],
                "price_range": "medium"
            },
            
            # 外环区（距离市中心25-40km）
            "outer_ring": {
                "suburbs": ["Manly", "Dee Why", "Brookvale", "Warringah", "Penrith", "Campbelltown", 
                           "Sutherland", "Cronulla", "Hurstville", "Kogarah", "Rockdale",
                           "Castle Hill", "Kellyville", "Baulkham Hills", "Blacktown", "Mount Druitt",
                           "Fairfield", "Cabramatta", "Banksia", "Beverly Hills"],
                "distance_from_city": "中",
                "characteristics": ["郊区", "家庭", "安静", "性价比", "自然环境"],
                "price_range": "medium-low"
            },
            
            # 远郊区（距离市中心40km+）
            "far_suburbs": {
                "suburbs": ["Wollongong", "Gosford", "Wyong", "Camden", "Picton", "Richmond", 
                           "Windsor", "Penrith", "Blue Mountains", "Hawkesbury", "Campbelltown",
                           "Appin", "Helensburgh", "Thirroul", "Goulburn"],
                "distance_from_city": "远",
                "characteristics": ["偏远", "便宜", "大房子", "自然", "安静", "远离喧嚣"],
                "price_range": "low"
            },
            
            # 海边区域
            "coastal": {
                "suburbs": ["Bondi", "Bondi Beach", "Coogee", "Bronte", "Tamarama", "Vaucluse",
                           "Watsons Bay", "Manly", "Dee Why", "Collaroy", "Narrabeen", "Avalon",
                           "Palm Beach", "Cronulla", "Maroubra", "Clovelly", "Randwick"],
                "distance_from_city": "varies",
                "characteristics": ["海景", "海滩", "度假感", "放松", "海边生活"],
                "price_range": "high"
            }
        }
    
    def analyze_location_preference(self, user_input: str, extracted_info: Dict) -> Dict:
        """分析用户的地理位置偏好"""
        location_analysis = {
            "recommended_areas": [],
            "distance_preference": None,
            "area_characteristics": [],
            "price_expectation": None
        }
        
        user_input_lower = user_input.lower()
        
        # 分析距离偏好
        if any(keyword in user_input_lower for keyword in ["离市区远", "远离市区", "郊外", "偏远", "远离喧嚣"]):
            location_analysis["distance_preference"] = "远"
            location_analysis["recommended_areas"].extend(self.geo_data["outer_ring"]["suburbs"])
            location_analysis["recommended_areas"].extend(self.geo_data["far_suburbs"]["suburbs"])
            location_analysis["area_characteristics"].extend(["安静", "性价比高", "大房子"])
            location_analysis["price_expectation"] = "medium-low"
            
        elif any(keyword in user_input_lower for keyword in ["市中心", "市区", "繁华", "便利", "中心"]):
            location_analysis["distance_preference"] = "近"
            location_analysis["recommended_areas"].extend(self.geo_data["city_center"]["suburbs"])
            location_analysis["recommended_areas"].extend(self.geo_data["inner_city"]["suburbs"])
            location_analysis["area_characteristics"].extend(["便利", "繁华", "交通便利"])
            location_analysis["price_expectation"] = "high"
            
        elif any(keyword in user_input_lower for keyword in ["海边", "海滩", "海景", "靠近海"]):
            location_analysis["distance_preference"] = "varies"
            location_analysis["recommended_areas"].extend(self.geo_data["coastal"]["suburbs"])
            location_analysis["area_characteristics"].extend(["海景", "海滩", "度假感"])
            location_analysis["price_expectation"] = "high"
        
        # 分析环境偏好
        if any(keyword in user_input_lower for keyword in ["安静", "静", "宁静", "清静"]):
            location_analysis["area_characteristics"].append("安静环境")
            # 推荐郊区
            location_analysis["recommended_areas"].extend(self.geo_data["outer_ring"]["suburbs"])
            
        if any(keyword in user_input_lower for keyword in ["便民", "方便", "便利", "生活便利"]):
            location_analysis["area_characteristics"].append("生活便利")
            # 推荐中环区
            location_analysis["recommended_areas"].extend(self.geo_data["middle_ring"]["suburbs"])
        
        return location_analysis
    
    def analyze_size_preference(self, user_input: str, extracted_info: Dict) -> Dict:
        """分析用户的房屋大小偏好"""
        size_analysis = {
            "size_preference": None,
            "inferred_bedrooms": None,
            "space_requirements": []
        }
        
        user_input_lower = user_input.lower()
        
        # 分析大小偏好
        if any(keyword in user_input_lower for keyword in ["大一点", "宽敞", "大的", "大房子", "空间大"]):
            size_analysis["size_preference"] = "大"
            size_analysis["space_requirements"].extend(["宽敞", "大空间"])
            # 推测可能需要更多卧室
            current_bedrooms = extracted_info.get("bedrooms")
            if current_bedrooms:
                size_analysis["inferred_bedrooms"] = current_bedrooms + 1
            else:
                size_analysis["inferred_bedrooms"] = 3  # 默认推测3室
                
        elif any(keyword in user_input_lower for keyword in ["小一点", "紧凑", "小的", "小房子", "精致"]):
            size_analysis["size_preference"] = "小"
            size_analysis["space_requirements"].extend(["紧凑", "精致"])
            # 推测可能需要更少卧室
            current_bedrooms = extracted_info.get("bedrooms")
            if current_bedrooms and current_bedrooms > 1:
                size_analysis["inferred_bedrooms"] = current_bedrooms - 1
            else:
                size_analysis["inferred_bedrooms"] = 1  # 默认推测1室
        
        return size_analysis
    
    def get_suburb_info(self, suburb: str) -> Dict:
        """获取特定区域的信息"""
        suburb_lower = suburb.lower()
        
        for area_type, area_data in self.geo_data.items():
            if suburb_lower in [s.lower() for s in area_data["suburbs"]]:
                return {
                    "area_type": area_type,
                    "distance_from_city": area_data["distance_from_city"],
                    "characteristics": area_data["characteristics"],
                    "price_range": area_data["price_range"]
                }
        
        return {
            "area_type": "unknown",
            "distance_from_city": "unknown",
            "characteristics": [],
            "price_range": "unknown"
        }
    
    def find_similar_areas(self, target_suburb: str, preferences: Dict) -> List[str]:
        """根据偏好找到类似的区域"""
        target_info = self.get_suburb_info(target_suburb)
        similar_areas = []
        
        # 找到同类型区域
        for area_type, area_data in self.geo_data.items():
            if area_type == target_info["area_type"]:
                similar_areas.extend(area_data["suburbs"])
        
        # 根据距离偏好调整
        distance_pref = preferences.get("distance_from_city")
        if distance_pref:
            for area_type, area_data in self.geo_data.items():
                if area_data["distance_from_city"] == distance_pref:
                    similar_areas.extend(area_data["suburbs"])
        
        # 去重并返回
        return list(set(similar_areas))
    
    def comprehensive_analysis(self, user_input: str, extracted_info: Dict) -> Dict:
        """综合分析用户需求"""
        location_analysis = self.analyze_location_preference(user_input, extracted_info)
        size_analysis = self.analyze_size_preference(user_input, extracted_info)
        
        return {
            "location_analysis": location_analysis,
            "size_analysis": size_analysis,
            "comprehensive_recommendations": self._generate_comprehensive_recommendations(
                location_analysis, size_analysis, extracted_info
            )
        }
    
    def _generate_comprehensive_recommendations(self, location_analysis: Dict, size_analysis: Dict, extracted_info: Dict) -> Dict:
        """生成综合推荐"""
        recommendations = {
            "priority_areas": [],
            "alternative_areas": [],
            "search_strategy": ""
        }
        
        # 优先推荐区域
        if location_analysis["recommended_areas"]:
            recommendations["priority_areas"] = location_analysis["recommended_areas"][:10]
        
        # 备选区域
        if extracted_info.get("suburb"):
            similar_areas = self.find_similar_areas(extracted_info["suburb"], location_analysis)
            recommendations["alternative_areas"] = similar_areas[:5]
        
        # 搜索策略
        if location_analysis["distance_preference"] == "远":
            recommendations["search_strategy"] = "优先搜索外环和远郊区域，重点关注性价比和房屋大小"
        elif location_analysis["distance_preference"] == "近":
            recommendations["search_strategy"] = "优先搜索市中心和内城区域，重点关注交通便利性"
        else:
            recommendations["search_strategy"] = "平衡搜索各个区域，根据预算和具体需求调整"
        
        return recommendations