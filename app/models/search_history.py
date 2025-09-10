"""
搜索历史数据模型

SQLAlchemy 搜索历史记录表定义
"""

from sqlalchemy import String, Integer, Float, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional, Dict, Any
import uuid

from app.database.base import Base


class SearchHistory(Base):
    """搜索历史记录模型"""
    
    __tablename__ = "search_history"
    
    # 基本信息
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    user_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 搜索参数
    location: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    min_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    max_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    property_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    bedrooms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    bathrooms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    parking: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    max_results: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    
    # 搜索结果统计
    results_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    search_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    firecrawl_usage: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # 搜索状态
    search_status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # success, error, timeout
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 数据质量指标
    data_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    duplicate_results: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # 用户交互
    csv_exported: Mapped[bool] = mapped_column(String(5), default="false", nullable=False)  # 使用字符串以避免布尔类型问题
    results_clicked: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # 完整搜索参数 (JSON)
    search_params: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # 索引定义
    __table_args__ = (
        # 按时间和状态查询索引
        Index('idx_time_status', 'created_at', 'search_status'),
        # 按地点和时间查询索引
        Index('idx_location_time', 'location', 'created_at'),
        # 用户会话查询索引
        Index('idx_session_time', 'session_id', 'created_at'),
        # 搜索性能分析索引
        Index('idx_performance', 'search_time_ms', 'results_found'),
        # 价格范围统计索引
        Index('idx_price_analysis', 'min_price', 'max_price', 'location'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'location': self.location,
            'min_price': self.min_price,
            'max_price': self.max_price,
            'property_type': self.property_type,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'parking': self.parking,
            'max_results': self.max_results,
            'results_found': self.results_found,
            'search_time_ms': self.search_time_ms,
            'search_status': self.search_status,
            'error_message': self.error_message,
            'data_quality_score': self.data_quality_score,
            'csv_exported': self.csv_exported == "true",
            'results_clicked': self.results_clicked,
            'search_params': self.search_params,
            'firecrawl_usage': self.firecrawl_usage,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def from_search_request(
        cls, 
        search_request: 'PropertySearchRequest',
        results_count: int,
        search_time_ms: float,
        search_status: str,
        session_id: Optional[str] = None,
        user_ip: Optional[str] = None,
        error_message: Optional[str] = None,
        firecrawl_usage: Optional[Dict[str, Any]] = None
    ) -> 'SearchHistory':
        """从搜索请求创建历史记录"""
        return cls(
            session_id=session_id,
            user_ip=user_ip,
            location=search_request.location,
            min_price=search_request.min_price,
            max_price=search_request.max_price,
            property_type=search_request.property_type,
            bedrooms=search_request.bedrooms,
            bathrooms=search_request.bathrooms,
            parking=search_request.parking,
            max_results=search_request.max_results or 50,
            results_found=results_count,
            search_time_ms=search_time_ms,
            search_status=search_status,
            error_message=error_message,
            firecrawl_usage=firecrawl_usage,
            search_params=search_request.dict(),
            csv_exported="false"
        )
    
    def mark_csv_exported(self):
        """标记CSV已导出"""
        self.csv_exported = "true"
    
    def increment_clicks(self):
        """增加点击次数"""
        self.results_clicked += 1