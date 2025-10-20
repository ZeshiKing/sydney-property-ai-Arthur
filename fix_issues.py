#!/usr/bin/env python3
"""
问题修复和诊断脚本
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

def fix_env_file():
    """修复环境配置文件"""
    env_file = PROJECT_ROOT / ".env"
    
    print("🔧 修复环境配置文件...")
    
    if env_file.exists():
        content = env_file.read_text()
        
        # 修复OpenAI模型名称
        if "gpt-5-nano" in content:
            content = content.replace("gpt-5-nano", "gpt-4o-mini")
            print("   ✅ 修复OpenAI模型名称: gpt-5-nano -> gpt-4o-mini")
        
        # 添加SQLite数据库配置
        if "DATABASE_URL=" not in content or "DATABASE_URL=sqlite" not in content:
            if "DATABASE_URL=" not in content:
                content += "\n# 数据库配置\nDATABASE_URL=sqlite+aiosqlite:///./properties.db\n"
            else:
                content = content.replace(
                    "DATABASE_URL=sqlite:///./properties.db",
                    "DATABASE_URL=sqlite+aiosqlite:///./properties.db"
                )
            print("   ✅ 配置SQLite数据库")
        
        env_file.write_text(content)
    else:
        print("   ❌ .env 文件不存在")
        return False
    
    return True

def check_dependencies():
    """检查并安装依赖"""
    print("📦 检查依赖包...")
    
    required_packages = {
        'fastapi': 'FastAPI web framework',
        'openai': 'OpenAI API client',
        'aiosqlite': 'Async SQLite support',
        'httpx': 'HTTP client',
        'sqlalchemy': 'Database ORM'
    }
    
    missing = []
    for package, description in required_packages.items():
        try:
            __import__(package)
            print(f"   ✅ {package}: {description}")
        except ImportError:
            print(f"   ❌ {package}: {description} (缺失)")
            missing.append(package)
    
    if missing:
        print(f"\n📥 安装缺失的包: {', '.join(missing)}")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install"] + missing, check=True)
            print("   ✅ 依赖安装完成")
            return True
        except subprocess.CalledProcessError:
            print("   ❌ 依赖安装失败")
            return False
    
    return True

def test_openai_key():
    """测试OpenAI API密钥"""
    print("🤖 测试OpenAI API密钥...")
    
    try:
        from openai import OpenAI
        
        # 从环境变量或.env文件获取API密钥
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # 尝试从.env文件读取
            env_file = PROJECT_ROOT / ".env"
            if env_file.exists():
                for line in env_file.read_text().split('\n'):
                    if line.startswith('OPENAI_API_KEY='):
                        api_key = line.split('=', 1)[1]
                        break
        
        if not api_key or api_key == "your_openai_api_key_here":
            print("   ⚠️ OpenAI API密钥未配置")
            return False
        
        # 测试API连接
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        print("   ✅ OpenAI API连接正常")
        return True
        
    except Exception as e:
        print(f"   ❌ OpenAI API测试失败: {e}")
        return False

def create_minimal_env():
    """创建最小化的工作环境配置"""
    print("⚡ 创建快速测试配置...")
    
    minimal_env = """# 快速测试配置
PORT=3000
ENVIRONMENT=development
SECRET_KEY=test-secret-key

# 数据库配置 (SQLite - 无需额外安装)
DATABASE_URL=sqlite+aiosqlite:///./properties.db

# API配置 (如果没有真实密钥，使用测试模式)
OPENAI_API_KEY=sk-test-key
OPENAI_MODEL=gpt-4o-mini
FIRECRAWL_API_KEY=fc-test-key

# CORS配置
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080,file://
"""
    
    env_file = PROJECT_ROOT / ".env"
    backup_file = PROJECT_ROOT / ".env.backup"
    
    # 备份现有文件
    if env_file.exists():
        env_file.rename(backup_file)
        print(f"   📋 已备份现有配置到: {backup_file}")
    
    # 创建测试配置
    env_file.write_text(minimal_env)
    print("   ✅ 创建测试配置文件")
    print("   ⚠️ 注意: 这是测试配置，API功能可能受限")
    
    return True

def start_backend_test():
    """启动后端服务进行测试"""
    print("🚀 启动后端服务...")
    
    try:
        # 设置环境变量
        os.chdir(PROJECT_ROOT)
        
        # 启动服务 (不使用reload模式，避免文件监控问题)
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "3000"
        ]
        
        print("   📡 启动命令:", " ".join(cmd))
        print("   🌐 服务地址: http://localhost:3000")
        print("   📚 API文档: http://localhost:3000/api/v1/docs")
        print("   💻 前端界面: frontend/index.html")
        print()
        print("按 Ctrl+C 停止服务")
        print("-" * 50)
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        print("\n🔧 可能的解决方案:")
        print("1. 检查端口3000是否被占用: lsof -i :3000")
        print("2. 尝试不同端口: uvicorn app.main:app --port 3001")
        print("3. 检查Python环境和依赖")

def main():
    """主函数"""
    print("🔧 澳洲房产智能推荐系统 - 问题修复工具")
    print("=" * 60)
    
    # 切换到项目目录
    try:
        os.chdir(PROJECT_ROOT)
        print(f"📁 工作目录: {os.getcwd()}")
    except:
        print("❌ 无法切换到项目目录")
        return
    
    print("\n🔍 诊断问题...")
    
    # 1. 修复配置文件
    if not fix_env_file():
        print("❌ 配置文件修复失败")
        return
    
    # 2. 检查依赖
    if not check_dependencies():
        print("❌ 依赖检查失败")
        return
    
    # 3. 测试API密钥
    api_ok = test_openai_key()
    if not api_ok:
        print("\n⚡ 将创建测试配置继续运行...")
        create_minimal_env()
    
    print("\n" + "=" * 60)
    print("✅ 问题修复完成！现在启动服务...")
    print("=" * 60)
    
    # 4. 启动服务
    start_backend_test()

if __name__ == "__main__":
    main()
