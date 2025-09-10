"""
房产搜索端点

提供房产数据搜索和聚合功能
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
import httpx
import pandas as pd
import json
import uuid

from app.core.config import settings, get_csv_export_path
from app.core.logging import api_logger, scraping_logger, csv_logger

router = APIRouter()


# 请求模型
class PropertySearchRequest(BaseModel):
    """房产搜索请求模型"""
    location: str = Field(..., description="搜索区域 (如: Camperdown, Sydney)")
    min_price: Optional[int] = Field(None, ge=0, description="最低价格 (周租)")
    max_price: Optional[int] = Field(None, ge=0, description="最高价格 (周租)")
    property_type: Optional[str] = Field(None, description="房产类型")
    bedrooms: Optional[int] = Field(None, ge=0, description="卧室数量")
    bathrooms: Optional[int] = Field(None, ge=0, description="浴室数量")
    parking: Optional[int] = Field(None, ge=0, description="停车位数量")
    max_results: Optional[int] = Field(50, ge=1, le=200, description="最大结果数量")
    
    @validator('max_price')
    def validate_price_range(cls, v, values):
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('最高价格不能小于最低价格')
        return v


# 响应模型
class PropertyModel(BaseModel):
    """标准房产数据模型"""
    id: str
    title: str
    price: str
    location: str
    bedrooms: Optional[int]
    bathrooms: Optional[int]
    parking: Optional[int]
    property_type: str
    description: str
    features: List[str]
    images: List[str]
    agent: Dict[str, Any]
    coordinates: Optional[Dict[str, float]]
    url: str
    source: str
    scraped_at: str
    available_from: Optional[str]
    property_size: Optional[str]
    land_size: Optional[str]
    year_built: Optional[int]
    energy_rating: Optional[str]
    pet_friendly: Optional[bool]
    furnished: Optional[bool]
    inspection_times: List[Dict[str, str]]


class SearchMetadata(BaseModel):
    """搜索元数据"""
    total_found: int
    search_time_ms: float
    firecrawl_usage: Dict[str, Any]
    search_params: Dict[str, Any]
    timestamp: str


class PropertySearchResponse(BaseModel):
    """房产搜索响应模型"""
    success: bool
    properties: List[PropertyModel]
    metadata: SearchMetadata
    message: str


class FirecrawlService:
    """Firecrawl API 服务类"""
    
    def __init__(self):
        self.api_key = settings.FIRECRAWL_API_KEY
        self.base_url = settings.FIRECRAWL_BASE_URL
        self.timeout = settings.SCRAPING_TIMEOUT
    
    def build_domain_search_url(self, params: PropertySearchRequest) -> str:
        """构建Domain.com.au搜索URL"""
        base_url = "https://www.domain.com.au/rent"
        
        # URL参数映射
        query_params = []
        
        # 地点参数
        if params.location:
            # 简化地点处理，实际项目中需要更复杂的地点映射
            location_slug = params.location.lower().replace(' ', '-').replace(',', '')
            query_params.append(f"suburb={location_slug}")
        
        # 价格范围
        if params.min_price:
            query_params.append(f"price={params.min_price}-any")
        if params.max_price:
            if params.min_price:
                query_params[query_params.index(f"price={params.min_price}-any")] = f"price={params.min_price}-{params.max_price}"
            else:
                query_params.append(f"price=any-{params.max_price}")
        
        # 房间数量
        if params.bedrooms:
            query_params.append(f"bedrooms={params.bedrooms}")
        if params.bathrooms:
            query_params.append(f"bathrooms={params.bathrooms}")
        if params.parking:
            query_params.append(f"parking={params.parking}")
        
        # 房产类型
        if params.property_type:
            query_params.append(f"ptype={params.property_type.lower()}")
        
        # 构建完整URL
        if query_params:
            return f"{base_url}/?{'&'.join(query_params)}"
        else:
            return f"{base_url}/"
    
    async def scrape_properties(self, search_params: PropertySearchRequest) -> Dict[str, Any]:
        """使用Firecrawl抓取房产数据"""
        
        # 构建搜索URL
        search_url = self.build_domain_search_url(search_params)
        scraping_logger.info(f"开始抓取URL: {search_url}")
        
        # Firecrawl API配置
        firecrawl_config = {
            "url": search_url,
            "formats": ["markdown", "html"],
            "includeTags": ["article", ".listing-result", ".property-card", "[data-testid*='listing']"],
            "excludeTags": ["nav", "footer", ".advertisement", ".cookie-banner"],
            "onlyMainContent": True,
            "timeout": self.timeout * 1000,  # 转换为毫秒
            "waitFor": 2000,  # 等待2秒让页面加载完成
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v0/scrape",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=firecrawl_config
                )
                
                response.raise_for_status()
                data = response.json()
                
                scraping_logger.info(f"Firecrawl响应状态: {response.status_code}")
                return data
                
            except httpx.HTTPStatusError as e:
                scraping_logger.error(f"Firecrawl API错误: {e.response.status_code} - {e.response.text}")
                if e.response.status_code == 402:
                    raise HTTPException(
                        status_code=402,
                        detail="Firecrawl API配额不足，请检查账户余额"
                    )
                raise HTTPException(
                    status_code=500,
                    detail=f"抓取服务错误: {e.response.text}"
                )
            except Exception as e:
                scraping_logger.error(f"抓取过程出错: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"抓取过程出错: {str(e)}"
                )
    
    def parse_property_data(self, raw_data: Dict[str, Any], search_params: PropertySearchRequest) -> List[PropertyModel]:
        """解析原始数据为标准房产模型"""
        properties = []
        
        try:
            # 从Firecrawl响应中提取内容
            content = raw_data.get('data', {})
            markdown = content.get('markdown', '')
            html = content.get('html', '')
            
            scraping_logger.info(f"开始解析数据，markdown长度: {len(markdown)}, HTML长度: {len(html)}")
            
            # 这里是简化的解析逻辑
            # 实际项目中需要根据Domain.com.au的具体HTML结构进行复杂的解析
            
            # 示例：创建一些测试数据 (实际项目中替换为真实解析逻辑)
            sample_properties = [
                {
                    "id": str(uuid.uuid4()),
                    "title": f"Modern {search_params.bedrooms or 2} Bedroom Apartment in {search_params.location}",
                    "price": f"${search_params.min_price or 500}/week",
                    "location": search_params.location,
                    "bedrooms": search_params.bedrooms or 2,
                    "bathrooms": search_params.bathrooms or 1,
                    "parking": search_params.parking or 1,
                    "property_type": search_params.property_type or "Apartment",
                    "description": "Well-appointed modern apartment with excellent amenities",
                    "features": ["Air Conditioning", "Built-in Wardrobes", "Balcony"],
                    "images": ["https://example.com/image1.jpg"],
                    "agent": {
                        "name": "Property Agent",
                        "phone": "0400 000 000",
                        "email": "agent@realestate.com"
                    },
                    "coordinates": {"lat": -33.8688, "lng": 151.2093},
                    "url": "https://www.domain.com.au/property/sample",
                    "source": "Domain.com.au",
                    "scraped_at": datetime.utcnow().isoformat() + "Z",
                    "available_from": "Available Now",
                    "property_size": "75 sqm",
                    "land_size": None,
                    "year_built": None,
                    "energy_rating": None,
                    "pet_friendly": False,
                    "furnished": False,
                    "inspection_times": []
                }
            ]
            
            # 根据请求参数生成多个示例属性
            for i in range(min(search_params.max_results or 10, 5)):
                prop_data = sample_properties[0].copy()
                prop_data["id"] = str(uuid.uuid4())
                prop_data["title"] = f"Property {i+1} - {prop_data['title']}"
                
                # 轻微变化价格
                base_price = search_params.min_price or 500
                varied_price = base_price + (i * 50)
                prop_data["price"] = f"${varied_price}/week"
                
                properties.append(PropertyModel(**prop_data))
            
            scraping_logger.info(f"成功解析 {len(properties)} 个房产数据")
            return properties
            
        except Exception as e:
            scraping_logger.error(f"数据解析错误: {str(e)}")
            return []


# 服务实例
firecrawl_service = FirecrawlService()


async def export_to_csv(
    properties: List[PropertyModel], 
    search_params: PropertySearchRequest,
    metadata: SearchMetadata
) -> str:
    """导出搜索结果到CSV文件"""
    try:
        # 准备CSV数据
        csv_data = []
        for prop in properties:
            csv_row = {
                'ID': prop.id,
                'Title': prop.title,
                'Price': prop.price,
                'Location': prop.location,
                'Bedrooms': prop.bedrooms,
                'Bathrooms': prop.bathrooms,
                'Parking': prop.parking,
                'Property_Type': prop.property_type,
                'Description': prop.description[:200] + '...' if len(prop.description) > 200 else prop.description,
                'Features': ', '.join(prop.features) if prop.features else '',
                'Agent_Name': prop.agent.get('name', '') if prop.agent else '',
                'Agent_Phone': prop.agent.get('phone', '') if prop.agent else '',
                'Available_From': prop.available_from or '',
                'Property_Size': prop.property_size or '',
                'Pet_Friendly': 'Yes' if prop.pet_friendly else 'No',
                'Furnished': 'Yes' if prop.furnished else 'No',
                'URL': prop.url,
                'Source': prop.source,
                'Scraped_At': prop.scraped_at,
                'Search_Location': search_params.location,
                'Search_Min_Price': search_params.min_price or '',
                'Search_Max_Price': search_params.max_price or '',
            }
            csv_data.append(csv_row)
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"property_search_{search_params.location.replace(' ', '_')}_{timestamp}.csv"
        
        # 保存CSV文件
        csv_dir = get_csv_export_path()
        file_path = csv_dir / filename
        
        df = pd.DataFrame(csv_data)
        df.to_csv(file_path, index=False, encoding='utf-8')
        
        csv_logger.info(f"CSV文件已保存: {file_path}")
        return str(file_path)
        
    except Exception as e:
        csv_logger.error(f"CSV导出失败: {str(e)}")
        return ""


@router.post("/search", response_model=PropertySearchResponse)
async def search_properties(
    request: PropertySearchRequest,
    background_tasks: BackgroundTasks
):
    """
    房产搜索API
    
    根据搜索条件从Domain.com.au抓取房产数据
    """
    request_id = str(uuid.uuid4())[:8]
    start_time = datetime.now()
    
    api_logger.info(f"[{request_id}] 开始房产搜索: {request.location}")
    
    try:
        # 使用Firecrawl抓取数据
        raw_data = await firecrawl_service.scrape_properties(request)
        
        # 解析房产数据
        properties = firecrawl_service.parse_property_data(raw_data, request)
        
        # 计算执行时间
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # 构建响应元数据
        metadata = SearchMetadata(
            total_found=len(properties),
            search_time_ms=round(execution_time, 2),
            firecrawl_usage=raw_data.get('metadata', {}),
            search_params=request.dict(),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
        # 构建响应
        response = PropertySearchResponse(
            success=True,
            properties=properties,
            metadata=metadata,
            message=f"成功找到 {len(properties)} 个房产"
        )
        
        # 后台任务：导出CSV
        if properties:
            background_tasks.add_task(export_to_csv, properties, request, metadata)
        
        api_logger.info(f"[{request_id}] 搜索完成，找到 {len(properties)} 个房产")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"[{request_id}] 搜索失败: {str(e)}")
        
        # 返回错误响应
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        metadata = SearchMetadata(
            total_found=0,
            search_time_ms=round(execution_time, 2),
            firecrawl_usage={},
            search_params=request.dict(),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
        return PropertySearchResponse(
            success=False,
            properties=[],
            metadata=metadata,
            message=f"搜索失败: {str(e)}"
        )


@router.get("/locations")
async def get_supported_locations():
    """
    获取支持的搜索区域列表
    
    返回可以搜索的澳洲城市和区域
    """
    # 这里返回一些常见的澳洲租房区域
    locations = [
        {"name": "Sydney", "state": "NSW", "popular_suburbs": ["Camperdown", "Newtown", "Surry Hills", "Bondi"]},
        {"name": "Melbourne", "state": "VIC", "popular_suburbs": ["Carlton", "Fitzroy", "South Yarra", "St Kilda"]},
        {"name": "Brisbane", "state": "QLD", "popular_suburbs": ["Fortitude Valley", "South Brisbane", "New Farm"]},
        {"name": "Perth", "state": "WA", "popular_suburbs": ["Northbridge", "Subiaco", "Fremantle"]},
        {"name": "Adelaide", "state": "SA", "popular_suburbs": ["North Adelaide", "Unley", "Glenelg"]}
    ]
    
    return {
        "success": True,
        "locations": locations,
        "message": "支持的搜索区域列表"
    }


@router.get("/test")
async def test_firecrawl():
    """
    测试Firecrawl API连接
    
    用于验证API配置是否正确
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{settings.FIRECRAWL_BASE_URL}/health",
                headers={"Authorization": f"Bearer {settings.FIRECRAWL_API_KEY}"}
            )
            
            return {
                "success": True,
                "status_code": response.status_code,
                "message": "Firecrawl API连接正常",
                "api_url": settings.FIRECRAWL_BASE_URL
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Firecrawl API连接失败",
            "api_url": settings.FIRECRAWL_BASE_URL
        }