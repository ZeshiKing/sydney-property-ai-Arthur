# Sydney Property AI - 重构版本

🏡 **全澳洲最好用的AI找房软件** - 企业级重构版本

## 🚀 重构亮点

### 架构升级
- ✅ **模块化设计**: 分离前端UI和后端业务逻辑
- ✅ **标准化目录结构**: 符合企业级Python项目规范
- ✅ **统一配置管理**: 集中管理所有配置项
- ✅ **完善日志系统**: 分类日志记录和监控
- ✅ **Docker容器化**: 一键部署和扩展
- ✅ **单元测试框架**: 保证代码质量和可靠性

### 技术栈
- **前端**: Streamlit (模块化组件)
- **后端**: Python 服务层架构
- **AI引擎**: Claude-3.5-Sonnet
- **数据处理**: Pandas + 自定义数据模型
- **容器化**: Docker + Docker Compose
- **测试**: Pytest
- **文档**: 完整API文档

## 📁 项目结构

```
sydney-property-ai/
├── frontend/              # 前端UI组件
│   ├── components/        # 可复用UI组件
│   ├── pages/            # 页面组件
│   └── styles/           # 样式配置
├── backend/              # 后端业务逻辑
│   ├── services/         # 业务服务层
│   ├── models/           # 数据模型
│   └── utils/            # 工具函数
├── ai/                   # AI处理模块
│   ├── processors/       # AI处理器
│   ├── models/           # AI模型
│   └── analyzers/        # 分析器
├── config/               # 配置管理
├── data/                 # 数据文件
├── tests/                # 测试文件
├── docs/                 # 文档
├── logs/                 # 日志文件
└── deployment/           # 部署配置
```

## 🛠 快速开始

### 方式1: Docker部署（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd sydney-property-ai-Arthur

# 2. 设置环境变量
export ANTHROPIC_API_KEY=your_api_key_here

# 3. 启动服务
docker-compose up -d

# 4. 访问应用
# 主应用: http://localhost:8501
# Traefik监控: http://localhost:8080
```

### 方式2: 本地开发

```bash
# 1. 安装依赖
pip install -r requirements_new.txt

# 2. 设置环境变量
export ANTHROPIC_API_KEY=your_api_key_here

# 3. 运行重构版本
streamlit run app_refactored.py

# 4. 或运行原版本
streamlit run app.py
```

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_intent_processor.py

# 生成覆盖率报告
pytest --cov=backend --cov=ai
```

## 📊 核心功能

### 1. 智能意图识别
```python
from ai.processors.intent_processor import intent_processor

intent = intent_processor.extract_intent("我要在Bondi找个2室的房子，预算100万")
# 返回: UserIntent(suburb="Bondi", bedrooms=2, budget=100.0, ...)
```

### 2. 灵活房源筛选
```python
from backend.services.data_service import data_service

properties = data_service.filter_properties_flexible(intent)
# 多层次筛选策略，确保返回有意义的结果
```

### 3. AI推荐生成
```python
from backend.services.recommendation_service import recommendation_service

recommendations = recommendation_service.generate_recommendations(
    user_input="我要大一点的房子",
    intent=intent
)
# 返回: ["推荐1: 123 Bondi St - $800,000 - 理由...", ...]
```

## 🔧 配置

### 环境变量
- `ANTHROPIC_API_KEY`: Claude AI API密钥（必需）
- `LOG_LEVEL`: 日志级别（INFO, DEBUG, WARNING, ERROR）

### 配置文件
所有配置集中在 `config/settings.py`:
```python
from config.settings import settings

print(settings.CLAUDE_MODEL)  # claude-3-5-sonnet-20241022
print(settings.DEFAULT_RESULT_LIMIT)  # 10
```

## 📈 性能优化

### 数据缓存
- 自动缓存房产数据，避免重复加载
- 智能筛选策略，优先精确匹配

### 容器优化
- 多阶段Docker构建，减少镜像体积
- 非root用户运行，提高安全性
- 健康检查和自动重启

## 🔍 监控和日志

### 日志分类
- `logs/app.log`: 应用程序日志
- `logs/api.log`: API调用日志
- `logs/data.log`: 数据处理日志

### 健康检查
```bash
# 检查应用状态
curl http://localhost:8501/_stcore/health

# 查看Docker容器状态
docker-compose ps
```

## 🚀 部署选项

### 开发环境
```bash
streamlit run app_refactored.py
```

### 生产环境
```bash
# 使用Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 或直接Docker
docker build -t sydney-property-ai .
docker run -p 8501:8501 -e ANTHROPIC_API_KEY=your_key sydney-property-ai
```

### 扩展部署
- 支持负载均衡（Traefik）
- 支持多实例部署
- 支持外部数据库集成

## 📖 文档

- [API文档](docs/API.md) - 详细的API接口说明
- [架构文档](docs/ARCHITECTURE.md) - 系统架构设计
- [部署指南](docs/DEPLOYMENT.md) - 生产环境部署

## 🔄 版本对比

| 功能 | 原版本 | 重构版本 |
|------|--------|----------|
| 架构 | 单文件 | 模块化 |
| 配置 | 硬编码 | 统一管理 |
| 日志 | 无 | 分类记录 |
| 测试 | 无 | 完整测试 |
| 部署 | 手动 | Docker化 |
| 文档 | 基础 | 完整文档 |

## 🤝 贡献

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 许可证

本项目仅用于技术学习和交流目的。

## ⚠️ 免责声明

请勿将该代码用于未经授权的商业用途，也请尊重目标网站的 robots.txt 协议与使用条款。

**Made by Arthur and Ryan in whitemirror** | Powered by Claude AI