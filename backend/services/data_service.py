"""
数据服务模块
处理房产数据的加载、筛选和管理
"""

import pandas as pd
from typing import List, Optional
from pathlib import Path

from backend.models.property import Property, UserIntent
from backend.utils.logger import data_logger
from config.settings import settings

class DataService:
    """数据服务类"""
    
    def __init__(self):
        self._df: Optional[pd.DataFrame] = None
        self.logger = data_logger
    
    def load_property_data(self) -> pd.DataFrame:
        """加载房产数据"""
        try:
            if self._df is None:
                self.logger.info(f"Loading property data from {settings.PROPERTY_DATA_FILE}")
                self._df = pd.read_csv(settings.PROPERTY_DATA_FILE)
                # 过滤掉价格为空的房源
                self._df = self._df[self._df['price_numeric'].notna()]
                self.logger.info(f"Loaded {len(self._df)} valid properties")
            return self._df
        except FileNotFoundError:
            self.logger.error(f"Property data file not found: {settings.PROPERTY_DATA_FILE}")
            raise FileNotFoundError(f"未找到房产数据文件: {settings.PROPERTY_DATA_FILE}")
        except Exception as e:
            self.logger.error(f"Failed to load property data: {str(e)}")
            raise RuntimeError(f"加载房产数据失败: {str(e)}")
    
    def get_properties(self, limit: Optional[int] = None) -> List[Property]:
        """获取房产列表"""
        df = self.load_property_data()
        if limit:
            df = df.head(limit)
        
        properties = []
        for _, row in df.iterrows():
            property_obj = Property(
                address=row.get('address', ''),
                suburb=row.get('suburb', ''),
                price=row.get('price', ''),
                price_numeric=row.get('price_numeric'),
                bedrooms=int(row.get('bedrooms', 0)),
                bathrooms=int(row.get('bathrooms', 0)),
                parking=int(row.get('parking', 0)),
                property_type=row.get('property_type', ''),
                link=row.get('link', '')
            )
            properties.append(property_obj)
        
        return properties
    
    def filter_properties_flexible(self, intent: UserIntent, 
                                 geo_analysis: Optional[dict] = None) -> List[Property]:
        """灵活筛选房产"""
        df = self.load_property_data()
        original_count = len(df)
        
        # 记录筛选过程
        self.logger.info(f"Starting property filtering with {original_count} properties")
        
        # 1. 尝试完全匹配
        if intent.suburb and intent.bedrooms and intent.budget_aud:
            exact_match = df[
                (df['suburb'].str.contains(intent.suburb, case=False, na=False)) &
                (df['bedrooms'] == intent.bedrooms) &
                (df['price_numeric'] <= intent.budget_aud)
            ]
            if len(exact_match) >= settings.MIN_RESULTS_THRESHOLD:
                self.logger.info(f"Found {len(exact_match)} exact matches")
                return self._df_to_properties(exact_match.head(settings.DEFAULT_RESULT_LIMIT))
        
        # 2. 放宽预算限制
        if intent.suburb and intent.bedrooms and intent.budget_aud:
            relaxed_budget = intent.budget_aud * settings.BUDGET_RELAXATION_FACTOR
            budget_relaxed = df[
                (df['suburb'].str.contains(intent.suburb, case=False, na=False)) &
                (df['bedrooms'] == intent.bedrooms) &
                (df['price_numeric'] <= relaxed_budget)
            ]
            if len(budget_relaxed) >= settings.MIN_RESULTS_THRESHOLD:
                self.logger.info(f"Found {len(budget_relaxed)} matches with relaxed budget")
                return self._df_to_properties(budget_relaxed.head(settings.DEFAULT_RESULT_LIMIT))
        
        # 3. 区域 + 卧室匹配
        if intent.suburb and intent.bedrooms:
            area_bedroom_match = df[
                (df['suburb'].str.contains(intent.suburb, case=False, na=False)) &
                (df['bedrooms'] == intent.bedrooms)
            ]
            if len(area_bedroom_match) >= settings.MIN_RESULTS_THRESHOLD:
                self.logger.info(f"Found {len(area_bedroom_match)} area+bedroom matches")
                return self._df_to_properties(area_bedroom_match.head(settings.DEFAULT_RESULT_LIMIT))
        
        # 4. 仅区域匹配
        if intent.suburb:
            area_match = df[df['suburb'].str.contains(intent.suburb, case=False, na=False)]
            if len(area_match) >= settings.MIN_RESULTS_THRESHOLD:
                self.logger.info(f"Found {len(area_match)} area matches")
                return self._df_to_properties(area_match.head(settings.DEFAULT_RESULT_LIMIT))
        
        # 5. 仅卧室匹配
        if intent.bedrooms:
            bedroom_match = df[df['bedrooms'] == intent.bedrooms]
            if len(bedroom_match) >= settings.MIN_RESULTS_THRESHOLD:
                self.logger.info(f"Found {len(bedroom_match)} bedroom matches")
                return self._df_to_properties(bedroom_match.head(settings.DEFAULT_RESULT_LIMIT))
        
        # 6. 仅预算匹配
        if intent.budget_aud:
            budget_match = df[df['price_numeric'] <= intent.budget_aud]
            if len(budget_match) >= settings.MIN_RESULTS_THRESHOLD:
                self.logger.info(f"Found {len(budget_match)} budget matches")
                return self._df_to_properties(budget_match.head(settings.DEFAULT_RESULT_LIMIT))
        
        # 7. 使用地理分析结果
        if geo_analysis and geo_analysis.get("location_analysis", {}).get("recommended_areas"):
            recommended_areas = geo_analysis["location_analysis"]["recommended_areas"]
            area_pattern = '|'.join(recommended_areas[:10])
            geo_match = df[df['suburb'].str.contains(area_pattern, case=False, na=False)]
            
            if intent.budget_aud:
                geo_match = geo_match[geo_match['price_numeric'] <= intent.budget_aud * settings.BUDGET_RELAXATION_FACTOR]
            if intent.bedrooms:
                geo_match = geo_match[geo_match['bedrooms'] == intent.bedrooms]
            
            if len(geo_match) >= settings.MIN_RESULTS_THRESHOLD:
                self.logger.info(f"Found {len(geo_match)} geo-analysis matches")
                return self._df_to_properties(geo_match.head(settings.DEFAULT_RESULT_LIMIT))
        
        # 8. 返回默认结果
        self.logger.warning("Using default results - no sufficient matches found")
        return self._df_to_properties(df.head(settings.DEFAULT_RESULT_LIMIT))
    
    def _df_to_properties(self, df: pd.DataFrame) -> List[Property]:
        """将DataFrame转换为Property对象列表"""
        properties = []
        for _, row in df.iterrows():
            property_obj = Property(
                address=row.get('address', ''),
                suburb=row.get('suburb', ''),
                price=row.get('price', ''),
                price_numeric=row.get('price_numeric'),
                bedrooms=int(row.get('bedrooms', 0)),
                bathrooms=int(row.get('bathrooms', 0)),
                parking=int(row.get('parking', 0)),
                property_type=row.get('property_type', ''),
                link=row.get('link', '')
            )
            properties.append(property_obj)
        return properties
    
    def get_suburbs(self) -> List[str]:
        """获取所有区域列表"""
        df = self.load_property_data()
        return sorted(df['suburb'].unique().tolist())
    
    def get_property_stats(self) -> dict:
        """获取房产数据统计信息"""
        df = self.load_property_data()
        return {
            "total_properties": len(df),
            "avg_price": df['price_numeric'].mean(),
            "max_price": df['price_numeric'].max(),
            "min_price": df['price_numeric'].min(),
            "unique_suburbs": len(df['suburb'].unique()),
            "property_types": df['property_type'].value_counts().to_dict()
        }

# 单例数据服务实例
data_service = DataService()