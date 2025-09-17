# 开发环境使用指南

## 🚀 快速开始

### 方式一：使用自动化脚本（推荐）

#### Linux/Mac/WSL
```bash
# 给脚本执行权限（首次使用）
chmod +x dev-start.sh

# 启动开发环境
./dev-start.sh

# 或者直接选择模式
./dev-start.sh api      # 仅启动API服务
./dev-start.sh docker   # 启动Docker完整环境
./dev-start.sh test     # 运行API测试
```

#### Windows
```cmd
# 双击运行或命令行运行
dev-start.bat
```

### 方式二：手动启动

#### 1. 环境准备
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 FIRECRAWL_API_KEY
```

#### 2. 启动服务
```bash
# 方式1: 直接运行
python -m app.main

# 方式2: 使用uvicorn（推荐开发）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🛠️ 开发模式选择

### 1. 仅API服务模式（最轻量）
- **适用场景**: 纯API开发，前端调试
- **启动命令**: `./dev-start.sh api` 或 `uvicorn app.main:app --reload`
- **特点**:
  - ✅ 启动速度快
  - ✅ 内存占用少
  - ✅ 支持热重载
  - ⚠️ 无数据持久化（重启后数据丢失）

### 2. Docker完整环境（功能完整）
- **适用场景**: 完整开发测试，接近生产环境
- **启动命令**: `./dev-start.sh docker` 或 `docker-compose up -d`
- **包含服务**:
  - PostgreSQL 数据库 (端口 5432)
  - Redis 缓存 (端口 6379)
  - FastAPI 应用 (端口 8000)
- **特点**:
  - ✅ 数据持久化
  - ✅ 完整缓存功能
  - ✅ 接近生产环境
  - ⚠️ 需要Docker环境
  - ⚠️ 资源占用较多

### 3. 混合模式（推荐）
- **适用场景**: 本地开发 + 外部数据库
- **操作步骤**:
  1. 启动数据库: `./dev-start.sh db`
  2. 启动API: `./dev-start.sh api`
- **特点**:
  - ✅ 数据持久化
  - ✅ 热重载开发
  - ✅ 灵活调试

## 📊 服务访问地址

启动成功后，可以访问以下地址：

- **API基础地址**: http://localhost:8000
- **API文档 (Swagger)**: http://localhost:8000/api/v1/docs
- **API文档 (ReDoc)**: http://localhost:8000/api/v1/redoc
- **健康检查**: http://localhost:8000/health
- **详细状态**: http://localhost:8000/api/v1/health/

### 数据库管理工具（Docker模式）
- **pgAdmin**: http://localhost:8080
  - 邮箱: admin@rental-aggregator.com
  - 密码: admin123
- **Redis Commander**: http://localhost:8081

## 🧪 测试API功能

### 使用自动化测试脚本
```bash
# 运行完整测试套件
./dev-start.sh test

# 或者直接运行Python脚本
python test-api.py
```

### 手动测试示例

#### 1. 健康检查
```bash
curl http://localhost:8000/health
```

#### 2. 房产搜索
```bash
curl -X POST "http://localhost:8000/api/v1/properties/search" \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Sydney",
    "max_results": 5
  }'
```

#### 3. 支持区域查询
```bash
curl http://localhost:8000/api/v1/properties/locations
```

## 📁 项目结构

```
rental-aggregator-backend/
├── app/                     # 主应用代码
│   ├── main.py             # 应用入口
│   ├── api/                # API路由
│   ├── core/               # 核心配置
│   ├── database/           # 数据库层
│   └── models/             # 数据模型
├── csv_exports/            # CSV导出文件（自动生成）
├── logs/                   # 日志文件（自动生成）
├── venv/                   # 虚拟环境
├── dev-start.sh           # Linux/Mac启动脚本
├── dev-start.bat          # Windows启动脚本
├── test-api.py            # API测试脚本
├── requirements.txt       # Python依赖
├── docker-compose.yml     # Docker编排文件
├── .env.example           # 环境变量模板
└── README.md              # 项目文档
```

## ⚙️ 配置说明

### 环境变量配置 (.env)
```env
# 基础配置
PORT=8000                           # API端口
DEBUG=true                          # 调试模式
ENVIRONMENT=development             # 环境标识

# Firecrawl API (必需)
FIRECRAWL_API_KEY=fc-your-key      # 从 https://firecrawl.dev 获取

# 数据库 (可选 - Docker环境)
DB_HOST=localhost
DB_PASSWORD=your_password

# Redis (可选 - Docker环境)
REDIS_PASSWORD=your_redis_password
```

### 重要配置项说明
- **FIRECRAWL_API_KEY**: 必需配置，用于房产数据抓取
- **数据库配置**: 可选，不配置时使用内存模式
- **CORS设置**: 已配置支持多端口前端开发

## 🔧 开发工具

### 代码质量
```bash
# 代码格式化
black app/

# 代码检查
ruff app/

# 类型检查
mypy app/
```

### 日志查看
```bash
# 应用日志
tail -f logs/app.log

# API请求日志
tail -f logs/api.log

# 抓取日志
tail -f logs/scraping.log

# Docker日志（如果使用Docker）
docker-compose logs -f app
```

## 🚨 常见问题

### 1. 端口被占用
```bash
# 查看端口占用
netstat -tulpn | grep 8000
# 或者
lsof -i :8000

# 停止占用进程
kill -9 PID
```

### 2. 虚拟环境问题
```bash
# 重新创建虚拟环境
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Firecrawl API错误
- 检查API密钥是否正确设置
- 确认网络连接正常
- 查看API配额是否用完

### 4. Docker问题
```bash
# 重启Docker服务
docker-compose down
docker-compose up -d

# 查看容器状态
docker-compose ps

# 查看容器日志
docker-compose logs app
```

## 📈 性能优化

### 开发环境优化
- 使用内存模式可以提升开发速度
- 启用代码热重载便于实时调试
- 合理设置日志级别避免日志过多

### 生产准备
- 配置PostgreSQL实现数据持久化
- 启用Redis提升缓存性能
- 设置适当的工作进程数量

## 📞 获取帮助

### 检查服务状态
```bash
./dev-start.sh status
```

### 常用诊断命令
```bash
# 检查Python环境
python --version
pip list

# 检查服务状态
curl http://localhost:8000/health

# 检查端口占用
netstat -an | grep 8000
```

### 开发建议
1. 优先使用脚本启动，避免手动配置错误
2. 开发时建议使用API模式，提交前用Docker测试
3. 定期运行测试脚本验证功能完整性
4. 观察日志输出了解系统运行状态

---

**🎯 开发愉快！如有问题请查看日志或联系项目维护者。**