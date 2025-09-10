# API使用指南 - Python FastAPI版本

**澳洲租房聚合系统** - 完整的API接口使用指南

## 🚀 快速开始

### 启动服务
```bash
# 方式1: Docker (推荐)
docker-compose up -d

# 方式2: 本地开发
source venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

### 访问API文档
- **Swagger UI**: http://localhost:3000/api/v1/docs
- **ReDoc**: http://localhost:3000/api/v1/redoc
- **基础信息**: http://localhost:3000/

## 📋 API端点总览

| 端点 | 方法 | 描述 | 认证 |
|------|------|------|------|
| `/` | GET | 基础信息 | 否 |
| `/health` | GET | 简单健康检查 | 否 |
| `/api/v1/health/` | GET | 详细健康检查 | 否 |
| `/api/v1/health/ready` | GET | 就绪检查 | 否 |
| `/api/v1/health/live` | GET | 存活检查 | 否 |
| `/api/v1/properties/search` | POST | 房产搜索 | 否 |
| `/api/v1/properties/locations` | GET | 支持的区域 | 否 |
| `/api/v1/properties/test` | GET | 测试Firecrawl | 否 |

## 🏠 房产搜索API详解

### 端点信息
- **URL**: `POST /api/v1/properties/search`
- **Content-Type**: `application/json`
- **响应**: JSON格式房产数据
- **副作用**: 自动生成CSV文件

### 请求参数

#### 必需参数
- `location` (string): 搜索区域，如 "Camperdown", "Sydney"

#### 可选参数
- `min_price` (integer): 最低价格 (周租)，范围: ≥0
- `max_price` (integer): 最高价格 (周租)，范围: ≥min_price
- `bedrooms` (integer): 卧室数量，范围: ≥0
- `bathrooms` (integer): 浴室数量，范围: ≥0
- `parking` (integer): 停车位数量，范围: ≥0
- `property_type` (string): 房产类型，如 "Apartment", "House", "Studio"
- `max_results` (integer): 最大结果数量，范围: 1-200，默认: 50

### 请求示例

#### 基础搜索
```bash
curl -X POST http://localhost:3000/api/v1/properties/search \
  -H "Content-Type: application/json" \
  -d '{"location": "Camperdown"}'
```

#### 完整参数搜索
```bash
curl -X POST http://localhost:3000/api/v1/properties/search \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Camperdown",
    "min_price": 500,
    "max_price": 800,
    "bedrooms": 2,
    "bathrooms": 1,
    "parking": 1,
    "property_type": "Apartment",
    "max_results": 20
  }'
```

#### Python示例
```python
import httpx
import asyncio
import json

