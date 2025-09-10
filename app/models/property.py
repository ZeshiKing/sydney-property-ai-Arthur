"""
房产数据模型

SQLAlchemy 房产数据表定义
"""

from sqlalchemy import String, Integer, Float, Text, Boolean, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional, Dict, List, Any
import uuid

from app.database.base import Base


class Property(Base):
    """房产数据模型"""
    
    __tablename__ = "properties"
    
    # 基本信息
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    price: Mapped[str] = mapped_column(String(100), nullable=False)
    price_numeric: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)  # 便于价格筛选
    location: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    suburb: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    state: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    postcode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    
    # 房产特征
    bedrooms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    bathrooms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    parking: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    property_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    property_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    land_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    year_built: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # 描述和特色
    description: Mapped[str] = mapped_column(Text, nullable=False)
    features: Mapped[List[str]] = mapped_column(JSON, nullable=True)
    
    # 图片和媒体
    images: Mapped[List[str]] = mapped_column(JSON, nullable=True)
    virtual_tour_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # 地理位置
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    
    # 出租信息
    available_from: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    lease_term: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bond_amount: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pet_friendly: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, index=True)
    furnished: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, index=True)
    utilities_included: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # 能效和评级
    energy_rating: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # 中介信息
    agent_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    agency_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # 看房时间
    inspection_times: Mapped[List[Dict[str, str]]] = mapped_column(JSON, nullable=True)
    
    # 数据来源
    url: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    scraped_at: Mapped[str] = mapped_column(String(30), nullable=False)
    
    # 数据质量
    data_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # 索引定义
    __table_args__ = (
        # 价格范围查询索引
        Index('idx_price_range', 'price_numeric', 'property_type'),
        # 地理位置查询索引
        Index('idx_location_coords', 'latitude', 'longitude'),
        # 房产特征组合索引
        Index('idx_property_features', 'bedrooms', 'bathrooms', 'parking'),
        # 数据源和状态索引
        Index('idx_source_active', 'source', 'is_active'),
        # 位置和类型组合索引
        Index('idx_location_type', 'suburb', 'property_type', 'is_active'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'title': self.title,
            'price': self.price,
            'location': self.location,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'parking': self.parking,
            'property_type': self.property_type,
            'description': self.description,
            'features': self.features or [],
            'images': self.images or [],
            'agent': self.agent_info or {},
            'coordinates': {
                'lat': self.latitude,
                'lng': self.longitude
            } if self.latitude and self.longitude else None,
            'url': self.url,
            'source': self.source,
            'scraped_at': self.scraped_at,
            'available_from': self.available_from,
            'property_size': self.property_size,
            'land_size': self.land_size,
            'year_built': self.year_built,
            'energy_rating': self.energy_rating,
            'pet_friendly': self.pet_friendly,
            'furnished': self.furnished,
            'inspection_times': self.inspection_times or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_api_model(cls, api_model: 'PropertyModel') -> 'Property':
        """从API模型创建数据库模型"""
        # 提取数字价格 (用于筛选)
        price_numeric = None
        if api_model.price:
            # 简单的价格解析 (例如: "$500/week" -> 500)
            import re
            price_match = re.search(r'\$(\d+)', api_model.price)
            if price_match:
                price_numeric = int(price_match.group(1))
        
        # 提取地理坐标
        lat = lng = None
        if api_model.coordinates:
            lat = api_model.coordinates.get('lat')
            lng = api_model.coordinates.get('lng')
        
        return cls(
            title=api_model.title,
            price=api_model.price,
            price_numeric=price_numeric,
            location=api_model.location,
            bedrooms=api_model.bedrooms,
            bathrooms=api_model.bathrooms,
            parking=api_model.parking,
            property_type=api_model.property_type,
            description=api_model.description,
            features=api_model.features,
            images=api_model.images,
            latitude=lat,
            longitude=lng,
            available_from=api_model.available_from,
            property_size=api_model.property_size,
            land_size=api_model.land_size,
            year_built=api_model.year_built,
            energy_rating=api_model.energy_rating,
            pet_friendly=api_model.pet_friendly,
            furnished=api_model.furnished,
            agent_info=api_model.agent,
            inspection_times=api_model.inspection_times,
            url=api_model.url,
            source=api_model.source,
            scraped_at=api_model.scraped_at,
            is_active=True,
            is_verified=False
        )