# 澳洲租房聚合系统后端 - Python FastAPI 版本

🏠 **澳洲房产租赁数据聚合API** - 基于Python FastAPI构建的高性能房产数据抓取和聚合系统

## 🚀 技术栈迁移

**从 TypeScript/Node.js 迁移至 Python FastAPI**

### 新技术栈优势
- ✅ **Python** - 主流语言，学习曲线友好
- ✅ **FastAPI** - 现代高性能Web框架，自动API文档生成
- ✅ **Pydantic** - 强类型数据验证和序列化
- ✅ **SQLAlchemy 2.0** - 现代Python ORM，支持异步操作
- ✅ **asyncio/httpx** - 异步HTTP客户端，高并发性能
- ✅ **pandas** - 强大的数据处理和CSV导出功能

### 核心功能
- 🔍 **智能房产搜索** - 支持多条件筛选
- 🤖 **Firecrawl集成** - 专业网页抓取服务
- 📊 **CSV数据导出** - 自动生成调试用CSV文件
- 🗄️ **数据存储** - 支持PostgreSQL持久化或内存模式
- ⚡ **缓存支持** - 可选Redis高性能缓存
- 🐳 **灵活部署** - 支持Docker或本地直接运行
- 🔧 **优雅降级** - 服务可在缺少依赖时正常运行

## 📋 快速开始

### 环境要求

**基础要求**:
- Python 3.11.x (必需)
- Firecrawl API密钥 (必需 - 用于房产数据抓取)

**可选依赖** (服务会自动降级):
- Docker & Docker Compose (推荐 - 一键部署)
- PostgreSQL 15+ (可选 - 用于数据持久化，否则使用内存模式)
- Redis 7+ (可选 - 用于缓存优化)

### 1. 克隆项目
```bash
git clone https://github.com/ZeshiKing/sydney-property-ai-Arthur.git
cd sydney-property-ai-Arthur
```

### 2. 配置环境变量
```bash
# 复制环境配置模板
cp .env.example .env

# 编辑 .env 文件，设置必要的配置
nano .env
```

**重要配置项**:
```env
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
DB_PASSWORD=your_secure_password
REDIS_PASSWORD=your_redis_password
SECRET_KEY=your-very-secure-secret-key
```

### 3. Docker方式运行（推荐）
```bash
# 一键启动（自动构建 & 跟随日志，可选）
./scripts/docker-up.sh --build --logs

# 或手动执行
docker compose up -d
docker compose ps
docker compose logs -f app

# 开发者热更新（可选）
docker compose --profile dev up app-dev
```

### 4. 本地开发方式（Python虚拟环境）

> 推荐使用 Python 3.11，以避免 pandas 等依赖在 Windows 上需要手动编译。

#### Windows (PowerShell)
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py -3.11 -m uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

#### macOS / Linux
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3.11 -m uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

服务启动后：
- 后端 API 文档：`http://localhost:8000/api/v1/docs`
- 前端界面（后端托管）：`http://localhost:8000/app`
- 静态文件：`http://localhost:8000/frontend/index.html`

**Firecrawl 验证**（命令行示例）
```bash
curl -X POST http://localhost:8000/api/v1/properties/search   -H "Content-Type: application/json"   -d '{
    "location": "Camperdown",
    "min_price": 500,
    "max_price": 900,
    "bedrooms": 2,
    "property_type": "Apartment",
    "max_results": 5
  }'
  scripts/docker-up.ps1 --build --logs

Windows PowerShell:
  scripts\docker-up.ps1 --build --logs
```
> 若未配置 `FIRECRAWL_API_KEY`，服务会自动降级为示例数据模式以便快速体验；配置真实密钥后即可启用真实抓取。
>
> 同样，缺少 `OPENAI_API_KEY` 时系统会退回到规则解析，依然可以完成流程。

> ⚠️ 本项目的 `requirements.txt` 在非 Python 3.11 环境会刻意报错（使用 `py311-only` 哨兵依赖），请务必先安装/切换到 3.11 再执行 `pip install -r requirements.txt`。

