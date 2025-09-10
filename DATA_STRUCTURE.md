# 数据结构文档 - Python FastAPI 版本

**澳洲租房聚合系统** - 房产数据结构和API接口规范

## 📊 核心数据模型

### 1. 房产搜索请求 (PropertySearchRequest)

```python
class PropertySearchRequest(BaseModel):
    location: str                    # 必需：搜索区域
    min_price: Optional[int]         # 可选：最低价格 (周租)
    max_price: Optional[int]         # 可选：最高价格 (周租)  
    property_type: Optional[str]     # 可选：房产类型
    bedrooms: Optional[int]          # 可选：卧室数量
    bathrooms: Optional[int]         # 可选：浴室数量
    parking: Optional[int]           # 可选：停车位数量
    max_results: Optional[int] = 50  # 可选：最大结果数量 (1-200)
```

**JSON示例**:
```json
{
  "location": "Camperdown",
  "min_price": 500,
  "max_price": 800,
  "bedrooms": 2,
  "bathrooms": 1,
  "property_type": "Apartment",
  "max_results": 20
}
```

### 2. 房产数据模型 (PropertyModel)

```python
class PropertyModel(BaseModel):
    # 基本信息
    id: str                          # 房产唯一标识
    title: str                       # 房产标题
    price: str                       # 租金价格 (如: "$650/week")
    location: str                    # 房产位置
    
    # 房产特征
    bedrooms: Optional[int]          # 卧室数量
    bathrooms: Optional[int]         # 浴室数量
    parking: Optional[int]           # 停车位数量
    property_type: str               # 房产类型 (Apartment/House/Studio等)
    
    # 详细描述
    description: str                 # 房产描述
    features: List[str]              # 房产特色列表
    images: List[str]                # 图片URL列表
    
    # 中介信息
    agent: Dict[str, Any]            # 中介联系信息
    
    # 地理位置
    coordinates: Optional[Dict[str, float]]  # 经纬度坐标
    
    # 数据源信息
    url: str                         # 房产链接
    source: str                      # 数据来源
    scraped_at: str                  # 抓取时间
    
    # 租赁信息
    available_from: Optional[str]    # 可入住时间
    property_size: Optional[str]     # 房产面积
    land_size: Optional[str]         # 土地面积
    year_built: Optional[int]        # 建造年份
    energy_rating: Optional[str]     # 能效等级
    pet_friendly: Optional[bool]     # 是否允许宠物
    furnished: Optional[bool]        # 是否有家具
    inspection_times: List[Dict[str, str]]  # 看房时间
```

**JSON示例**:
```json
{
  "id": "3afcb9c5-0396-4547-84e2-965bb94aa6cd",
  "title": "Modern 2 Bedroom Apartment in Camperdown",
  "price": "$650/week",
  "location": "Camperdown",
  "bedrooms": 2,
  "bathrooms": 1,
  "parking": 1,
  "property_type": "Apartment",
  "description": "Well-appointed modern apartment with excellent amenities",
  "features": [
    "Air Conditioning",
    "Built-in Wardrobes",
    "Balcony"
  ],
  "images": [
    "https://example.com/image1.jpg"
  ],
  "agent": {
    "name": "Property Agent",
    "phone": "0400 000 000",
    "email": "agent@realestate.com"
  },
  "coordinates": {
    "lat": -33.8688,
    "lng": 151.2093
  },
  "url": "https://www.domain.com.au/property/sample",
  "source": "Domain.com.au",
  "scraped_at": "2024-09-10T17:30:00Z",
  "available_from": "Available Now",
  "property_size": "75 sqm",
  "land_size": null,
  "year_built": null,
  "energy_rating": null,
  "pet_friendly": false,
  "furnished": false,
  "inspection_times": []
}
```

### 3. 搜索元数据 (SearchMetadata)

```python
class SearchMetadata(BaseModel):
    total_found: int                 # 找到的房产总数
    search_time_ms: float            # 搜索耗时 (毫秒)
    firecrawl_usage: Dict[str, Any]  # Firecrawl API使用信息
    search_params: Dict[str, Any]    # 搜索参数
    timestamp: str                   # 搜索时间戳
```

### 4. 搜索响应 (PropertySearchResponse)

```python
class PropertySearchResponse(BaseModel):
    success: bool                    # 搜索是否成功
    properties: List[PropertyModel]  # 房产数据列表
    metadata: SearchMetadata         # 搜索元数据
    message: str                     # 响应消息
```

**完整响应示例**:
```json
{
  "success": true,
  "properties": [
    {
      "id": "uuid-123",
      "title": "Modern Apartment",
      "price": "$650/week",
      "location": "Camperdown",
      // ... 其他房产字段
    }
  ],
  "metadata": {
    "total_found": 1,
    "search_time_ms": 1250.0,
    "firecrawl_usage": {},
    "search_params": {
      "location": "Camperdown",
      "min_price": 500,
      "max_price": 800
    },
    "timestamp": "2024-09-10T17:30:00Z"
  },
  "message": "成功找到 1 个房产"
}
```

## 🗄️ 数据库模型

### 1. 房产表 (properties)

