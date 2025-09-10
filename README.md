# 澳洲租房聚合网站后端系统

一个用于聚合澳洲租房市场数据的企业级后端API服务，支持实时抓取Domain.com.au等房产网站数据，为用户提供智能房产搜索和AI报告生成服务。

## 🏗️ 系统架构

### 核心组件
- **Express.js API服务器** - RESTful API接口
- **Firecrawl集成** - 智能网页抓取服务
- **Redis缓存层** - 高性能数据缓存
- **PostgreSQL数据库** - 可靠的数据持久化
- **Bull队列系统** - 异步任务处理
- **TypeScript** - 类型安全的代码

### 技术栈
- **后端框架**: Node.js + Express.js + TypeScript
- **数据库**: PostgreSQL 15 + Redis 7
- **队列处理**: Bull Queue (Redis-based)
- **网页抓取**: Firecrawl API
- **容器化**: Docker + Docker Compose
- **测试框架**: Jest + Supertest
- **代码质量**: ESLint + TypeScript

## 🚀 快速开始

### 环境要求
- Node.js 18+
- Docker & Docker Compose
- Firecrawl API Key

### 1. 克隆项目
```bash
git clone <repository-url>
cd rental-aggregator-backend
```

### 2. 环境配置
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env
```

必填配置项：
```env
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
```

### 3. 启动开发环境
```bash
# 启动所有服务 (数据库、缓存、应用)
docker-compose up -d

# 或仅启动依赖服务
docker-compose up -d postgres redis

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 启动管理工具 (可选)
```bash
# 启动 Redis GUI 和 PostgreSQL GUI
docker-compose --profile tools up -d

# 访问地址：
# Redis Commander: http://localhost:8081
# pgAdmin: http://localhost:8080 (admin@rental-aggregator.com / admin123)
```

## 📚 API 文档

### 基础信息
- **Base URL**: `http://localhost:3000`
- **Content-Type**: `application/json`
- **Rate Limit**: 100 requests per 15 minutes (default)

### 核心端点

#### 1. 房产搜索
```bash
POST /api/properties/search
```

请求示例：
```json
{
  "listingType": "rent",
  "location": {
    "suburb": "Camperdown",
    "state": "NSW",
    "postcode": "2050"
  },
  "propertyType": "apartment",
  "bedrooms": {
    "min": 2,
    "max": 3
  },
  "priceRange": {
    "min": 400,
    "max": 800
  },
  "sortBy": "price-asc",
  "page": 1,
  "limit": 20
}
```

响应示例：
```json
{
  "success": true,
  "data": {
    "properties": [
      {
        "id": "property-123",
        "source": "domain",
        "address": {
          "street": "123 Test Street",
          "suburb": "Camperdown",
          "state": "NSW",
          "postcode": "2050",
          "fullAddress": "123 Test Street, Camperdown NSW 2050"
        },
        "price": {
          "display": "$450 per week",
          "amount": 450,
          "frequency": "weekly",
          "currency": "AUD"
        },
        "propertyDetails": {
          "type": "apartment",
          "bedrooms": 2,
          "bathrooms": 1,
          "parking": 1
        },
        "media": {
          "images": ["https://example.com/image1.jpg"]
        },
        "description": "Modern apartment with city views...",
        "features": ["Air conditioning", "Balcony", "Pool"],
        "contact": {
          "agentName": "John Smith",
          "agencyName": "Premium Real Estate"
        },
        "metadata": {
          "listingDate": "2024-01-15T10:00:00Z",
          "lastUpdated": "2024-01-15T14:30:00Z",
          "sourceUrl": "https://domain.com.au/property-123"
        }
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 5,
      "totalProperties": 89,
      "hasNext": true,
      "hasPrevious": false
    },
    "metadata": {
      "searchId": "search_1642234567_abc123",
      "executionTime": 1250,
      "sourcesScrapped": ["domain", "cache"],
      "cacheHit": false
    }
  }
}
```

#### 2. 获取单个房产
```bash
GET /api/properties/:id?source=domain
```

#### 3. 地区建议
```bash
GET /api/locations/suggest?query=camper&limit=10
```

#### 4. 健康检查
```bash
GET /health
GET /health/detailed
GET /health/ready
GET /health/live
```

#### 5. 管理员端点
```bash
GET /api/admin/analytics/search?days=7
GET /api/admin/queue/status
POST /api/admin/cache/invalidate
```

## 🧪 测试

```bash
# 运行所有测试
npm test

# 运行测试并生成覆盖率报告
npm run test:coverage

# 运行测试监视模式
npm run test:watch

# 运行特定测试文件
npm test -- domainUrlBuilder.test.ts
```

测试覆盖率目标: >80%

## 🛠️ 开发工具

### 代码质量
```bash
# 代码检查
npm run lint

# 自动修复代码风格问题
npm run lint:fix

# TypeScript 类型检查
npm run build
```

### 数据库管理
```bash
# 运行数据库迁移
npm run db:migrate

# 查看数据库状态
docker-compose exec postgres psql -U postgres -d rental_aggregator
```

