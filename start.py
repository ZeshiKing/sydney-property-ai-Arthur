#!/usr/bin/env python3
"""
澳洲房产智能推荐系统 - 启动脚本
快速启动和环境检查
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 9):
        print("❌ 需要Python 3.9或更高版本")
        print(f"   当前版本: {sys.version}")
        sys.exit(1)
    else:
        print(f"✅ Python版本: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

def check_env_file():
    """检查环境配置文件"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("⚠️  未找到 .env 文件")
            response = input("是否复制 .env.example 到 .env? (y/N): ")
            if response.lower() in ['y', 'yes']:
                env_file.write_text(env_example.read_text())
                print("✅ 已创建 .env 文件")
            else:
                print("❌ 请先配置 .env 文件")
                return False
        else:
            print("❌ 未找到 .env.example 文件")
            return False
    
    # 检查关键配置
    env_content = env_file.read_text()
    
    missing_keys = []
    if "OPENAI_API_KEY=your_openai_api_key_here" in env_content or "OPENAI_API_KEY=" not in env_content:
        missing_keys.append("OPENAI_API_KEY")
    
    if "FIRECRAWL_API_KEY=your_firecrawl_api_key_here" in env_content or "FIRECRAWL_API_KEY=" not in env_content:
        missing_keys.append("FIRECRAWL_API_KEY")
    
    if missing_keys:
        print("⚠️  需要配置以下API密钥:")
        for key in missing_keys:
            print(f"   - {key}")
        print("\n📝 请编辑 .env 文件添加真实的API密钥")
        print("   OpenAI: https://platform.openai.com/api-keys")
        print("   Firecrawl: https://firecrawl.dev")
        
        response = input("\n继续启动 (将使用回退模式)? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            return False
    else:
        print("✅ 环境配置检查通过")
    
    return True

def check_dependencies():
    """检查依赖包"""
    try:
        import fastapi
        import openai
        import httpx
        import pandas
        print("✅ 依赖包检查通过")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖包: {e.name}")
        print("请运行: pip install -r requirements.txt")
        return False

def start_backend():
    """启动后端服务"""
    print("\n🚀 启动后端服务...")
    print("访问 http://localhost:3000/health 检查服务状态")
    print("API文档: http://localhost:3000/api/v1/docs")
    print("按 Ctrl+C 停止服务\n")
    
    try:
        # 启动uvicorn服务
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
        print(f"❌ 启动失败: {e}")

def open_frontend():
    """打开前端界面"""
    frontend_path = Path("frontend/index.html")
    if frontend_path.exists():
        frontend_url = f"file://{frontend_path.absolute()}"
        print(f"🌐 打开前端界面: {frontend_url}")
        webbrowser.open(frontend_url)
    else:
        print("⚠️  前端文件不存在: frontend/index.html")

def main():
    """主函数"""
    print("🏠 澳洲房产智能推荐系统 - 启动助手")
    print("=" * 50)
    
    # 环境检查
    check_python_version()
    
    if not check_dependencies():
        sys.exit(1)
    
    if not check_env_file():
        sys.exit(1)
    
    # 询问是否打开前端
    response = input("\n是否同时打开前端界面? (Y/n): ")
    if response.lower() not in ['n', 'no']:
        open_frontend()
    
    # 启动后端
    start_backend()

if __name__ == "__main__":
    main()