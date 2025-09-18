# 🚀 澳洲房产智能推荐系统 - 运行指南

## 📋 系统概览

本系统集成了您的解析算法和推荐算法，提供：
- 🤖 **智能解析**: 使用OpenAI GPT-4o-mini解析自然语言查询
- 🎯 **智能推荐**: 基于多维权重算法的房产推荐
- 🔍 **数据抓取**: Firecrawl集成的Domain.com.au数据抓取
- 💻 **Web界面**: 用户友好的前端界面

## 🛠️ 环境准备

### 1. 系统要求
- Python 3.9+
- 网络连接 (用于API调用)
- 最低配置即可运行 (无需GPU)

### 2. 依赖安装
```bash
cd sydney-property-ai-Arthur

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖 (更轻量，无需torch等重型ML库)
pip install -r requirements.txt
```

### 3. API密钥获取

#### 3.1 获取OpenAI API密钥
1. 访问 [OpenAI平台](https://platform.openai.com/api-keys)
2. 登录或注册账户
3. 创建新的API密钥
4. **重要**: OpenAI API按使用量收费，gpt-4o-mini很便宜 (~$0.15/1M tokens)

#### 3.2 获取Firecrawl API密钥  
1. 访问 [Firecrawl](https://firecrawl.dev)
2. 注册账户
3. 获取API密钥

### 4. 环境配置
```bash
# 复制环境配置模板
cp .env.example .env

# 编辑 .env 文件
nano .env
```

**必需配置**:
```env
# OpenAI API配置 (必需)
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=500
OPENAI_TEMPERATURE=0.1

# Firecrawl API配置 (必需)  
FIRECRAWL_API_KEY=fc-your-firecrawl-api-key-here
FIRECRAWL_BASE_URL=https://api.firecrawl.dev

# 基本配置
PORT=3000
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here

# 其他配置 (可选)
DATABASE_URL=sqlite:///./properties.db
```

## 🚀 启动系统

### 方式1: 直接运行 (推荐开发)
```bash
# 启动后端API服务
python -m app.main

# 或使用uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

### 方式2: Docker运行
```bash
# 启动完整服务栈
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

## 🌐 访问系统

### 后端API文档
- **Swagger UI**: http://localhost:3000/api/v1/docs
- **ReDoc**: http://localhost:3000/api/v1/redoc
- **健康检查**: http://localhost:3000/health

### 前端界面
在浏览器中打开: `frontend/index.html`

或使用简单HTTP服务器:
```bash
cd frontend
python -m http.server 8080
# 然后访问 http://localhost:8080
```

## 🧪 API测试

### 1. 健康检查
```bash
curl http://localhost:3000/health
```

### 2. 智能推荐搜索 (新功能)
```bash
curl -X POST "http://localhost:3000/api/v1/properties/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Looking for a 2 bedroom apartment in Camperdown, budget $800 per week, must have parking",
    "max_results": 5
  }'
```

**支持中英文混合查询**:
```bash
curl -X POST "http://localhost:3000/api/v1/properties/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "我想在悉尼找一个2室公寓，预算每周$900，需要停车位",
    "max_results": 5
  }'
```

### 3. 普通搜索
```bash
curl -X POST "http://localhost:3000/api/v1/properties/search" \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Camperdown",
    "min_price": 600,
    "max_price": 900,
    "bedrooms": 2,
    "max_results": 10
  }'
```

## 📊 功能说明

### 智能推荐流程
1. **自然语言解析**: OpenAI GPT-4o-mini解析用户查询
2. **参数提取**: 提取位置、价格、房型等信息  
3. **数据抓取**: Firecrawl抓取Domain.com.au数据
4. **数据解析**: OpenAI解析房产信息
5. **智能推荐**: 多维算法评分排序
6. **结果返回**: 返回最匹配的房产

### 推荐算法权重
- **用户价格偏好**: 34%
- **区域匹配**: 22% 
- **卧室数量**: 14%
- **卫浴数量**: 8%
- **房产类型**: 6%
- **区域价格合理性**: 8%
- **停车位**: 5%
- **特色功能**: 2%
- **数据新鲜度**: 1%

## 🐛 故障排除

### 常见问题

#### 1. OpenAI API错误
```bash
# 测试API连接
curl -X POST "https://api.openai.com/v1/chat/completions" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 5}'

# 检查API余额 (登录OpenAI平台查看)
# 访问 https://platform.openai.com/usage
```

**常见OpenAI错误**:
- `401 Unauthorized`: API密钥错误或无效
- `429 Rate limit exceeded`: 请求频率过高，稍后重试  
- `402 Payment required`: 账户余额不足
- `400 Bad request`: 请求格式错误

#### 2. Firecrawl API错误
```bash
# 测试API连接
curl -H "Authorization: Bearer your_api_key" https://api.firecrawl.dev/health

# 检查API余额
# 访问 https://firecrawl.dev 查看账户状态
```

#### 3. 端口被占用
```bash
# 查找占用端口的进程
lsof -i :3000

# 杀死进程
kill -9 <PID>

# 或使用不同端口
uvicorn app.main:app --port 3001
```

## 📝 开发模式

### 修改OpenAI配置
编辑 `.env` 文件或环境变量:
```env
# 使用不同的OpenAI模型
OPENAI_MODEL=gpt-4o-mini      # 最便宜，推荐
OPENAI_MODEL=gpt-4o           # 更强大，但更贵  
OPENAI_MODEL=gpt-3.5-turbo    # 经典选择

# 调整输出长度和创意度
OPENAI_MAX_TOKENS=800         # 更长的输出
OPENAI_TEMPERATURE=0.3        # 更有创意的解析
```

### 调整推荐权重
编辑 `app/services/recommendation_service.py`:
```python
self.weights = {
    "priceU": 0.40,    # 增加价格权重
    "area": 0.25,      # 增加区域权重
    # ... 其他权重
}
```

### 测试模式 (跳过API调用)
如果要快速测试不使用API，可以暂时清空API密钥:
```bash
export OPENAI_API_KEY=""
export FIRECRAWL_API_KEY=""
```
系统会自动回退到规则解析和示例数据。

## 📈 性能监控

### 查看日志
```bash
# 应用日志
tail -f logs/app.log

# 抓取日志
tail -f logs/scraping.log

# CSV导出日志
tail -f logs/csv_export.log
```

### 监控指标
- **响应时间**: 在API响应中的 `search_time_ms`
- **成功率**: 检查 `success` 字段
- **数据质量**: 检查返回的房产数量

## 🔧 扩展功能

### 添加新的数据源
1. 创建新的抓取服务类
2. 在 `FirecrawlService` 中添加新的URL构建逻辑
3. 更新解析逻辑以处理新格式

### 自定义推荐算法
1. 修改 `PropertyRecommendationService` 
2. 调整权重配置
3. 添加新的评分维度

### 数据持久化
1. 配置PostgreSQL数据库
2. 启用数据库存储功能
3. 实现搜索历史记录

---

## ✅ 快速启动清单

- [ ] 安装Python 3.9+和依赖 (`pip install -r requirements.txt`)
- [ ] 获取OpenAI API密钥 (https://platform.openai.com/api-keys)
- [ ] 获取Firecrawl API密钥 (https://firecrawl.dev)
- [ ] 配置 `.env` 文件 (复制 `.env.example`)
- [ ] 启动后端服务 (`python -m app.main`)
- [ ] 打开前端界面 (`frontend/index.html`)
- [ ] 测试智能推荐功能

**💡 成本估算**: 
- OpenAI API: ~$0.01-0.05 每次查询 (gpt-4o-mini)
- Firecrawl API: 按抓取页面计费

**🎉 现在您可以开始使用澳洲房产智能推荐系统了！**