```sql
CREATE TABLE properties (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    price VARCHAR(100) NOT NULL,
    price_numeric INTEGER,           -- 便于价格筛选
    location VARCHAR(200) NOT NULL,
    suburb VARCHAR(100),
    state VARCHAR(10),
    postcode VARCHAR(10),
    
    -- 房产特征
    bedrooms INTEGER,
    bathrooms INTEGER,
    parking INTEGER,
    property_type VARCHAR(50) NOT NULL,
    property_size VARCHAR(50),
    land_size VARCHAR(50),
    year_built INTEGER,
    
    -- 描述和特色
    description TEXT NOT NULL,
    features JSON,                   -- 房产特色数组
    
    -- 图片和媒体
    images JSON,                     -- 图片URL数组
    virtual_tour_url VARCHAR(500),
    
    -- 地理位置
    latitude FLOAT,
    longitude FLOAT,
    
    -- 出租信息
    available_from VARCHAR(100),
    lease_term VARCHAR(100),
    bond_amount VARCHAR(100),
    pet_friendly BOOLEAN,
    furnished BOOLEAN,
    utilities_included VARCHAR(200),
    
    -- 能效和评级
    energy_rating VARCHAR(10),
    
    -- 中介信息
    agent_info JSON,                 -- 中介信息对象
    agency_name VARCHAR(200),
    
    -- 看房时间
    inspection_times JSON,           -- 看房时间数组
    
    -- 数据来源
    url VARCHAR(1000) UNIQUE NOT NULL,
    source VARCHAR(100) NOT NULL,
    source_id VARCHAR(100),
    scraped_at VARCHAR(30) NOT NULL,
    
    -- 数据质量
    data_quality_score FLOAT,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 2. 搜索历史表 (search_history)

```sql
CREATE TABLE search_history (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(100),
    user_ip VARCHAR(50),
    user_agent TEXT,
    
    -- 搜索参数
    location VARCHAR(200) NOT NULL,
    min_price INTEGER,
    max_price INTEGER,
    property_type VARCHAR(50),
    bedrooms INTEGER,
    bathrooms INTEGER,
    parking INTEGER,
    max_results INTEGER DEFAULT 50,
    
    -- 搜索结果统计
    results_found INTEGER DEFAULT 0,
    search_time_ms FLOAT NOT NULL,
    firecrawl_usage JSON,
    
    -- 搜索状态
    search_status VARCHAR(20) NOT NULL, -- success, error, timeout
    error_message TEXT,
    
    -- 用户交互
    csv_exported VARCHAR(5) DEFAULT 'false',
    results_clicked INTEGER DEFAULT 0,
    
    -- 完整搜索参数
    search_params JSON NOT NULL,
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 📄 CSV导出格式

自动生成的CSV文件包含以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| ID | string | 房产唯一标识 |
| Title | string | 房产标题 |
| Price | string | 租金价格 |
| Location | string | 房产位置 |
| Bedrooms | number | 卧室数量 |
| Bathrooms | number | 浴室数量 |
| Parking | number | 停车位数量 |
| Property_Type | string | 房产类型 |
| Description | string | 房产描述 (截取200字符) |
| Features | string | 房产特色 (逗号分隔) |
| Agent_Name | string | 中介姓名 |
| Agent_Phone | string | 中介电话 |
| Available_From | string | 可入住时间 |
| Property_Size | string | 房产面积 |
| Pet_Friendly | string | 是否允许宠物 (Yes/No) |
| Furnished | string | 是否有家具 (Yes/No) |
| URL | string | 房产链接 |
| Source | string | 数据来源 |
| Scraped_At | string | 抓取时间 |
| Search_Location | string | 搜索位置 |
| Search_Min_Price | number | 搜索最低价 |
| Search_Max_Price | number | 搜索最高价 |

## 🔄 与TypeScript版本的主要差异

### 1. **编程语言和框架**
- **之前**: TypeScript + Node.js + Express
- **现在**: Python + FastAPI + Pydantic

### 2. **数据验证**
- **之前**: 手动验证或使用第三方库
- **现在**: Pydantic自动类型验证和转换

### 3. **响应格式**
- **核心结构保持一致**，但有以下改进：
  - 更严格的类型定义
  - 自动API文档生成
  - 更好的错误处理

### 4. **新增功能**
- **后台任务**: FastAPI的BackgroundTasks用于CSV导出
- **更丰富的元数据**: 包含Firecrawl使用统计
- **改进的日志系统**: 专用的API、抓取、CSV日志

### 5. **数据库模型增强**
- 更多索引优化
- JSON字段用于复杂数据
- 改进的数据质量跟踪

## 🚀 API端点

### 主要端点
- `POST /api/v1/properties/search` - 房产搜索
- `GET /api/v1/properties/locations` - 支持的区域
- `GET /api/v1/properties/test` - 测试Firecrawl连接
- `GET /api/v1/health/` - 健康检查

### 文档地址
- **Swagger UI**: `http://localhost:3000/api/v1/docs`
- **ReDoc**: `http://localhost:3000/api/v1/redoc`

## 📝 使用示例

### Python代码示例
```python
import httpx
import asyncio

async def search_properties():
    search_request = {
        "location": "Camperdown",
        "min_price": 500,
        "max_price": 800,
        "bedrooms": 2,
        "property_type": "Apartment"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:3000/api/v1/properties/search",
            json=search_request
        )
        
        data = response.json()
        print(f"找到 {data['metadata']['total_found']} 个房产")
        
        for prop in data['properties']:
            print(f"- {prop['title']}: {prop['price']}")

asyncio.run(search_properties())
```

### cURL示例
```bash
curl -X POST http://localhost:3000/api/v1/properties/search \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Camperdown",
    "min_price": 500,
    "max_price": 800,
    "bedrooms": 2,
    "property_type": "Apartment"
  }'
```

---

**🎯 总结**: Python FastAPI版本保持了与TypeScript版本的数据结构兼容性，同时提供了更强的类型安全、自动验证和更丰富的功能。