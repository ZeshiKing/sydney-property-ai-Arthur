#!/usr/bin/env python3
"""
后端服务启动脚本
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

def check_port_in_use(port=3000):
    """检查端口是否被占用"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=2)
        return True, f"端口{port}已有服务运行"
    except:
        return False, f"端口{port}可用"

def install_dependencies():
    """安装必要依赖"""
    print("📦 检查并安装依赖...")
    
    required_packages = ['aiosqlite', 'fastapi', 'uvicorn', 'openai', 'httpx']
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            print(f"   安装 {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         capture_output=True, text=True)
    
    print("✅ 依赖检查完成")

def create_simple_env():
    """创建简单的环境配置"""
    env_file = PROJECT_ROOT / ".env"
    
    if not env_file.exists():
        print("📝 创建基本配置文件...")
        env_content = """# 基本配置
PORT=3000
ENVIRONMENT=development
SECRET_KEY=dev-secret-key

# 数据库配置 (SQLite)
DATABASE_URL=sqlite+aiosqlite:///./properties.db

# API配置 (测试模式)
OPENAI_API_KEY=sk-test
OPENAI_MODEL=gpt-4o-mini
FIRECRAWL_API_KEY=fc-test

# CORS配置
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080,file://
"""
        env_file.write_text(env_content)
        print("✅ 配置文件已创建")

def start_server():
    """启动服务器"""
    print("🚀 启动后端服务...")

    # 切换到项目目录
    os.chdir(PROJECT_ROOT)
    
    # 检查端口
    port_used, msg = check_port_in_use()
    if port_used:
        print(f"⚠️  {msg}")
        print("如需重启服务，请先停止现有服务")
        return
    
    # 安装依赖
    install_dependencies()
    
    # 创建配置
    create_simple_env()
    
    print("\n" + "="*50)
    print("🌐 服务地址:")
    print("   后端API: http://localhost:3000")
    print("   健康检查: http://localhost:3000/health")
    print("   API文档: http://localhost:3000/api/v1/docs")
    print("   前端界面: frontend/index.html")
    print("   测试界面: frontend/test.html")
    print("="*50)
    print("\n按 Ctrl+C 停止服务\n")
    
    try:
        # 启动uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "3000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        print("\n🔧 故障排除:")
        print("1. 检查Python环境: python --version")
        print("2. 检查项目目录是否正确")
        print("3. 手动安装依赖: pip install -r requirements.txt")

if __name__ == "__main__":
    start_server()
