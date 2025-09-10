# 快速开始指南

欢迎加入澳洲租房聚合网站后端开发团队！本指南将帮助您快速搭建开发环境并开始贡献代码。

## 🚀 5分钟快速启动

### 前置要求
- Node.js 18+
- Docker & Docker Compose
- Git
- 一个Firecrawl API账户（免费注册：https://firecrawl.dev）

> 📖 **重要提醒**：我们的团队使用不同操作系统（macOS、Windows、Linux）进行开发。
> 
> 🔧 **跨平台协作必读**：请先阅读 [DEVELOPMENT.md](DEVELOPMENT.md) 了解系统特定的配置和注意事项，特别是：
> - **macOS用户**：避免提交 `.DS_Store` 等系统文件
> - **Windows用户**：正确配置Git行结束符
> - **所有用户**：Docker和环境变量的最佳实践

### 1. 克隆并配置项目
```bash
# 克隆项目
git clone <repository-url>
cd rental-aggregator-backend

# 复制环境配置
cp .env.example .env

# 编辑.env文件，添加您的Firecrawl API密钥
# FIRECRAWL_API_KEY=fc-your-api-key-here
```

### 2. 启动开发环境
```bash
# 启动数据库和缓存服务
docker-compose up -d postgres redis

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 3. 验证安装
```bash
# 测试API连接
curl http://localhost:3000/health

# 测试房产搜索
node test-firecrawl.js
```

## 📁 项目结构

```
rental-aggregator-backend/
├── src/
│   ├── controllers/     # API控制器
│   ├── services/       # 业务逻辑
│   ├── middleware/     # 中间件
│   ├── routes/         # API路由
│   ├── queues/         # 异步队列
│   ├── types/          # TypeScript类型
│   └── utils/          # 工具函数
├── tests/              # 测试文件
├── docs/               # 项目文档
└── scripts/            # 数据库脚本
```

## 🔧 开发工作流

### 代码规范
```bash
# 代码检查
npm run lint

# 自动修复
npm run lint:fix

# 运行测试
npm test
```

### Git工作流
```bash
# 创建功能分支
git checkout -b feature/your-feature-name

# 提交代码
git add .
git commit -m "feat: 添加新功能"

# 推送分支
git push origin feature/your-feature-name
```

## 🎯 当前功能状态

### ✅ 已完成
- [x] Express.js API服务器
- [x] Firecrawl集成 (实时抓取)
- [x] Domain.com.au URL构建器
- [x] PostgreSQL + Redis 数据层
- [x] Bull队列异步处理
- [x] 完整的错误处理和日志
- [x] Docker容器化
- [x] 基础API端点

### 🚧 开发中
- [ ] 前端用户界面
- [ ] AI报告生成
- [ ] 更多房产网站支持
- [ ] 用户认证系统
- [ ] 高级搜索过滤器

### 📝 优先级任务
1. **前端集成** - 创建用户友好的搜索界面
2. **AI报告** - 基于房产数据生成市场分析
3. **性能优化** - 缓存策略和查询优化
4. **监控仪表板** - 系统健康和使用统计

## 🔑 核心API端点

```bash
# 搜索房产
POST /api/properties/search
{
  "listingType": "rent",
  "location": {
    "suburb": "Camperdown",
    "state": "NSW", 
    "postcode": "2050"
  },
  "bedrooms": {"min": 2}
}

# 获取单个房产
GET /api/properties/:id

# 地区建议
GET /api/locations/suggest?query=camper

# 健康检查
GET /health
```

## 💡 开发建议

### 新功能开发
1. 查看现有的服务模式 (`src/services/`)
2. 遵循相同的错误处理模式
3. 添加相应的测试文件
4. 更新API文档

### 性能考虑
- 使用Redis缓存频繁查询
- 考虑队列系统处理耗时操作
- 监控Firecrawl API使用量

### 测试策略
- 单元测试：业务逻辑
- 集成测试：API端点  
- E2E测试：完整用户流程

## 🆘 常见问题

### Q: Firecrawl API配额用完了？
A: 检查当前用量，考虑升级计划或优化缓存策略

### Q: Docker服务启动失败？
A: 检查端口占用，确保Docker Desktop正在运行

### Q: 数据库连接错误？
A: 验证.env配置，确保PostgreSQL容器正常运行

### Q: 房产数据解析失败？
A: Domain.com.au可能更新了页面结构，需要更新解析逻辑

## 📞 联系方式

- **技术问题**: 创建GitHub Issue
- **功能建议**: 发起Discussion
- **紧急问题**: 联系项目维护者

## 🎉 贡献指南

我们欢迎所有形式的贡献：
- 🐛 Bug修复
- ✨ 新功能
- 📚 文档改进  
- 🧪 测试覆盖
- 🎨 UI/UX改进

让我们一起打造最好的澳洲房产聚合平台！