# 多阶段构建的Dockerfile，用于悉尼房产AI推荐系统

# 第一阶段：构建环境
FROM python:3.9-slim as builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --user -r requirements.txt

# 第二阶段：运行环境
FROM python:3.9-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app

# 设置工作目录
WORKDIR /app

# 从构建阶段复制Python包
COPY --from=builder /root/.local /home/app/.local

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs data

# 设置权限
RUN chown -R app:app /app

# 切换到非root用户
USER app

# 确保.local/bin在PATH中
ENV PATH=/home/app/.local/bin:$PATH

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 暴露端口
EXPOSE 8501

# 启动命令
CMD ["streamlit", "run", "app_refactored.py", "--server.port=8501", "--server.address=0.0.0.0"]