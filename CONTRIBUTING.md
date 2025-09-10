# 贡献指南

感谢您对澳洲租房聚合网站项目的关注！本指南将帮助您了解如何为项目做出贡献。

## 🤝 如何贡献

### 贡献类型
- 🐛 **Bug报告和修复**
- ✨ **新功能开发**
- 📚 **文档改进**
- 🧪 **测试增强**
- 🎨 **代码优化**

### 开始之前
1. Fork项目到您的GitHub账户
2. 阅读[快速开始指南](GETTING_STARTED.md)
3. 设置本地开发环境
4. 了解项目架构和代码规范

## 📋 开发流程

### 1. 创建Issue
在开始开发之前，请先创建或认领一个Issue：
- 描述问题或功能需求
- 讨论实现方案
- 获得维护者的确认

### 2. 分支管理
```bash
# 从main分支创建功能分支
git checkout -b feature/issue-123-add-new-feature

# 分支命名规范：
# feature/issue-number-description    # 新功能
# bugfix/issue-number-description     # Bug修复
# docs/issue-number-description       # 文档更新
# test/issue-number-description       # 测试相关
```

### 3. 代码开发
- 遵循现有代码风格
- 添加必要的测试
- 更新相关文档
- 确保所有检查通过

### 4. 提交规范
使用约定式提交格式：
```
type(scope): description

feat(api): 添加房产搜索过滤器
fix(scraper): 修复Domain.com.au数据解析问题
docs(readme): 更新安装说明
test(search): 添加搜索功能单元测试
```

**提交类型:**
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式化
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建或工具变动

### 5. Pull Request
- 确保分支是最新的
- 填写完整的PR描述
- 关联相关Issue
- 请求代码审查

## 🔍 代码质量标准

### 代码规范
```bash
# 运行代码检查
npm run lint

# 自动修复格式问题
npm run lint:fix

# TypeScript类型检查
npm run build
```

### 测试要求
- 新功能必须包含测试
- Bug修复需要回归测试
- 保持测试覆盖率>80%

```bash
# 运行所有测试
npm test

# 运行特定测试
npm test -- search.test.ts

# 生成覆盖率报告
npm run test:coverage
```

### 文档要求
- 所有公共函数需要JSDoc注释
- 复杂逻辑需要内联注释
- API变更需要更新README

## 🏗️ 项目架构指南

### 目录结构
```
src/
├── controllers/    # HTTP请求处理
├── services/      # 业务逻辑层
├── models/        # 数据模型
├── middleware/    # Express中间件
├── routes/        # API路由定义
├── queues/        # 异步任务处理
├── utils/         # 工具函数
└── types/         # TypeScript类型定义
```

### 设计原则
- **单一职责**: 每个模块有明确的职责
- **依赖注入**: 便于测试和维护
- **错误处理**: 统一的错误处理机制
- **日志记录**: 详细的操作日志
- **类型安全**: 充分利用TypeScript

### 新增服务模板
```typescript
// src/services/newService.ts
import { logger } from '@/utils/logger';

export class NewService {
  constructor(
    private dependency: SomeDependency
  ) {}

  public async doSomething(param: string): Promise<Result> {
    try {
      logger.info('操作开始', { param });
      
      // 业务逻辑
      const result = await this.dependency.process(param);
      
      logger.info('操作完成', { result });
      return result;
    } catch (error) {
      logger.error('操作失败', { param, error });
      throw error;
    }
  }
}
```

## 🧪 测试指南

### 测试类型
1. **单元测试**: 测试单个函数或类
2. **集成测试**: 测试组件间交互
3. **E2E测试**: 测试完整用户流程

### 测试示例
```typescript
// tests/unit/urlBuilder.test.ts
describe('DomainUrlBuilder', () => {
  let urlBuilder: DomainUrlBuilder;

  beforeEach(() => {
    urlBuilder = new DomainUrlBuilder();
  });

  it('should build correct URL for basic search', () => {
    const params = {
      listingType: 'rent',
      location: { suburb: 'Camperdown', state: 'NSW', postcode: '2050' }
    };
    
    const url = urlBuilder.buildSearchUrl(params);
    expect(url).toBe('https://www.domain.com.au/rent/camperdown-nsw-2050/');
  });
});
```

## 📊 性能指导

### 性能要求
- API响应时间 < 500ms
- 数据库查询优化
- 合理使用缓存
- 异步处理耗时操作

### 性能测试
```bash
# 性能基准测试
npm run benchmark

# 监控API响应时间
curl -w "%{time_total}" http://localhost:3000/api/properties/search
```

## 🚀 发布流程

### 版本管理
- 使用语义化版本 (SemVer)
- 主版本：破坏性变更
- 次版本：新功能
- 补丁版本：Bug修复

### 发布清单
- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] 变更日志已更新
- [ ] 版本号已更新
- [ ] 部署测试通过

## 🎯 优先级任务

### 高优先级
- [ ] 前端React组件开发
- [ ] AI报告生成系统
- [ ] 用户认证和授权
- [ ] Real Estate.com.au集成

### 中优先级
- [ ] 高级搜索过滤器
- [ ] 数据导出功能
- [ ] 移动端API优化
- [ ] 监控和告警系统

### 低优先级
- [ ] 多语言支持
- [ ] 社交分享功能
- [ ] 数据可视化图表
- [ ] 第三方集成API

## 🐛 Bug报告模板

```markdown
**Bug描述**
简要描述遇到的问题

**复现步骤**
1. 进入 '...'
2. 点击 '....'
3. 滚动到 '....'
4. 看到错误

**期望行为**
描述您期望发生的情况

**实际行为**
描述实际发生的情况

**环境信息**
- OS: [例如 macOS, Windows, Linux]
- Node.js版本: [例如 18.17.0]
- Docker版本: [例如 24.0.6]

**附加信息**
添加任何其他有助于解决问题的信息
```

## 📞 获取帮助

### 联系方式
- **GitHub Issues**: 技术问题和Bug报告
- **GitHub Discussions**: 功能讨论和问答
- **Email**: urgent-issues@rental-aggregator.com

### 响应时间
- Bug报告: 24小时内回复
- 功能请求: 48小时内回复
- Pull Request: 72小时内审查

---

再次感谢您的贡献！让我们一起打造最优秀的澳洲房产聚合平台！ 🏡✨