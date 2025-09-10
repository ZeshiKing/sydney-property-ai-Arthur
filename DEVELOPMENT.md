# 开发环境最佳实践指南

## 🔧 跨平台开发团队协作指南

本项目支持macOS、Windows、Linux多平台开发，为保证团队协作顺利，请遵循以下最佳实践。

## 🍎 macOS 开发者须知

### 系统文件管理
macOS会自动创建多种系统和缓存文件，这些文件不应提交到Git仓库中：

**自动创建的系统文件：**
- `.DS_Store` - Finder目录设置
- `._*` - 资源分叉文件
- `.Spotlight-V100` - Spotlight搜索索引
- `.Trashes` - 回收站元数据
- `.fseventsd` - 文件系统事件守护程序
- `.TemporaryItems` - 临时文件

### 推荐Git配置
```bash
# 设置全局用户信息
git config --global user.name "你的姓名"
git config --global user.email "your.email@example.com"

# 创建全局gitignore
echo ".DS_Store
._*
.Spotlight-V100
.Trashes
.fseventsd
.TemporaryItems" > ~/.gitignore_global

# 启用全局gitignore
git config --global core.excludesfile ~/.gitignore_global

# 设置默认编辑器
git config --global core.editor "code --wait"  # VS Code
# 或
git config --global core.editor "nano"         # nano
```

### Docker配置注意事项
```bash
# 检查Docker Desktop状态
docker --version
docker-compose --version

# 确保有足够的资源分配
# Docker Desktop -> Preferences -> Resources
# 推荐设置：CPU: 4核，Memory: 4GB，Disk: 20GB
```

### macOS特有问题解决

**问题1: 权限问题**
```bash
# 如果遇到权限问题，使用sudo谨慎操作
sudo chown -R $(whoami) /usr/local/lib/node_modules
```

**问题2: Node.js版本管理**
```bash
# 推荐使用nvm管理Node.js版本
brew install nvm
nvm install 18
nvm use 18
```

**问题3: 端口被占用**
```bash
# 查找占用端口的进程
lsof -ti:3000
kill -9 PID
```

## 💻 Windows 开发者须知

### Git行结束符配置
Windows和Unix系统使用不同的行结束符，需要正确配置：

```bash
# 设置自动转换行结束符
git config --global core.autocrlf true

# 设置默认编辑器
git config --global core.editor "code --wait"
```

### Docker Desktop配置
```bash
# 确保启用WSL2集成
# Docker Desktop -> Settings -> General -> Use WSL 2 based engine

# 在WSL2中开发时的配置
wsl --set-default-version 2
```

### 路径处理注意事项
```bash
# 使用正斜杠或双反斜杠
cd C:/Users/username/project  # 正确
cd C:\\Users\\username\\project  # 正确
cd C:\Users\username\project   # 可能出错
```

## 🐧 Linux 开发者须知

### 权限管理
```bash
# 避免使用sudo运行npm
npm config set prefix ~/.npm-global
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### Docker权限配置
```bash
# 将用户添加到docker组（避免每次使用sudo）
sudo usermod -aG docker $USER
# 重新登录或运行
newgrp docker
```

## 🛠 通用开发环境设置

### Node.js和npm配置
```bash
# 检查版本
node --version  # 应该是18+
npm --version

# 设置npm镜像（中国开发者推荐）
npm config set registry https://registry.npmmirror.com/

# 全局安装常用工具
npm install -g nodemon typescript ts-node
```

### VS Code推荐插件
```json
{
  "recommendations": [
    "ms-vscode.vscode-typescript-next",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-eslint",
    "ms-python.python",
    "ms-vscode-remote.remote-containers",
    "bradlc.vscode-tailwindcss",
    "formulahendry.auto-rename-tag"
  ]
}
```

### 环境变量管理
```bash
# 永远不要提交真实的API密钥
# 使用 .env.example 作为模板

# 检查环境变量是否正确加载
npm run check-env  # 如果有这个脚本
```

## ⚡ 性能优化建议

### Docker优化
```yaml
# docker-compose.yml 优化建议
version: '3.8'
services:
  app:
    # 使用多阶段构建减少镜像大小
    build:
      context: .
      dockerfile: Dockerfile
    # 限制资源使用
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

### 缓存策略
```bash
# npm缓存清理
npm cache clean --force

# Docker镜像清理
docker system prune -af
```

## 🚨 常见问题排查

### 1. 端口冲突
```bash
# macOS/Linux
lsof -ti:3000
kill -9 <PID>

# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### 2. 依赖安装问题
```bash
# 清除node_modules和package-lock.json
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### 3. Docker问题
```bash
# 重启Docker服务
# macOS: 重启Docker Desktop
# Linux: sudo systemctl restart docker
# Windows: 重启Docker Desktop

# 清理Docker资源
docker system prune -af --volumes
```

### 4. 权限问题
```bash
# macOS/Linux: 检查文件权限
ls -la
chmod 755 filename

# Windows: 以管理员身份运行终端
```

## 📝 提交代码前检查清单

- [ ] 运行测试: `npm test`
- [ ] 检查代码格式: `npm run lint`
- [ ] 构建项目: `npm run build`
- [ ] 检查没有敏感信息被提交
- [ ] 确认没有系统文件被添加 (`.DS_Store`, `Thumbs.db`等)
- [ ] 提交信息清晰描述变更内容

## 🤝 团队协作建议

### 分支管理
```bash
# 功能开发
git checkout -b feature/your-feature-name

# Bug修复
git checkout -b bugfix/issue-description

# 合并前更新
git checkout main
git pull origin main
git checkout your-branch
git rebase main
```

### 代码审查
- 小而频繁的提交
- 清晰的提交信息
- 详细的PR描述
- 及时响应审查意见

### 环境一致性
- 使用相同的Node.js版本
- 使用Docker保证环境一致性
- 定期同步依赖版本
- 共享开发配置文件

---

**需要帮助？** 遇到问题时请先检查此文档，如仍无法解决请在团队群中询问或提交Issue。