async def search_properties():
    request_data = {
        "location": "Camperdown",
        "min_price": 500,
        "max_price": 800,
        "bedrooms": 2,
        "property_type": "Apartment"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:3000/api/v1/properties/search",
            json=request_data,
            timeout=60  # 60秒超时
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功: {data['success']}")
            print(f"🏠 找到: {data['metadata']['total_found']} 个房产")
            print(f"⚡ 时间: {data['metadata']['search_time_ms']} ms")
            
            for i, prop in enumerate(data['properties'][:3]):
                print(f"\n📍 房产 {i+1}:")
                print(f"   标题: {prop['title']}")
                print(f"   价格: {prop['price']}")
                print(f"   房间: {prop['bedrooms']}室{prop['bathrooms']}浴")
                print(f"   链接: {prop['url']}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)

# 运行搜索
asyncio.run(search_properties())
```

### 响应格式

#### 成功响应 (200)
```json
{
  "success": true,
  "properties": [
    {
      "id": "uuid-123",
      "title": "Modern 2 Bedroom Apartment in Camperdown",
      "price": "$650/week",
      "location": "Camperdown",
      "bedrooms": 2,
      "bathrooms": 1,
      "parking": 1,
      "property_type": "Apartment",
      "description": "Well-appointed modern apartment...",
      "features": ["Air Conditioning", "Built-in Wardrobes"],
      "images": ["https://example.com/image1.jpg"],
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
      "pet_friendly": false,
      "furnished": false,
      "inspection_times": []
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

#### 错误响应 (4xx/5xx)
```json
{
  "success": false,
  "properties": [],
  "metadata": {
    "total_found": 0,
    "search_time_ms": 100.0,
    "firecrawl_usage": {},
    "search_params": {},
    "timestamp": "2024-09-10T17:30:00Z"
  },
  "message": "搜索失败: 错误描述"
}
```

## 🔍 健康检查API

### 详细健康检查
```bash
curl http://localhost:3000/api/v1/health/
```

**响应**:
```json
{
  "status": "healthy",
  "timestamp": "2024-09-10T17:30:00Z",
  "version": "2.0.0-python",
  "environment": "development",
  "services": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12.5
    },
    "redis": {
      "status": "healthy", 
      "response_time_ms": 8.2
    },
    "firecrawl": {
      "status": "healthy",
      "response_time_ms": 150.0
    }
  }
}
```

### 就绪检查 (Kubernetes)
```bash
curl http://localhost:3000/api/v1/health/ready
```

### 存活检查 (Kubernetes)
```bash
curl http://localhost:3000/api/v1/health/live
```

## 📍 支持的区域API

### 获取支持的搜索区域
```bash
curl http://localhost:3000/api/v1/properties/locations
```

**响应**:
```json
{
  "success": true,
  "locations": [
    {
      "name": "Sydney",
      "state": "NSW",
      "popular_suburbs": ["Camperdown", "Newtown", "Surry Hills"]
    },
    {
      "name": "Melbourne", 
      "state": "VIC",
      "popular_suburbs": ["Carlton", "Fitzroy", "South Yarra"]
    }
  ],
  "message": "支持的搜索区域列表"
}
```

## 🧪 Firecrawl测试API

### 测试API连接状态
```bash
curl http://localhost:3000/api/v1/properties/test
```

**成功响应**:
```json
{
  "success": true,
  "status_code": 200,
  "message": "Firecrawl API连接正常",
  "api_url": "https://api.firecrawl.dev"
}
```

**失败响应**:
```json
{
  "success": false,
  "error": "Connection timeout",
  "message": "Firecrawl API连接失败",
  "api_url": "https://api.firecrawl.dev"
}
```

## 📄 CSV自动导出

### 导出触发
每次成功的房产搜索都会自动在后台生成CSV文件，无需额外操作。

### 文件位置
- **开发环境**: `./csv_exports/`
- **Docker环境**: 映射到主机 `./csv_exports/`

### 文件命名
```
property_search_[地区]_[时间戳].csv
```
**示例**: `property_search_Camperdown_20240910_173045.csv`

### CSV字段
包含22个字段：ID, Title, Price, Location, Bedrooms, Bathrooms, Parking, Property_Type, Description, Features, Agent_Name, Agent_Phone, Available_From, Property_Size, Pet_Friendly, Furnished, URL, Source, Scraped_At, Search_Location, Search_Min_Price, Search_Max_Price

## ⚡ 性能考虑

### 超时设置
- **API响应**: 默认60秒超时
- **Firecrawl抓取**: 30秒超时
- **数据库查询**: 10秒超时

### 限流规则
- **每分钟**: 100次请求
- **突发**: 最多10次连续请求

### 缓存策略
- **搜索结果**: 5分钟缓存
- **通用数据**: 1小时缓存

## 🚨 错误处理

### 常见错误代码

#### 400 - 请求参数错误
```json
{
  "detail": [
    {
      "loc": ["body", "max_price"],
      "msg": "最高价格不能小于最低价格",
      "type": "value_error"
    }
  ]
}
```

#### 402 - API配额不足
```json
{
  "detail": "Firecrawl API配额不足，请检查账户余额"
}
```

#### 500 - 服务器内部错误
```json
{
  "success": false,
  "message": "抓取过程出错: Connection timeout",
  "properties": [],
  "metadata": {...}
}
```

### 重试机制
- **自动重试**: 网络错误最多3次
- **退避策略**: 指数退避，最大延迟30秒
- **熔断器**: 连续失败5次后暂停1分钟

## 🛠️ 开发和调试

### 本地开发
```bash
# 启动开发服务器
source venv/bin/activate  
uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

### 查看日志
```bash
# 应用日志
tail -f logs/app.log

# API请求日志
tail -f logs/api.log

# 抓取日志
tail -f logs/scraping.log

# CSV导出日志
tail -f logs/csv_export.log
```

### 调试技巧
1. **检查健康状态**: `GET /api/v1/health/`
2. **测试Firecrawl**: `GET /api/v1/properties/test`  
3. **查看CSV文件**: 检查 `csv_exports/` 目录
4. **验证数据**: 使用少量max_results测试

## 📊 监控和指标

### 关键指标
- **响应时间**: 平均搜索时间 < 5秒
- **成功率**: > 95%
- **可用性**: > 99.9%
- **Firecrawl配额**: 实时监控

### 健康检查端点
- `/health`: 简单检查
- `/api/v1/health/`: 详细检查
- `/api/v1/health/ready`: Kubernetes就绪探针
- `/api/v1/health/live`: Kubernetes存活探针

---

**📞 技术支持**: 如需帮助，请查看日志文件或通过GitHub Issues反馈问题。