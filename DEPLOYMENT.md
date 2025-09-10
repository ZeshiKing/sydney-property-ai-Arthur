# 部署指南

本文档提供了澳洲租房聚合网站后端系统的完整部署指南。

## 🚀 快速部署

### 最小环境要求

#### 系统要求
- **操作系统**: Linux (Ubuntu 20.04+), macOS, Windows 10/11 + WSL2
- **内存**: 最小 2GB RAM，推荐 4GB+
- **存储**: 最小 10GB 可用空间
- **网络**: 稳定的互联网连接

#### 软件依赖
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Node.js**: 18+ (如果不使用Docker)
- **Git**: 版本控制

### 1. 获取代码

```bash
# 克隆项目
git clone <repository-url>
cd rental-aggregator-backend

# 检查项目结构
ls -la
```

### 2. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境配置（重要！）
nano .env
```

必填配置：
```env
# Firecrawl API (必须配置)
FIRECRAWL_API_KEY=fc-your-api-key-here

# 生产环境设置
NODE_ENV=production

# 数据库密码 (修改默认值)
DB_PASSWORD=your-secure-password-here

# Redis密码 (修改默认值)  
REDIS_PASSWORD=your-redis-password-here

# JWT密钥 (必须修改)
JWT_SECRET=your-very-secure-jwt-secret-here
```

### 3. 一键启动

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

### 4. 验证部署

```bash
# 检查健康状态
curl http://localhost:3000/health

# 测试API端点
curl http://localhost:3000/api

# 预期响应：
# {
#   "message": "Rental Aggregator API",
#   "version": "1.0.0",
#   "status": "operational",
#   ...
# }
```

## 🔧 详细部署配置

### 数据库初始化

#### 自动初始化
系统启动时会自动运行数据库初始化脚本：

```bash
# 查看数据库初始化日志
docker-compose logs postgres

# 连接数据库验证表结构
docker-compose exec postgres psql -U postgres -d rental_aggregator -c "\dt"
```

#### 手动初始化（如果需要）
```bash
# 进入PostgreSQL容器
docker-compose exec postgres psql -U postgres -d rental_aggregator

# 运行初始化脚本
\i /docker-entrypoint-initdb.d/init-db.sql

# 退出
\q
```

### Redis配置验证

```bash
# 测试Redis连接
docker-compose exec redis redis-cli -a your-redis-password ping

# 查看Redis信息
docker-compose exec redis redis-cli -a your-redis-password info memory
```

### 应用程序配置

#### 性能调优
```env
# 队列并发数 (根据服务器性能调整)
QUEUE_CONCURRENCY=5

# 最大并发爬虫数
MAX_CONCURRENT_REQUESTS=3

# 缓存TTL (秒)
CACHE_TTL_SECONDS=900

# 请求频率限制 (毫秒)
SCRAPING_DELAY_MS=1000
```

#### 日志配置
```env
# 日志级别
LOG_LEVEL=info

# 日志文件路径
LOG_FILE_PATH=logs/app.log
```

## 🏭 生产环境部署

### 生产环境Docker Compose

创建 `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  app:
    build:
      target: production
    environment:
      NODE_ENV: production
    restart: always
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  postgres:
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  redis:
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_prod_data:/data
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M

volumes:
  postgres_prod_data:
  redis_prod_data:
```

启动生产环境：

```bash
# 使用生产配置启动
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 验证生产部署
curl http://localhost:3000/health/detailed
```

### SSL/TLS配置 (推荐)

#### 使用Nginx反向代理

创建 `nginx.conf`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL配置
    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/key.pem;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # 代理到应用
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 使用Let's Encrypt (免费SSL)

```bash
# 安装Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com

# 设置自动续期
sudo crontab -e
# 添加：0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 监控和维护

### 健康检查配置

```bash
# 创建健康检查脚本
cat > health-check.sh << 'EOF'
#!/bin/bash

# 检查API健康状态
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health)

if [ $response = "200" ]; then
    echo "✅ API服务正常"
else
    echo "❌ API服务异常 (HTTP $response)"
    exit 1
fi

# 检查数据库
db_status=$(docker-compose exec -T postgres pg_isready -U postgres -d rental_aggregator)
if [[ $db_status == *"accepting connections"* ]]; then
    echo "✅ 数据库正常"
else
    echo "❌ 数据库异常"
    exit 1
fi

# 检查Redis
redis_status=$(docker-compose exec -T redis redis-cli -a ${REDIS_PASSWORD:-redis123} ping)
if [[ $redis_status == "PONG" ]]; then
    echo "✅ Redis正常"
else
    echo "❌ Redis异常"
    exit 1
fi

echo "🎉 系统运行正常"
EOF

chmod +x health-check.sh
```

### 日志监控

```bash
# 查看实时日志
docker-compose logs -f app

# 查看错误日志
docker-compose exec app tail -f logs/error.log

# 日志轮转配置 (如果需要)
cat > logrotate.conf << 'EOF'
/path/to/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
    postrotate
        docker-compose restart app
    endscript
}
EOF
```

### 数据备份

#### 数据库备份
```bash
#!/bin/bash
# backup-db.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/postgres_backup_$DATE.sql"

mkdir -p $BACKUP_DIR

# 创建备份
docker-compose exec -T postgres pg_dump -U postgres rental_aggregator > $BACKUP_FILE

# 压缩备份
gzip $BACKUP_FILE

# 清理7天前的备份
find $BACKUP_DIR -name "postgres_backup_*.sql.gz" -mtime +7 -delete

echo "数据库备份完成: $BACKUP_FILE.gz"
```