### 缓存管理
```bash
# 连接到 Redis CLI
docker-compose exec redis redis-cli -a redis123

# 查看缓存统计
redis-cli -a redis123 info memory
```

## 📊 监控和日志

### 日志级别
- **error**: 系统错误和异常
- **warn**: 警告和潜在问题
- **info**: 一般信息和重要事件
- **debug**: 调试信息（仅开发环境）

### 日志文件位置
```
logs/
├── error.log      # 错误日志
├── combined.log   # 综合日志
└── app.log        # 应用日志
```

### 监控端点
- `/health` - 基础健康检查
- `/health/detailed` - 详细系统状态
- `/api/properties/health` - 服务健康状态
- `/api/admin/queue/status` - 队列状态

## 🔧 配置说明

### 环境变量

#### 应用配置
```env
NODE_ENV=development
PORT=3000
APP_NAME=Rental Aggregator Backend
```

#### 数据库配置
```env
DATABASE_URL=postgresql://postgres:password123@localhost:5432/rental_aggregator
DB_HOST=localhost
DB_PORT=5432
DB_NAME=rental_aggregator
```

#### Redis配置
```env
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
```

#### Firecrawl配置
```env
FIRECRAWL_API_KEY=your_api_key_here
FIRECRAWL_BASE_URL=https://api.firecrawl.dev
```

#### 性能配置
```env
RATE_LIMIT_WINDOW_MS=900000    # 15分钟
RATE_LIMIT_MAX_REQUESTS=100
CACHE_TTL_SECONDS=900          # 15分钟
QUEUE_CONCURRENCY=5
MAX_CONCURRENT_REQUESTS=3
SCRAPING_DELAY_MS=1000
```

## 🚢 部署

### Docker生产部署
```bash
# 构建生产镜像
docker build --target production -t rental-aggregator:latest .

# 运行生产容器
docker run -d \
  --name rental-aggregator \
  -p 3000:3000 \
  --env-file .env.production \
  rental-aggregator:latest
```

### Docker Compose生产部署
```bash
# 使用生产配置
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 环境变量清单（生产）
确保生产环境包含所有必需的环境变量：
- ✅ `FIRECRAWL_API_KEY`
- ✅ `DATABASE_URL`
- ✅ `REDIS_URL`
- ✅ `NODE_ENV=production`

## 🔒 安全考虑

### API安全
- ✅ Helmet.js 安全头
- ✅ CORS 跨域保护
- ✅ 请求速率限制
- ✅ 输入数据验证
- ✅ SQL注入防护

### 数据安全
- ✅ 敏感数据不记录日志
- ✅ 数据库连接加密 (生产环境SSL)
- ✅ API密钥环境变量管理
- ✅ 容器非root用户运行

## 📈 性能优化

### 缓存策略
- **搜索结果**: 15分钟TTL
- **单个房产**: 30分钟TTL
- **地区建议**: 1小时TTL

### 数据库优化
- 地理位置GIN索引
- 价格和卧室BTREE索引
- 自动更新时间戳触发器
- 定期ANALYZE统计信息

### 队列优化
- 并发处理控制
- 指数退避重试机制
- 优先级队列管理
- 失败任务清理

## 🐛 故障排除

### 常见问题

#### 1. Firecrawl API错误
```bash
# 检查API密钥配置
echo $FIRECRAWL_API_KEY

# 测试API连接
curl -H "Authorization: Bearer $FIRECRAWL_API_KEY" https://api.firecrawl.dev/v0/scrape
```

#### 2. 数据库连接问题
```bash
# 检查数据库状态
docker-compose exec postgres pg_isready

# 查看数据库日志
docker-compose logs postgres
```

#### 3. Redis连接问题
```bash
# 测试Redis连接
docker-compose exec redis redis-cli ping

# 查看Redis日志
docker-compose logs redis
```

#### 4. 队列处理问题
```bash
# 查看队列状态
curl http://localhost:3000/api/admin/queue/status

# 查看应用日志
docker-compose logs app
```

### 调试技巧

#### 启用详细日志
```env
LOG_LEVEL=debug
```

#### 监控资源使用
```bash
# Docker容器资源使用
docker stats

# 应用健康状态
curl http://localhost:3000/health/detailed
```

## 🤝 开发贡献

### 开发流程
1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范
- 使用 TypeScript 严格模式
- 遵循 ESLint 配置规则
- 编写单元测试（覆盖率 >80%）
- 添加JSDoc注释
- 使用语义化版本控制

### 提交信息规范
```
type(scope): description

类型：
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式调整
- refactor: 代码重构
- test: 添加测试
- chore: 构建过程或工具变动
```

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🆘 支持

如遇问题，请通过以下方式获取支持：
- 📧 Email: support@rental-aggregator.com
- 🐛 Issues: GitHub Issues
- 📖 文档: [项目文档](docs/)

---

**注意**: 本项目仅用于教育和演示目的。请确保遵守目标网站的robots.txt和使用条款。