## 📚 API文档

### 自动生成的文档
启动服务后访问：
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

### 核心API端点

#### 🏠 房产搜索
```http
POST /api/v1/properties/search
Content-Type: application/json

{
  "location": "Camperdown",
  "min_price": 400,
  "max_price": 800,
  "bedrooms": 2,
  "bathrooms": 1,
  "property_type": "Apartment",
  "max_results": 20
}
```

**响应示例**:
```json
{
  "success": true,
  "properties": [
    {
      "id": "uuid-here",
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
        "phone": "0400 000 000"
      },
      "url": "https://www.domain.com.au/property/sample",
      "source": "Domain.com.au",
      "scraped_at": "2024-01-01T00:00:00Z"
    }
  ],
  "metadata": {
    "total_found": 1,
    "search_time_ms": 2500.0,
    "timestamp": "2024-01-01T00:00:00Z"
  },
  "message": "成功找到 1 个房产"
}
```

#### 🔍 健康检查
```http
GET /api/v1/health/
```

#### 📊 支持的区域
```http
GET /api/v1/properties/locations
```

#### 🧪 测试Firecrawl连接
```http
GET /api/v1/properties/test
```

## 🗄️ 数据库设计

### 房产表 (Properties)
```sql
CREATE TABLE properties (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    price VARCHAR(100) NOT NULL,
    price_numeric INTEGER,  -- 便于价格筛选
    location VARCHAR(200) NOT NULL,
    bedrooms INTEGER,
    bathrooms INTEGER,
    parking INTEGER,
    property_type VARCHAR(50) NOT NULL,
    description TEXT,
    features JSON,
    images JSON,
    latitude FLOAT,
    longitude FLOAT,
    url VARCHAR(1000) UNIQUE NOT NULL,
    source VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 搜索历史表 (Search History)
```sql
CREATE TABLE search_history (
    id VARCHAR(36) PRIMARY KEY,
    location VARCHAR(200) NOT NULL,
    search_params JSON NOT NULL,
    results_found INTEGER DEFAULT 0,
    search_time_ms FLOAT NOT NULL,
    search_status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 📁 项目结构

```
rental-aggregator-backend/
├── app/                          # 主应用目录
│   ├── __init__.py
│   ├── main.py                   # FastAPI应用入口
│   ├── api/                      # API路由
│   │   ├── api_v1/
│   │   │   ├── api.py           # API路由聚合
│   │   │   └── endpoints/
│   │   │       ├── health.py    # 健康检查端点
│   │   │       └── properties.py # 房产搜索端点
│   ├── core/                     # 核心配置
│   │   ├── config.py            # 应用配置
│   │   └── logging.py           # 日志配置
│   ├── database/                 # 数据库层
│   │   └── base.py              # 数据库连接和基类
│   └── models/                   # 数据模型
│       ├── property.py          # 房产模型
│       └── search_history.py    # 搜索历史模型
├── csv_exports/                  # CSV导出目录
├── logs/                         # 日志文件
├── requirements.txt              # Python依赖
├── pyproject.toml               # 项目配置
├── docker-compose.yml           # Docker编排
├── Dockerfile                   # Docker镜像
└── .env.example                 # 环境变量模板
```

## 🔧 开发工具

### 代码格式化和检查
```bash
# 安装开发依赖
pip install -r requirements.txt

# 代码格式化
black app/

# 代码检查
ruff app/

# 类型检查
mypy app/
```

### 数据库迁移
```bash
# 手动创建数据库表（当前版本）
# 启动应用时会自动创建表

# 未来版本将集成Alembic进行版本化迁移
```

## 🐳 Docker部署

### 开发环境
```bash
# 启动开发环境（支持热重载）
docker-compose up -d

# 仅启动数据库服务
docker-compose up -d postgres redis
```

### 生产环境
```bash
# 构建生产镜像
docker build --target production -t rental-aggregator:latest .

# 使用环境变量文件
docker-compose --env-file .env.production up -d
```

### 常用Docker命令
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app

# 进入应用容器
docker-compose exec app bash

# 重启应用服务
docker-compose restart app

# 清理并重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📊 CSV数据导出

每次成功搜索后，系统会自动在后台生成CSV文件：

### CSV文件位置
- 开发环境: `./csv_exports/`
- Docker环境: 映射到主机的 `./csv_exports/`

### CSV文件格式
```csv
ID,Title,Price,Location,Bedrooms,Bathrooms,Parking,Property_Type,Description,Features,Agent_Name,Agent_Phone,Available_From,Property_Size,Pet_Friendly,Furnished,URL,Source,Scraped_At,Search_Location,Search_Min_Price,Search_Max_Price
```

### CSV管理
- 自动清理：保留最新50个文件
- 文件命名：`property_search_[location]_[timestamp].csv`
- 编码格式：UTF-8

## 🚨 故障排除

### 常见问题

#### 1. Firecrawl API错误
```bash
# 检查API密钥配置
curl -H "Authorization: Bearer your_api_key" https://api.firecrawl.dev/health

# 查看API使用量
# 访问 https://firecrawl.dev 查看账户余额
```

#### 2. 数据库连接失败
```bash
# 检查PostgreSQL服务
docker-compose ps postgres

# 查看数据库日志
docker-compose logs postgres

# 测试数据库连接
docker-compose exec postgres psql -U postgres -d rental_aggregator -c "SELECT version();"
```

#### 3. Redis连接问题
```bash
# 检查Redis服务
docker-compose ps redis

# 测试Redis连接
docker-compose exec redis redis-cli ping
```

#### 4. 应用启动失败
```bash
# 查看详细日志
docker-compose logs -f app

# 检查环境变量
docker-compose exec app env | grep -E "(DB_|REDIS_|FIRECRAWL_)"

# 重新构建镜像
docker-compose build --no-cache app
```

## 🔧 管理界面

### PostgreSQL管理 (pgAdmin)
```bash
# 启动pgAdmin（可选）
docker-compose --profile tools up -d pgadmin

# 访问 http://localhost:8080
# 邮箱: admin@rental-aggregator.com
# 密码: admin123
```

### Redis管理 (Redis Commander)
```bash
# 启动Redis Commander（可选）
docker-compose --profile tools up -d redis-commander

# 访问 http://localhost:8081
```

## 📈 性能优化

### 数据库优化
- 索引优化：价格、位置、房产类型等关键字段
- 连接池：配置合适的连接池大小
- 查询优化：使用SQLAlchemy的延迟加载

### 缓存策略
- Redis缓存：搜索结果缓存5分钟
- 应用缓存：Firecrawl响应缓存1小时
- 数据库查询缓存：相同查询条件缓存

### 并发处理
- 异步处理：全面使用asyncio和httpx
- 连接限制：控制并发请求数量
- 超时设置：合理设置网络超时时间

## 🔒 安全考虑

### API安全
- CORS配置：限制跨域请求来源
- 速率限制：防止API滥用
- 输入验证：Pydantic严格验证输入

### 数据安全
- 环境变量：敏感信息不硬编码
- 数据库安全：使用强密码和SSL连接
- 日志安全：不记录敏感信息

## 📞 技术支持

### 获取帮助
- 查看日志文件：`logs/app.log`
- API文档：http://localhost:8000/api/v1/docs
- 健康检查：http://localhost:8000/health

### 联系方式
- 项目地址：https://github.com/ZeshiKing/sydney-property-ai-Arthur
- 问题反馈：通过GitHub Issues

## 🚀 部署上线

### 生产环境清单
- [ ] 更新所有默认密码
- [ ] 配置SSL/TLS证书
- [ ] 设置反向代理（Nginx）
- [ ] 配置日志轮转
- [ ] 设置监控和告警
- [ ] 数据库定期备份
- [ ] 性能测试和调优

---

**🎉 恭喜！Python FastAPI版本已成功迁移完成。享受更简洁的Python开发体验！**