#### Redis备份
```bash
#!/bin/bash
# backup-redis.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 创建Redis备份
docker-compose exec -T redis redis-cli -a ${REDIS_PASSWORD:-redis123} SAVE
docker cp $(docker-compose ps -q redis):/data/dump.rdb $BACKUP_DIR/redis_backup_$DATE.rdb

# 压缩备份
gzip $BACKUP_DIR/redis_backup_$DATE.rdb

echo "Redis备份完成: $BACKUP_DIR/redis_backup_$DATE.rdb.gz"
```

### 自动化备份
```bash
# 添加到crontab
crontab -e

# 每天凌晨2点备份
0 2 * * * /path/to/backup-db.sh
30 2 * * * /path/to/backup-redis.sh
```

## 🚨 故障排除

### 常见问题及解决方案

#### 1. 服务启动失败

```bash
# 检查端口占用
sudo netstat -tlnp | grep :3000
sudo lsof -i :3000

# 如果端口被占用，修改配置或停止占用进程
sudo kill -9 <PID>

# 重启服务
docker-compose restart app
```

#### 2. 数据库连接错误

```bash
# 检查数据库状态
docker-compose exec postgres pg_isready

# 查看数据库日志
docker-compose logs postgres

# 重启数据库
docker-compose restart postgres
```

#### 3. Redis连接问题

```bash
# 测试Redis连接
docker-compose exec redis redis-cli ping

# 查看Redis配置
docker-compose exec redis redis-cli config get "*"

# 重启Redis
docker-compose restart redis
```

#### 4. Firecrawl API错误

```bash
# 测试API密钥
curl -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
     https://api.firecrawl.dev/v0/scrape \
     -d '{"url": "https://example.com"}'

# 检查配置
echo $FIRECRAWL_API_KEY
grep FIRECRAWL .env
```

### 性能优化

#### 1. 数据库优化

```sql
-- 连接到数据库
psql -U postgres -d rental_aggregator

-- 查看查询性能
EXPLAIN ANALYZE SELECT * FROM properties WHERE address_data->>'suburb' = 'Camperdown';

-- 重建索引
REINDEX DATABASE rental_aggregator;

-- 更新统计信息
ANALYZE;
```

#### 2. Redis优化

```bash
# 查看内存使用
docker-compose exec redis redis-cli info memory

# 清理过期键
docker-compose exec redis redis-cli --latency

# 配置内存策略
docker-compose exec redis redis-cli config set maxmemory-policy allkeys-lru
```

#### 3. 应用性能监控

```bash
# 查看容器资源使用
docker stats

# 查看应用内存使用
curl http://localhost:3000/health/detailed

# 监控队列状态
curl http://localhost:3000/api/admin/queue/status
```

## 🔄 更新和维护

### 应用更新流程

```bash
#!/bin/bash
# update-app.sh

echo "🔄 开始更新应用..."

# 1. 备份数据
./backup-db.sh
./backup-redis.sh

# 2. 拉取最新代码
git fetch origin
git pull origin main

# 3. 更新依赖
docker-compose pull

# 4. 重建应用
docker-compose build app

# 5. 重启服务（滚动更新）
docker-compose up -d app

# 6. 验证更新
sleep 10
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health)

if [ $response = "200" ]; then
    echo "✅ 应用更新成功"
else
    echo "❌ 应用更新失败，开始回滚..."
    git checkout HEAD~1
    docker-compose build app
    docker-compose up -d app
    exit 1
fi
```

### 定期维护任务

```bash
#!/bin/bash
# maintenance.sh

echo "🧹 开始定期维护..."

# 清理Docker镜像和容器
docker system prune -f

# 清理应用日志
find logs/ -name "*.log" -mtime +7 -delete

# 清理队列中的旧任务
curl -X POST http://localhost:3000/api/admin/queue/clean

# 数据库维护
docker-compose exec -T postgres psql -U postgres -d rental_aggregator -c "VACUUM ANALYZE;"

echo "✅ 维护完成"
```

### 监控脚本

```bash
#!/bin/bash
# monitor.sh

# 检查磁盘空间
df_output=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $df_output -gt 85 ]; then
    echo "⚠️ 磁盘空间不足: ${df_output}%"
fi

# 检查内存使用
memory_usage=$(free | awk '/Mem:/ {printf "%.0f", $3/$2*100}')
if [ $memory_usage -gt 85 ]; then
    echo "⚠️ 内存使用过高: ${memory_usage}%"
fi

# 检查服务状态
./health-check.sh

# 检查日志中的错误
error_count=$(docker-compose logs app --since="1h" | grep -i error | wc -l)
if [ $error_count -gt 10 ]; then
    echo "⚠️ 检测到异常错误数量: $error_count"
fi
```

## 📞 支持和联系

如果您在部署过程中遇到任何问题：

1. **查看日志**: `docker-compose logs app`
2. **检查健康状态**: `curl http://localhost:3000/health/detailed`
3. **查看GitHub Issues**: 搜索已知问题
4. **联系支持**: support@rental-aggregator.com

---

**重要提醒**: 
- 🔐 务必修改所有默认密码
- 🔑 保护好Firecrawl API密钥
- 🔄 定期备份重要数据
- 📊 监控系统性能和健康状态